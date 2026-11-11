"""Coordinator boundary — coordinator home, forward to consultant routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.control.auth_control import get_current_coordinator

coordinator_bp = Blueprint("coordinator", __name__)


def _is_valid_student_id_format(student_id):
    return student_id.isdigit() and len(student_id) == 10


@coordinator_bp.route("/coordinator/home")
@login_required
def coordinator_home():
    return render_template("home_coordinator.html")


@coordinator_bp.route("/forward-case-to-consultant", methods=["GET", "POST"])
@login_required
def forward_case_to_consultant():
    if current_user.role != "coordinator":
        flash("Only coordinators can forward cases to consultants.")
        return redirect(url_for("auth.login"))
    coordinator = get_current_coordinator()
    if not coordinator:
        flash("Coordinator profile not found.")
        return redirect(url_for("coordinator.coordinator_home"))
    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        description = request.form.get("description", "").strip()
        if not student_id:
            flash("Student ID is required.")
            return render_template("forward_case_to_consultant.html")
        if not _is_valid_student_id_format(student_id):
            flash("Invalid Student ID format. Student ID must be 10 digits.")
            return render_template("forward_case_to_consultant.html")
        success = coordinator.forward_case_to_consultant(student_id, description)
        if success:
            flash("Case forwarded to faculty consultant successfully.")
            return redirect(url_for("coordinator.coordinator_home"))
        else:
            flash("Failed to forward case. Check that the student exists and a faculty consultant is assigned.")
    return render_template("forward_case_to_consultant.html")
