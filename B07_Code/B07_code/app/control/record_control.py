"""Record CRUD and search control logic."""

import uuid
from datetime import datetime

from flask_login import current_user

from app.entity.record import Record
from app.mapper.user_mapper import StudentMapper
from app.mapper.record_mapper import RecordMapper
from app.control.auth_control import get_current_mentor
from app.control.mentor_allocation_control import (
    get_student_by_student_id,
    can_mentor_access_student,
)


def _not_blank(value):
    return value is not None and str(value).strip() != ""


def _parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def _parse_time(value):
    return datetime.strptime(value, "%H:%M").time()


def _student_faculty_id(student):
    if student and student.group and student.group.major and student.group.major.department:
        return student.group.major.department.faculty_id
    return None


def get_records_for_student(display_student_id):
    student = get_student_by_student_id(display_student_id)
    if not student:
        return []
    return RecordMapper.find_by_student_id(student.id)


def get_record_by_id(record_id):
    return RecordMapper.find_by_record_id(record_id)


def can_current_user_view_student_records(display_student_id):
    if not current_user.is_authenticated:
        return False
    if current_user.role == "faculty_consultant":
        student = get_student_by_student_id(display_student_id)
        if not student:
            return False
        consultant_faculty_id = current_user.faculty_id
        if consultant_faculty_id is None:
            return True
        student_fac_id = _student_faculty_id(student)
        return student_fac_id is not None and student_fac_id == consultant_faculty_id
    if current_user.role == "coordinator":
        return True
    if current_user.role == "mentor":
        return can_mentor_access_student(current_user.id, display_student_id)
    if current_user.role == "student":
        student = StudentMapper.find_by_id(current_user.id)
        return bool(student and student.student_id == display_student_id)
    return False


def can_current_user_edit_student_records(display_student_id):
    if not current_user.is_authenticated:
        return False
    if current_user.role == "mentor":
        return can_mentor_access_student(current_user.id, display_student_id)
    return False


def add_record(display_student_id, date_text, time_text, problem_statement, interview_summary, followup_action):
    if not all(map(_not_blank, [display_student_id, date_text, time_text, problem_statement, interview_summary, followup_action])):
        return False, "All fields are required.", None

    student = get_student_by_student_id(display_student_id)
    if not student:
        return False, "Student not found.", None

    if not can_current_user_edit_student_records(display_student_id):
        return False, "You do not have permission to add records for this student.", None

    mentor = get_current_mentor()
    if current_user.role == "faculty_consultant":
        mentor = student.group.mentor if student.group else None
    if not mentor:
        return False, "Mentor profile not found.", None

    try:
        record_date = _parse_date(date_text)
        record_time = _parse_time(time_text)
    except ValueError:
        return False, "Invalid date or time format.", None

    record = Record(
        record_id=f"R-{uuid.uuid4().hex[:10].upper()}",
        student_id=student.id,
        mentor_id=mentor.id,
        interview_date=record_date,
        interview_time=record_time,
        problem_statement=problem_statement.strip(),
        interview_summary=interview_summary.strip(),
        followup_action=followup_action.strip(),
    )
    RecordMapper.add(record)
    return True, "Record added successfully.", record


def modify_record(record_id, problem_statement, interview_summary, followup_action):
    record = RecordMapper.find_by_record_id(record_id)
    if not record:
        return False, "Record not found."
    if not can_current_user_edit_student_records(record.student.student_id):
        return False, "You do not have permission to modify this record."
    if not all(map(_not_blank, [problem_statement, interview_summary, followup_action])):
        return False, "All fields are required."
    record.problem_statement = problem_statement.strip()
    record.interview_summary = interview_summary.strip()
    record.followup_action = followup_action.strip()
    RecordMapper.update(record)
    return True, "Record updated successfully."


def delete_record(record_id):
    record = RecordMapper.find_by_record_id(record_id)
    if not record:
        return False, "Record not found."
    display_student_id = record.student.student_id
    if not can_current_user_edit_student_records(display_student_id):
        return False, "You do not have permission to delete this record."
    RecordMapper.delete(record)
    return True, "Record deleted successfully."


def search_records(keyword="", academic_year="", mentor_name="", student_name="",
                   academic_year_list=None, department_name=""):
    return RecordMapper.search(
        keyword=keyword, academic_year=academic_year,
        mentor_name=mentor_name, student_name=student_name,
        academic_year_list=academic_year_list, department_name=department_name,
    )
