"""Authentication boundary — login/logout/change_password/home routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user

from app.control.auth_control import get_user_by_account, get_student_by_user_db_id
from app.utils.time_utils import local_now_iso

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        account = request.form.get("account")
        password = request.form.get("password")

        user = get_user_by_account(account)

        if not user or user.password != password:
            flash("Invalid account or password.")
            return render_template("login.html")

        if user.role == "student":
            student = get_student_by_user_db_id(user.id)
            if not student or not student.is_in_group():
                flash("You are not assigned to any MCP group.")
                return render_template("login.html")

        login_user(user)

        if user.role == "student":
            # Start a real activity-log session. Student activity logs should
            # show the actual login time and the eventual logout time, rather
            # than using the same timestamp for both columns.
            session["student_login_time"] = local_now_iso()
            session["student_session_log_ids"] = []
            session.modified = True

        if user.role == "admin":
            return redirect(url_for("admin.admin_home"))
        if user.role == "faculty_consultant":
            return redirect(url_for("consultant.faculty_home"))
        if user.role == "mentor":
            return redirect(url_for("mentor.mentor_home"))
        if user.role == "student":
            return redirect(url_for("student.student_home"))
        if user.role == "coordinator":
            return redirect(url_for("coordinator.coordinator_home"))
        if user.role == "faculty_member":
            return redirect(url_for("auth.faculty_member_home"))

        flash("Unknown user role.")
        return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    # Close the student's activity-log session before Flask-Login clears
    # current_user. This updates all logs generated during this login session
    # so their logout_time is the real logout time.
    if getattr(current_user, "is_authenticated", False) and getattr(current_user, "role", None) == "student":
        try:
            from app.control.log_control import close_student_activity_session
            close_student_activity_session(add_logout_log=True)
        except Exception:
            # Logging must not block a normal logout.
            pass

    logout_user()
    session.pop("student_login_time", None)
    session.pop("student_session_log_ids", None)
    session.modified = True
    return redirect(url_for("auth.login"))


@auth_bp.route("/faculty-member/home")
@login_required
def faculty_member_home():
    return render_template("home_faculty_member.html")


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if new_password != confirm_password:
            flash("New passwords do not match.")
            return render_template("change_password.html")

        success = current_user.change_password(old_password, new_password)
        if success:
            flash("Password changed successfully.")
            return redirect(url_for("auth.login"))
        else:
            flash("Failed to change password. Check your old password and ensure new password is at least 6 characters.")

    return render_template("change_password.html")
