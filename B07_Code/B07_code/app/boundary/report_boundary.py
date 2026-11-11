"""Report boundary — record/search/export/log routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user

from app.control.record_control import (
    get_records_for_student, get_record_by_id, can_current_user_view_student_records,
    can_current_user_edit_student_records, add_record, modify_record, delete_record, search_records,
)
from app.control.report_control import get_export_conditions, export_records_to_docx, get_all_word_files, get_word_file_by_id
from app.control.log_control import add_demo_log, get_logs_by_faculty, get_logs_by_mentor, get_all_logs
from app.control.mentor_allocation_control import get_student_detail_info
from app.control.auth_control import get_current_mentor

report_bp = Blueprint("report", __name__)


@report_bp.route("/records/student/<student_id>")
@login_required
def student_records(student_id):
    if not can_current_user_view_student_records(student_id):
        if current_user.role == "faculty_consultant":
            flash("Warning: This student is not from your faculty. You can only view records of students within your faculty.")
        else:
            flash("You do not have permission to view records for this student.")
        return redirect(url_for("consultant.search_student"))
    info = get_student_detail_info(student_id)
    if not info:
        flash("Student not found.")
        return redirect(url_for("consultant.search_student"))
    records = get_records_for_student(student_id)
    can_edit = can_current_user_edit_student_records(student_id)
    return render_template("record_list.html", info=info, records=records, can_edit=can_edit)


@report_bp.route("/records/student/<student_id>/add", methods=["GET", "POST"])
@login_required
def add_record_page(student_id):
    if not can_current_user_edit_student_records(student_id):
        flash("You do not have permission to add records for this student.")
        return redirect(url_for("report.student_records", student_id=student_id))
    info = get_student_detail_info(student_id)
    if not info:
        flash("Student not found.")
        return redirect(url_for("consultant.search_student"))
    if request.method == "POST":
        success, message, record = add_record(
            student_id,
            request.form.get("date", ""),
            request.form.get("time", ""),
            request.form.get("problem_statement", ""),
            request.form.get("interview_summary", ""),
            request.form.get("followup_action", ""),
        )
        flash(message)
        if success:
            return redirect(url_for("report.student_records", student_id=student_id))
    return render_template("record_form.html", info=info, record=None, mode="add")


@report_bp.route("/records/<record_id>")
@login_required
def record_detail(record_id):
    record = get_record_by_id(record_id)
    if not record:
        flash("Record not found.")
        return redirect(url_for("consultant.search_student"))
    if not can_current_user_view_student_records(record.student.student_id):
        flash("You do not have permission to view this record.")
        return redirect(url_for("consultant.search_student"))
    return render_template("record_detail.html", record=record)


@report_bp.route("/records/<record_id>/edit", methods=["GET", "POST"])
@login_required
def edit_record_page(record_id):
    record = get_record_by_id(record_id)
    if not record:
        flash("Record not found.")
        return redirect(url_for("consultant.search_student"))
    student_id = record.student.student_id
    if not can_current_user_edit_student_records(student_id):
        flash("You do not have permission to edit this record.")
        return redirect(url_for("report.record_detail", record_id=record_id))
    info = get_student_detail_info(student_id)
    if request.method == "POST":
        success, message = modify_record(
            record_id,
            request.form.get("problem_statement", ""),
            request.form.get("interview_summary", ""),
            request.form.get("followup_action", ""),
        )
        flash(message)
        if success:
            return redirect(url_for("report.record_detail", record_id=record_id))
    return render_template("record_form.html", info=info, record=record, mode="edit")


@report_bp.route("/records/<record_id>/delete", methods=["POST"])
@login_required
def delete_record_page(record_id):
    record = get_record_by_id(record_id)
    student_id = record.student.student_id if record else None
    success, message = delete_record(record_id)
    flash(message)
    if student_id:
        return redirect(url_for("report.student_records", student_id=student_id))
    return redirect(url_for("consultant.search_student"))


@report_bp.route("/records/search", methods=["GET", "POST"])
@login_required
def record_search():
    if current_user.role not in ["mentor", "coordinator", "faculty_consultant"]:
        flash("You do not have permission to search records.")
        return redirect(url_for("auth.login"))
    records = []
    keyword = academic_year = mentor_name = student_name = ""
    if request.method == "POST":
        keyword = request.form.get("keyword", "")
        academic_year = request.form.get("academic_year", "")
        mentor_name = request.form.get("mentor_name", "")
        student_name = request.form.get("student_name", "")
        records = search_records(keyword, academic_year, mentor_name, student_name)
        if not records:
            flash("No matching records found.")
    return render_template("record_search.html", records=records, keyword=keyword,
                           academic_year=academic_year, mentor_name=mentor_name, student_name=student_name)


@report_bp.route("/records/export", methods=["GET", "POST"])
@login_required
def export_records_page():
    if current_user.role not in ["faculty_consultant", "mentor", "coordinator"]:
        flash("You do not have permission to export records.")
        return redirect(url_for("auth.login"))
    years, mentors, students, departments = get_export_conditions()
    if request.method == "POST":
        academic_year_list = request.form.getlist("academic_year_list")
        conditions = {
            "Academic Year List": academic_year_list,
            "Department Name": request.form.get("department_name", ""),
            "Mentor Name": request.form.get("mentor_name", ""),
            "Student Name": request.form.get("student_name", ""),
        }
        records = search_records(
            academic_year_list=conditions["Academic Year List"],
            department_name=conditions["Department Name"],
            mentor_name=conditions["Mentor Name"],
            student_name=conditions["Student Name"],
        )
        success, message, word_file = export_records_to_docx(records, conditions=conditions)
        flash(message)
        if success:
            return redirect(url_for("report.word_files"))
    return render_template("export_records.html", years=years, mentors=mentors, students=students, departments=departments)


@report_bp.route("/records/word-files")
@login_required
def word_files():
    files = get_all_word_files()
    return render_template("wordfile_list.html", files=files)


@report_bp.route("/records/word-files/<int:file_id>/download")
@login_required
def download_word_file(file_id):
    import os

    word_file = get_word_file_by_id(file_id)
    if not word_file:
        flash("Word file not found.")
        return redirect(url_for("report.word_files"))

    raw_path = word_file.file_path or ""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    file_path = raw_path if os.path.isabs(raw_path) else os.path.join(project_root, raw_path)

    if not os.path.exists(file_path):
        flash("Word file is missing on disk: " + raw_path)
        return redirect(url_for("report.word_files"))

    return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))

@report_bp.route("/records/logs", methods=["GET", "POST"])
@login_required
def log_list():
    if current_user.role not in ["faculty_consultant", "coordinator", "mentor", "faculty_member"]:
        flash("You do not have permission to view log activities.")
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        success, message = add_demo_log(
            request.form.get("student_id", ""),
            request.form.get("function_access", "View Interview Records"),
        )
        flash(message)
        return redirect(url_for("report.log_list"))
    if current_user.role == "faculty_consultant" and current_user.faculty_id:
        logs = get_logs_by_faculty(current_user.faculty_id)
    elif current_user.role == "faculty_member" and current_user.faculty_id:
        logs = get_logs_by_faculty(current_user.faculty_id)
    elif current_user.role == "mentor":
        mentor = get_current_mentor()
        logs = get_logs_by_mentor(mentor) if mentor else []
    else:
        logs = get_all_logs()
    student_id_filter = request.args.get("student_id", "").strip()
    if student_id_filter:
        from app.control.mentor_allocation_control import get_student_by_student_id

        student = get_student_by_student_id(student_id_filter)
        if not student:
            flash("Student not found.")
            logs = []
        else:
            # Checklist 3.8: faculty-side users must receive a clear warning
            # when searching activity logs for a student outside their faculty.
            student_faculty_id = None
            if student.group and student.group.major and student.group.major.department:
                student_faculty_id = student.group.major.department.faculty_id

            if current_user.role in ["faculty_consultant", "faculty_member"] and current_user.faculty_id:
                if student_faculty_id != current_user.faculty_id:
                    flash("Warning: This student is not from your faculty. You can only view log information of students within your faculty.")
                    logs = []
                else:
                    logs = [log for log in logs if log.student_id == student.id]
            else:
                logs = [log for log in logs if log.student_id == student.id]
    return render_template("log_list.html", logs=logs, student_id_filter=student_id_filter)
