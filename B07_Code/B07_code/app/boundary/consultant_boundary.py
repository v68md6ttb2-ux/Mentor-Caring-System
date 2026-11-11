"""Faculty Consultant boundary — groups, students, import, search routes."""

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.control.mentor_allocation_control import (
    get_all_mcp_groups, get_all_mentors, change_group_mentor,
    get_all_students, add_student_to_group, remove_student_from_group,
    get_student_detail_info, search_mentor_info, preview_student_excel, preview_coordinator_excel,
    get_group_by_db_id, import_mcp_info, import_coordinator_info,
)

consultant_bp = Blueprint("consultant", __name__)


def _is_valid_student_id_format(student_id):
    return student_id.isdigit() and len(student_id) == 10


def _upload_dir():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
    os.makedirs(path, exist_ok=True)
    return path


def _safe_uploaded_path(file_name):
    if not file_name:
        return None
    base_name = os.path.basename(file_name)
    path = os.path.abspath(os.path.join(_upload_dir(), base_name))
    if os.path.dirname(path) != _upload_dir():
        return None
    return path


@consultant_bp.route("/faculty/home")
@login_required
def faculty_home():
    return render_template("home_faculty_consultant.html")


@consultant_bp.route("/faculty/groups")
@login_required
def faculty_groups():
    if current_user.role != "faculty_consultant":
        flash("Only faculty consultants can view MCP groups.")
        return redirect(url_for("auth.login"))
    groups = get_all_mcp_groups()
    return render_template("group_list.html", groups=groups)


@consultant_bp.route("/faculty/group/change-mentor", methods=["GET", "POST"])
@login_required
def change_group_mentor_page():
    if current_user.role != "faculty_consultant":
        flash("Only faculty consultants can change group mentors.")
        return redirect(url_for("auth.login"))
    groups = get_all_mcp_groups()
    mentors = get_all_mentors()
    if request.method == "POST":
        group_id = request.form.get("group_id")
        mentor_id = request.form.get("mentor_id")
        success, message = change_group_mentor(group_id, mentor_id)
        flash(message)
        if success:
            return redirect(url_for("consultant.faculty_groups"))
    return render_template("change_group_mentor.html", groups=groups, mentors=mentors)


@consultant_bp.route("/faculty/group/add-student", methods=["GET", "POST"])
@login_required
def add_student_to_group_page():
    if current_user.role != "faculty_consultant":
        flash("Only faculty consultants can add students to groups.")
        return redirect(url_for("auth.login"))
    groups = get_all_mcp_groups()
    students = get_all_students()
    if request.method == "POST":
        student_id = request.form.get("student_id", "")
        group_id = request.form.get("group_id")
        success, message = add_student_to_group(student_id, group_id)
        flash(message)
        if success:
            return redirect(url_for("consultant.faculty_groups"))
    return render_template("add_student_to_group.html", groups=groups, students=students)


@consultant_bp.route("/faculty/group/remove-student", methods=["GET", "POST"])
@login_required
def remove_student_from_group_page():
    if current_user.role != "faculty_consultant":
        flash("Only faculty consultants can remove students from groups.")
        return redirect(url_for("auth.login"))
    students = get_all_students()
    if request.method == "POST":
        student_id = request.form.get("student_id", "")
        success, message = remove_student_from_group(student_id)
        flash(message)
        if success:
            return redirect(url_for("consultant.faculty_groups"))
    return render_template("remove_student_from_group.html", students=students)


@consultant_bp.route("/students/search", methods=["GET", "POST"])
@login_required
def search_student():
    allowed_roles = ["mentor", "coordinator", "faculty_consultant"]
    if current_user.role not in allowed_roles:
        flash("You do not have permission to search student information.")
        return redirect(url_for("auth.login"))
    student_id = ""
    if request.method == "POST":
        # Accept both the current form field (student_id) and the legacy
        # test field (keyword) so student search remains backward-compatible.
        student_id = (
            request.form.get("student_id", "").strip()
            or request.form.get("keyword", "").strip()
        )
        if not student_id:
            flash("Student ID cannot be empty.")
            return render_template("student_search.html", student_id=student_id)
        if not _is_valid_student_id_format(student_id):
            flash("Invalid Student ID format. Student ID must be 10 digits.")
            return render_template("student_search.html", student_id=student_id)
        return redirect(url_for("consultant.student_detail", student_id=student_id))
    return render_template("student_search.html", student_id=student_id)


@consultant_bp.route("/students/<student_id>")
@login_required
def student_detail(student_id):
    allowed_roles = ["mentor", "coordinator", "faculty_consultant"]
    if current_user.role not in allowed_roles:
        flash("You do not have permission to view student information.")
        return redirect(url_for("auth.login"))
    student_id = student_id.strip()
    if not _is_valid_student_id_format(student_id):
        flash("Invalid Student ID format. Student ID must be 10 digits.")
        return redirect(url_for("consultant.search_student"))
    info = get_student_detail_info(student_id)
    if not info:
        flash("Student not found.")
        return redirect(url_for("consultant.search_student"))
    return render_template("student_detail.html", info=info)


@consultant_bp.route("/faculty/import-students", methods=["GET", "POST"])
@login_required
def import_students():
    if current_user.role != "faculty_consultant":
        flash("Only faculty consultants can import students.")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "preview":
            file = request.files.get("excel_file")
            if not file or not file.filename.endswith((".xlsx", ".xls")):
                flash("Please upload a valid Excel file (.xlsx or .xls).")
                return render_template("import_students.html", preview_rows=None)
            file_path = os.path.join(_upload_dir(), "students_import.xlsx")
            file.save(file_path)
        else:
            file_path = _safe_uploaded_path(request.form.get("file_path") or "students_import.xlsx")

        if not file_path or not os.path.exists(file_path):
            flash("Please preview a valid student Excel file before confirming import.")
            return render_template("import_students.html", preview_rows=None)

        success, message, rows = preview_student_excel(file_path)
        if not success:
            flash(f"Failed to read file: {message}")
            return render_template("import_students.html", preview_rows=None)

        if action == "preview":
            flash(message)
            return render_template("import_students.html", preview_rows=rows, file_path=os.path.basename(file_path))

        if action == "confirm":
            result = import_mcp_info(file_path)
            if result:
                flash(f"Students imported successfully. {len(rows)} rows processed.")
            else:
                flash("Import failed. Check Appendix B format.")
            return redirect(url_for("consultant.faculty_groups"))

    return render_template("import_students.html", preview_rows=None)


@consultant_bp.route("/faculty/import-coordinators", methods=["GET", "POST"])
@login_required
def import_coordinators():
    if current_user.role != "faculty_consultant":
        flash("Only faculty consultants can import coordinators.")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "preview":
            file = request.files.get("excel_file")
            if not file or not file.filename.endswith((".xlsx", ".xls")):
                flash("Please upload a valid Excel file (.xlsx or .xls).")
                return render_template("import_coordinators.html", preview_rows=None)
            file_path = os.path.join(_upload_dir(), "coordinators_import.xlsx")
            file.save(file_path)
        else:
            file_path = _safe_uploaded_path(request.form.get("file_path") or "coordinators_import.xlsx")

        if not file_path or not os.path.exists(file_path):
            flash("Please preview a valid coordinator Excel file before confirming import.")
            return render_template("import_coordinators.html", preview_rows=None)

        success, message, rows = preview_coordinator_excel(file_path)
        if not success:
            flash(f"Failed to read file: {message}")
            return render_template("import_coordinators.html", preview_rows=None)

        if action == "preview":
            flash(message)
            return render_template("import_coordinators.html", preview_rows=rows, file_path=os.path.basename(file_path))

        if action == "confirm":
            result = import_coordinator_info(file_path)
            if result:
                flash(f"Coordinators imported successfully. {len(rows)} rows processed.")
            else:
                flash("Import failed. Check Appendix C format.")
            return redirect(url_for("consultant.faculty_groups"))

    return render_template("import_coordinators.html", preview_rows=None)


@consultant_bp.route("/mentors/search", methods=["GET", "POST"])
@login_required
def search_mentor():
    allowed_roles = ["coordinator", "faculty_consultant"]
    if current_user.role not in allowed_roles:
        flash("You do not have permission to search mentor information.")
        return redirect(url_for("auth.login"))
    groups = None
    keyword = ""
    selected_group = None
    selected_group_id = ""
    if request.method == "POST":
        action = request.form.get("action")
        keyword = request.form.get("keyword", "").strip()
        if action == "search":
            if not keyword:
                flash("Search keyword cannot be empty.")
                return render_template("mentor_search.html", groups=groups, keyword=keyword,
                                       selected_group=selected_group, selected_group_id=selected_group_id)
            groups = search_mentor_info(keyword)
            if not groups:
                flash("No matching mentor or group found.")
        elif action == "show_members":
            selected_group_id = request.form.get("selected_group_id", "").strip()
            if keyword:
                groups = search_mentor_info(keyword)
            if not selected_group_id:
                flash("Please select a group ID before showing members.")
                return render_template("mentor_search.html", groups=groups, keyword=keyword,
                                       selected_group=selected_group, selected_group_id=selected_group_id)
            try:
                selected_group = get_group_by_db_id(int(selected_group_id))
            except ValueError:
                selected_group = None
            if not selected_group:
                flash("Selected group was not found.")
    return render_template("mentor_search.html", groups=groups, keyword=keyword,
                           selected_group=selected_group, selected_group_id=selected_group_id)
