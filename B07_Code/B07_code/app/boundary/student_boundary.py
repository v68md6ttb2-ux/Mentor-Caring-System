"""Student boundary — student home, mentor info routes."""

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.control.mentor_allocation_control import get_student_mentor_info
from app.control.log_control import add_student_activity_log

student_bp = Blueprint("student", __name__)


@student_bp.route("/student/home")
@login_required
def student_home():
    if current_user.role == "student":
        add_student_activity_log("Access Student Home")
    return render_template("home_student.html")


@student_bp.route("/student/mentor-info")
@login_required
def student_mentor_info():
    if current_user.role != "student":
        flash("Only students can view this page.")
        return redirect(url_for("auth.login"))
    info = get_student_mentor_info()
    if not info:
        flash("Student profile not found.")
        return redirect(url_for("student.student_home"))
    add_student_activity_log("Check Mentor Information")
    return render_template("student_mentor_info.html", info=info)
