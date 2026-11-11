"""Appointment business logic control."""

from flask_login import current_user

from app.mapper.user_mapper import StudentMapper
from app.mapper.appointment_mapper import AppointmentMapper
from app.control.auth_control import get_current_mentor, get_current_student


def get_students_for_current_mentor():
    mentor = get_current_mentor()
    if not mentor:
        return []
    students = []
    for group in mentor.groups:
        students.extend(group.students)
    return students


def create_appointment(student_id, slot_text_list, content="Appointment request"):
    mentor = get_current_mentor()
    if not mentor:
        return False, "Only mentors can create appointments."

    student = StudentMapper.find_by_id(student_id)
    if not student:
        return False, "Student not found."

    success, msg, _ = AppointmentMapper.create(mentor, student, slot_text_list, content, sender_id=current_user.id)
    return success, msg


def get_mentor_appointments():
    mentor = get_current_mentor()
    if not mentor:
        return []
    return AppointmentMapper.find_by_mentor(mentor.id)


def get_student_appointments():
    student = get_current_student()
    if not student:
        return []
    return AppointmentMapper.find_by_student(student.id)


def choose_appointment_slot(appointment_id, slot_id):
    student = get_current_student()
    if not student:
        return False, "Only students can choose appointment slots."

    appointment = AppointmentMapper.find_by_id(appointment_id)
    if not appointment:
        return False, "Appointment not found."

    if appointment.student_id != student.id:
        return False, "This appointment does not belong to you."

    available = appointment.available_slot_list
    chosen_slot = None
    for s in available:
        if str(s["id"]) == str(slot_id):
            chosen_slot = {"start_time": s["start_time"], "end_time": s["end_time"]}
            break

    if not chosen_slot:
        return False, "Slot not found."

    result = AppointmentMapper.choose_slot(appointment, student.id, chosen_slot)
    if not result:
        return False, "Failed to choose slot."
    return True, result


def confirm_appointment(appointment_id, venue):
    venue = venue.strip() if venue else ""
    if not venue:
        return False, "Venue cannot be empty."

    mentor = get_current_mentor()
    if not mentor:
        return False, "Only mentors can confirm appointments."

    appointment = AppointmentMapper.find_by_id(appointment_id)
    if not appointment:
        return False, "Appointment not found."

    if appointment.mentor_id != mentor.id:
        return False, "You cannot confirm this appointment."

    success = AppointmentMapper.confirm_appointment(appointment, venue)
    if not success:
        return False, "Please wait until the student selects a slot."
    return True, "Appointment confirmed successfully."


def cancel_appointment(appointment_id):
    appointment = AppointmentMapper.find_by_id(appointment_id)
    if not appointment:
        return False, "Appointment not found."

    mentor = get_current_mentor()
    student = get_current_student()

    is_related_mentor = mentor and appointment.mentor_id == mentor.id
    is_related_student = student and appointment.student_id == student.id

    if not is_related_mentor and not is_related_student:
        return False, "You cannot cancel this appointment."

    AppointmentMapper.cancel_appointment(appointment)
    return True, "Appointment cancelled successfully."
