"""Mentor boundary — mentor home, forward case routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.control.auth_control import get_current_mentor

mentor_bp = Blueprint("mentor", __name__)


def _is_valid_student_id_format(student_id):
    return student_id.isdigit() and len(student_id) == 10


@mentor_bp.route("/mentor/home")
@login_required
def mentor_home():
    return render_template("home_mentor.html")


@mentor_bp.route("/forward-case", methods=["GET", "POST"])
@login_required
def forward_case():
    if current_user.role != "mentor":
        flash("Only mentors can forward cases.")
        return redirect(url_for("auth.login"))
    mentor = get_current_mentor()
    if not mentor:
        flash("Mentor profile not found.")
        return redirect(url_for("mentor.mentor_home"))
    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        description = request.form.get("description", "").strip()
        if not student_id:
            flash("Student ID is required.")
            students = [s for group in mentor.groups for s in group.students]
            return render_template("forward_case.html", students=students)
        if not _is_valid_student_id_format(student_id):
            flash("Invalid Student ID format. Student ID must be 10 digits.")
            students = [s for group in mentor.groups for s in group.students]
            return render_template("forward_case.html", students=students)
        success = mentor.forward_case(student_id, description)
        if success:
            flash("Case forwarded to coordinator successfully.")
            return redirect(url_for("mentor.mentor_home"))
        else:
            flash("Failed to forward case. Check that the student is in your group and a coordinator exists.")
    students = [s for group in mentor.groups for s in group.students]
    return render_template("forward_case.html", students=students)
