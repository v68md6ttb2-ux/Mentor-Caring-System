"""Admin boundary — organization management, consultants, import routes."""

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.control.organization_control import (
    get_organization_structure, add_faculty, add_department, add_major, preview_org_excel,
    get_all_active_faculties, get_all_active_departments, import_organization as do_import_organization,
)
from app.control.mentor_allocation_control import (
    get_all_faculty_consultants, get_faculties_without_consultant,
    add_faculty_consultant, change_faculty_consultant, delete_faculty_consultant,
)

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/home")
@login_required
def admin_home():
    return render_template("home_admin.html")


@admin_bp.route("/organization")
@login_required
def organization():
    if current_user.role != "admin":
        flash("Only administrators can view the organization management page.")
        return redirect(url_for("auth.login"))
    faculties = get_organization_structure()
    return render_template("organization.html", faculties=faculties)


@admin_bp.route("/organization/faculty/add", methods=["GET", "POST"])
@login_required
def add_faculty_page():
    if current_user.role != "admin":
        flash("Only administrators can add faculties.")
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        name = request.form.get("name", "")
        success, message = add_faculty(name)
        flash(message)
        if success:
            return redirect(url_for("admin.organization"))
    return render_template("add_faculty.html")


@admin_bp.route("/organization/department/add", methods=["GET", "POST"])
@login_required
def add_department_page():
    if current_user.role != "admin":
        flash("Only administrators can add departments.")
        return redirect(url_for("auth.login"))
    faculties = get_all_active_faculties()
    if request.method == "POST":
        faculty_id = request.form.get("faculty_id")
        name = request.form.get("name", "")
        success, message = add_department(faculty_id, name)
        flash(message)
        if success:
            return redirect(url_for("admin.organization"))
    return render_template("add_department.html", faculties=faculties)


@admin_bp.route("/organization/major/add", methods=["GET", "POST"])
@login_required
def add_major_page():
    if current_user.role != "admin":
        flash("Only administrators can add majors.")
        return redirect(url_for("auth.login"))
    departments = get_all_active_departments()
    if request.method == "POST":
        department_id = request.form.get("department_id")
        name = request.form.get("name", "")
        success, message = add_major(department_id, name)
        flash(message)
        if success:
            return redirect(url_for("admin.organization"))
    return render_template("add_major.html", departments=departments)


@admin_bp.route("/admin/consultants")
@login_required
def admin_consultants():
    if current_user.role != "admin":
        flash("Only administrators can manage faculty consultants.")
        return redirect(url_for("auth.login"))
    consultants = get_all_faculty_consultants()
    return render_template("consultant_list.html", consultants=consultants)


@admin_bp.route("/admin/consultants/add", methods=["GET", "POST"])
@login_required
def add_consultant():
    if current_user.role != "admin":
        flash("Only administrators can add faculty consultants.")
        return redirect(url_for("auth.login"))
    faculties = get_all_active_faculties()
    if request.method == "POST":
        account = request.form.get("account", "")
        password = request.form.get("password", "")
        name = request.form.get("name", "")
        email = request.form.get("email", "")
        faculty_id = request.form.get("faculty_id", "")
        success, message = add_faculty_consultant(account, password, name, email, faculty_id)
        flash(message)
        if success:
            return redirect(url_for("admin.admin_consultants"))
    return render_template("add_consultant.html", faculties=faculties)


@admin_bp.route("/admin/consultants/change", methods=["GET", "POST"])
@login_required
def change_consultant():
    if current_user.role != "admin":
        flash("Only administrators can change faculty consultants.")
        return redirect(url_for("auth.login"))
    consultants = get_all_faculty_consultants()
    faculties = get_all_active_faculties()
    if request.method == "POST":
        consultant_id = request.form.get("consultant_id")
        faculty_id = request.form.get("faculty_id", "")
        success, message = change_faculty_consultant(consultant_id, faculty_id)
        flash(message)
        if success:
            return redirect(url_for("admin.admin_consultants"))
    return render_template("change_consultant.html", consultants=consultants, faculties=faculties)


@admin_bp.route("/admin/consultants/delete", methods=["POST"])
@login_required
def delete_consultant():
    if current_user.role != "admin":
        flash("Only administrators can delete faculty consultants.")
        return redirect(url_for("auth.login"))
    consultant_id = request.form.get("consultant_id")
    success, message = delete_faculty_consultant(consultant_id)
    flash(message)
    return redirect(url_for("admin.admin_consultants"))


@admin_bp.route("/admin/import-organization", methods=["GET", "POST"])
@login_required
def import_organization():
    if current_user.role != "admin":
        flash("Only administrators can import organization structure.")
        return redirect(url_for("auth.login"))

    upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
    os.makedirs(upload_dir, exist_ok=True)
    default_file_path = os.path.join(upload_dir, "org_import.xlsx")

    if request.method == "POST":
        action = request.form.get("action")

        if action == "preview":
            file = request.files.get("excel_file")
            if not file or not file.filename.endswith((".xlsx", ".xls")):
                flash("Please upload a valid Excel file (.xlsx or .xls).")
                return render_template("import_org.html", preview_rows=None)

            file.save(default_file_path)
            success, message, rows = preview_org_excel(default_file_path)
            if not success:
                flash(f"Failed to read file: {message}")
                return render_template("import_org.html", preview_rows=None)

            flash(message)
            return render_template("import_org.html", preview_rows=rows, file_path=default_file_path)

        if action == "confirm":
            file_path = request.form.get("file_path") or default_file_path
            file_path = os.path.abspath(file_path)

            if os.path.commonpath([upload_dir, file_path]) != upload_dir or not os.path.exists(file_path):
                flash("Preview file is missing. Please upload and preview the Excel file again.")
                return render_template("import_org.html", preview_rows=None)

            success, message, rows = preview_org_excel(file_path)
            if not success:
                flash(f"Failed to read file: {message}")
                return render_template("import_org.html", preview_rows=None)

            result = do_import_organization(file_path)
            if result:
                flash(f"Organization imported successfully. {len(rows)} rows processed.")
            else:
                flash("Import failed. Check file format (Faculty | Department | Major).")
            return redirect(url_for("admin.organization"))

        flash("Invalid import action.")
        return render_template("import_org.html", preview_rows=None)

    return render_template("import_org.html", preview_rows=None)
