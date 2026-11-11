"""Appointment boundary — appointment routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.control.appointment_control import (
    get_students_for_current_mentor, create_appointment, get_mentor_appointments,
    get_student_appointments, choose_appointment_slot, confirm_appointment, cancel_appointment,
)

appointment_bp = Blueprint("appointment", __name__, url_prefix="/appointments")


@appointment_bp.route("/")
@login_required
def appointment_home():
    if current_user.role == "mentor":
        return redirect(url_for("appointment.mentor_appointments"))
    if current_user.role == "student":
        return redirect(url_for("appointment.student_appointments"))
    flash("Only mentors and students can use appointments.")
    return redirect(url_for("auth.login"))


@appointment_bp.route("/mentor")
@login_required
def mentor_appointments():
    if current_user.role != "mentor":
        flash("Only mentors can view this page.")
        return redirect(url_for("auth.login"))
    appointments = get_mentor_appointments()
    return render_template("appointment_mentor.html", appointments=appointments)


@appointment_bp.route("/mentor/create", methods=["GET", "POST"])
@login_required
def create_appointment_page():
    if current_user.role != "mentor":
        flash("Only mentors can create appointments.")
        return redirect(url_for("auth.login"))
    students = get_students_for_current_mentor()
    if request.method == "POST":
        student_id = request.form.get("student_id")
        content = request.form.get("content", "Appointment request")

        # New UI submits one hidden input named "slots" for each selected slot.
        # Keep the old slot1/slot2/slot3 fallback so existing tests or old forms still work.
        slot_text_list = [slot.strip() for slot in request.form.getlist("slots") if slot.strip()]
        if not slot_text_list:
            slot_text_list = [
                request.form.get("slot1", ""),
                request.form.get("slot2", ""),
                request.form.get("slot3", "")
            ]

        success, message = create_appointment(student_id=student_id, slot_text_list=slot_text_list, content=content)
        flash(message)
        if success:
            return redirect(url_for("appointment.mentor_appointments"))
    return render_template("appointment_create.html", students=students)


@appointment_bp.route("/student")
@login_required
def student_appointments():
    if current_user.role != "student":
        flash("Only students can view this page.")
        return redirect(url_for("auth.login"))
    appointments = get_student_appointments()
    return render_template("appointment_student.html", appointments=appointments)


@appointment_bp.route("/<int:appointment_id>/choose", methods=["POST"])
@login_required
def choose_slot(appointment_id):
    slot_id = request.form.get("slot_id")
    success, message = choose_appointment_slot(appointment_id, slot_id)
    flash(message)
    return redirect(url_for("appointment.student_appointments"))


@appointment_bp.route("/<int:appointment_id>/confirm", methods=["POST"])
@login_required
def confirm(appointment_id):
    venue = request.form.get("venue", "")
    success, message = confirm_appointment(appointment_id, venue)
    flash(message)
    return redirect(url_for("appointment.mentor_appointments"))


@appointment_bp.route("/<int:appointment_id>/cancel", methods=["POST"])
@login_required
def cancel(appointment_id):
    success, message = cancel_appointment(appointment_id)
    flash(message)
    if current_user.role == "mentor":
        return redirect(url_for("appointment.mentor_appointments"))
    if current_user.role == "student":
        return redirect(url_for("appointment.student_appointments"))
    return redirect(url_for("appointment.appointment_home"))
