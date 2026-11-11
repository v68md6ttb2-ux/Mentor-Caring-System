"""Data mapper for Appointment entity."""

import json
from datetime import datetime, timedelta

from app.extensions import db
from app.entity.appointment import Appointment
from app.entity.student import Student
from app.entity.enums import AppointmentStatus, MessageStatus


class AppointmentMapper:
    """Data mapper for Appointment entity."""

    @staticmethod
    def find_by_id(appointment_id):
        return Appointment.query.get(appointment_id)

    @staticmethod
    def find_by_mentor(mentor_id):
        return (
            Appointment.query
            .filter_by(mentor_id=mentor_id)
            .order_by(Appointment.sent_datetime.desc())
            .all()
        )

    @staticmethod
    def find_by_student(db_student_id):
        return (
            Appointment.query
            .filter_by(student_id=db_student_id)
            .order_by(Appointment.sent_datetime.desc())
            .all()
        )

    @staticmethod
    def create_from_mentor(mentor, student_id, slot_list):
        student = Student.query.filter_by(student_id=student_id).first()
        if not student:
            return None
        appointment = Appointment(
            content=f"Appointment with {student.name}",
            sender_id=mentor.id,
            mentor_id=mentor.id,
            student_id=student.id,
        )
        db.session.add(appointment)
        db.session.flush()
        receiver_data = [{
            "receiver_id": str(student.id),
            "status": "Unrespond",
            "read_at": None,
            "responded_at": None
        }]
        appointment.receiver_data_json = json.dumps(receiver_data)
        if slot_list:
            AppointmentMapper.set_available_slots(appointment, slot_list)
        return appointment

    @staticmethod
    def create(mentor, student, slot_text_list, content="Appointment request", sender_id=None):
        if not mentor:
            return False, "Only mentors can create appointments.", None

        if not student.group or student.group.mentor_id != mentor.id:
            return False, "This student is not in your MCP group.", None

        slot_list = []
        seen_slot_starts = set()

        for slot_text in slot_text_list:
            slot_text = slot_text.strip()
            if not slot_text:
                continue
            try:
                start_time = datetime.strptime(slot_text, "%Y-%m-%d %H:%M")
            except ValueError:
                return False, "Invalid time format. Please use YYYY-MM-DD HH:MM.", None

            normalized_start = start_time.strftime("%Y-%m-%d %H:%M")
            if normalized_start in seen_slot_starts:
                return False, "Duplicate available slots are not allowed.", None
            seen_slot_starts.add(normalized_start)

            end_time = start_time + timedelta(minutes=30)
            slot_list.append({
                "start_time": start_time,
                "end_time": end_time
            })

        if not slot_list:
            return False, "Please provide at least one available slot.", None

        appointment = Appointment(
            content=content,
            sender_id=sender_id,
            mentor_id=mentor.id,
            student_id=student.id,
            appointment_status=AppointmentStatus.Requested.value
        )
        db.session.add(appointment)
        db.session.flush()

        slot_data = AppointmentMapper._build_slot_data(slot_list)
        appointment.available_slot_list_json = json.dumps(slot_data)

        receiver_data = [{
            "receiver_id": str(student.id),
            "status": MessageStatus.Unrespond.value,
            "read_at": None,
            "responded_at": None
        }]
        appointment.receiver_data_json = json.dumps(receiver_data)

        db.session.commit()
        return True, "Appointment request created successfully.", appointment

    @staticmethod
    def set_available_slots(appointment, slot_list):
        serializable_slots = AppointmentMapper._build_slot_data(slot_list)
        appointment.available_slot_list_json = json.dumps(serializable_slots)
        appointment.appointment_status = AppointmentStatus.Requested.value
        db.session.commit()

    @staticmethod
    def choose_slot(appointment, student_id, chosen_slot):
        student = Student.query.get(student_id)
        if not student:
            return None

        slot_start = chosen_slot["start_time"] if isinstance(chosen_slot["start_time"], str) else chosen_slot["start_time"].strftime("%Y-%m-%d %H:%M")
        slot_end = chosen_slot["end_time"] if isinstance(chosen_slot["end_time"], str) else chosen_slot["end_time"].strftime("%Y-%m-%d %H:%M")

        slots = AppointmentMapper._get_available_slots(appointment)
        for slot in slots:
            if slot["start_time"] == slot_start and slot["end_time"] == slot_end:
                if slot["is_selected"]:
                    return None
                slot["is_selected"] = True
                slot["selected_by_student_id"] = student_id
                AppointmentMapper._set_available_slots_data(appointment, slots)

                appointment.student_id = student.id
                appointment.selected_slot_json = json.dumps(slot)
                dt = datetime.strptime(slot["start_time"], "%Y-%m-%d %H:%M")
                appointment.appointment_date = dt.date()
                appointment.appointment_time = dt.time()
                appointment.appointment_status = AppointmentStatus.Slot_Selected.value

                db.session.commit()
                return "Slot selected successfully."
        return None

    @staticmethod
    def confirm_appointment(appointment, venue):
        if not venue:
            return False
        if not appointment.selected_slot_json:
            return False
        appointment.venue = venue
        appointment.appointment_status = AppointmentStatus.Confirmed.value
        db.session.commit()
        return True

    @staticmethod
    def cancel_appointment(appointment):
        appointment.appointment_status = AppointmentStatus.Cancelled.value
        selected = AppointmentMapper._get_selected_slot(appointment)
        if selected:
            slots = AppointmentMapper._get_available_slots(appointment)
            for slot in slots:
                if slot["id"] == selected["id"]:
                    slot["is_selected"] = False
                    slot["selected_by_student_id"] = None
                    break
            AppointmentMapper._set_available_slots_data(appointment, slots)
            appointment.selected_slot_json = None
        db.session.commit()
        return True

    @staticmethod
    def _build_slot_data(slot_list):
        """Convert slot data to JSON-safe records and skip duplicates defensively."""
        serializable_slots = []
        seen_slot_starts = set()

        for slot_data in slot_list:
            start_time = slot_data["start_time"]
            end_time = slot_data["end_time"]

            start_text = start_time if isinstance(start_time, str) else start_time.strftime("%Y-%m-%d %H:%M")
            end_text = end_time if isinstance(end_time, str) else end_time.strftime("%Y-%m-%d %H:%M")

            if start_text in seen_slot_starts:
                continue
            seen_slot_starts.add(start_text)

            serializable_slots.append({
                "id": str(len(serializable_slots) + 1),
                "start_time": start_text,
                "end_time": end_text,
                "is_selected": False,
                "selected_by_student_id": None
            })

        return serializable_slots

    @staticmethod
    def _get_available_slots(appointment):
        try:
            return json.loads(appointment.available_slot_list_json or "[]")
        except json.JSONDecodeError:
            return []

    @staticmethod
    def _set_available_slots_data(appointment, data):
        appointment.available_slot_list_json = json.dumps(data)

    @staticmethod
    def _get_selected_slot(appointment):
        try:
            return json.loads(appointment.selected_slot_json) if appointment.selected_slot_json else None
        except json.JSONDecodeError:
            return None
