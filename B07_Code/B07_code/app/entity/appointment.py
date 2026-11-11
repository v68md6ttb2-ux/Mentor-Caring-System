"""Appointment entity class."""

import json
from app.utils.time_utils import local_now

from app.extensions import db
from app.entity.enums import AppointmentStatus


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sent_datetime = db.Column(db.DateTime, default=local_now, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_data_json = db.Column(db.Text, default="[]", nullable=False)

    appointment_date = db.Column(db.Date, nullable=True)
    appointment_time = db.Column(db.Time, nullable=True)
    venue = db.Column(db.String(255), nullable=True)

    appointment_status = db.Column(
        db.String(30),
        default=AppointmentStatus.Requested.value,
        nullable=False
    )

    available_slot_list_json = db.Column(db.Text, default="[]", nullable=False)
    selected_slot_json = db.Column(db.Text, nullable=True)

    mentor_id = db.Column(db.Integer, db.ForeignKey("mentors.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=True)

    mentor = db.relationship("Mentor", backref="appointments", foreign_keys=[mentor_id])
    student = db.relationship("Student", backref="appointments", foreign_keys=[student_id])
    sender = db.relationship("User", foreign_keys=[sender_id], backref="sent_appointments")

    def _get_available_slots(self):
        try:
            return json.loads(self.available_slot_list_json or "[]")
        except json.JSONDecodeError:
            return []

    def _set_available_slots_data(self, data):
        self.available_slot_list_json = json.dumps(data)

    def _get_selected_slot(self):
        try:
            return json.loads(self.selected_slot_json) if self.selected_slot_json else None
        except json.JSONDecodeError:
            return None

    @property
    def available_slot_list(self):
        return self._get_available_slots()

    def set_available_slots(self, slot_list):
        from app.mapper.appointment_mapper import AppointmentMapper
        AppointmentMapper.set_available_slots(self, slot_list)

    def choose_slot(self, student_id, chosen_slot):
        from app.mapper.appointment_mapper import AppointmentMapper
        return AppointmentMapper.choose_slot(self, student_id, chosen_slot)

    def confirm_appointment(self, venue):
        from app.mapper.appointment_mapper import AppointmentMapper
        return AppointmentMapper.confirm_appointment(self, venue)

    def cancel_appointment(self):
        from app.mapper.appointment_mapper import AppointmentMapper
        return AppointmentMapper.cancel_appointment(self)

    def setAvailableSlots(self, slot_list):
        self.set_available_slots(slot_list)

    def chooseSlot(self, student_id, chosen_slot):
        return self.choose_slot(student_id, chosen_slot)

    def confirmAppointment(self, venue):
        return self.confirm_appointment(venue)

    def cancelAppointment(self):
        return self.cancel_appointment()
