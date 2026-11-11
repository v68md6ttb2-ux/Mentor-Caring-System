"""Data mappers for Record, WordFile, LogActivity entities and export."""

import os
import uuid
from datetime import timedelta
from app.utils.time_utils import local_now

from app.extensions import db
from app.entity.record import Record, WordFile, LogActivity
from app.entity.student import Student
from app.entity.mentor import Mentor
from app.entity.mcp_group import MCPGroup
from app.entity.major import Major
from app.entity.department import Department


def _not_blank(value):
    return value is not None and str(value).strip() != ""


def _get_student_detail_info(student_id):
    """Traverse ORM relationships to build a student detail info dict."""
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return None
    group = student.group
    mentor = group.mentor if group else None
    major = group.major if group else None
    department = major.department if major else None
    faculty = department.faculty if department else None
    return {
        "student": student, "group": group, "mentor": mentor,
        "major": major, "department": department, "faculty": faculty,
    }


class RecordMapper:
    """Data mapper for Record entity."""

    @staticmethod
    def find_by_record_id(record_id):
        if not _not_blank(record_id):
            return None
        return Record.query.filter_by(record_id=record_id).first()

    @staticmethod
    def find_by_student_id(db_student_id):
        return Record.query.filter_by(student_id=db_student_id).order_by(
            Record.interview_date.desc(), Record.interview_time.desc()
        ).all()

    @staticmethod
    def find_all():
        return Record.query.all()

    @staticmethod
    def find_by_mentor_and_student_ids(mentor_id, student_id_list):
        return Record.query.filter(
            Record.student.has(Student.student_id.in_(student_id_list)),
            Record.mentor_id == mentor_id
        ).all()

    @staticmethod
    def add(record):
        db.session.add(record)
        db.session.commit()
        return True

    @staticmethod
    def update(record):
        record.updated_at = local_now()
        db.session.commit()
        return True

    @staticmethod
    def delete(record):
        db.session.delete(record)
        db.session.commit()
        return True

    @staticmethod
    def search(keyword="", academic_year="", mentor_name="", student_name="",
               academic_year_list=None, department_name=""):
        query = Record.query.join(Record.student).join(Record.mentor)

        if _not_blank(keyword):
            key = f"%{keyword.strip()}%"
            query = query.filter(
                (Student.student_id.like(key)) |
                (Student.name.like(key)) |
                (Mentor.name.like(key)) |
                (Record.problem_statement.like(key)) |
                (Record.interview_summary.like(key))
            )

        if _not_blank(mentor_name):
            query = query.filter(Mentor.name.like(f"%{mentor_name.strip()}%"))
        if _not_blank(student_name):
            query = query.filter(Student.name.like(f"%{student_name.strip()}%"))

        if _not_blank(department_name):
            query = query.join(Student.group).join(MCPGroup.major).join(Major.department).filter(
                Department.name.like(f"%{department_name.strip()}%")
            )

        years = RecordMapper._normalize_year_list(academic_year_list, academic_year)
        if years:
            query = query.filter(Student.group.has(MCPGroup.academic_year.in_(years)))

        return query.order_by(Record.interview_date.desc(), Record.interview_time.desc()).all()

    @staticmethod
    def _normalize_year_list(academic_year_list=None, academic_year=None):
        source = academic_year_list if academic_year_list is not None else academic_year
        if source is None:
            return []
        if isinstance(source, str):
            candidates = [source]
        else:
            candidates = list(source)
        return list(dict.fromkeys(str(year).strip() for year in candidates if str(year).strip()))


class WordFileMapper:
    """Data mapper for WordFile entity."""

    @staticmethod
    def find_all_ordered():
        return WordFile.query.order_by(WordFile.created_at.desc()).all()

    @staticmethod
    def find_by_id(file_id):
        return WordFile.query.get_or_404(file_id)

    @staticmethod
    def create(file_id, file_path, records, conditions=None):
        word_file = WordFile(file_id=file_id, file_path=file_path)
        word_file.records = list(records)
        if conditions:
            academic_years = conditions.get("Academic Year List", conditions.get("Academic Year"))
            if academic_years:
                if isinstance(academic_years, list):
                    word_file.set_export_condition(academic_year_list=academic_years)
                else:
                    word_file.set_export_condition(academic_year_list=[academic_years])
        db.session.add(word_file)
        db.session.commit()
        return word_file


class LogMapper:
    """Data mapper for LogActivity entity."""

    @staticmethod
    def find_all_ordered():
        return LogActivity.query.order_by(LogActivity.created_at.desc()).all()

    @staticmethod
    def find_by_student_id(db_student_id):
        return LogActivity.query.filter_by(student_id=db_student_id).order_by(
            LogActivity.created_at.desc()
        ).all()

    @staticmethod
    def find_by_faculty(faculty_id):
        return LogActivity.query.join(LogActivity.student).join(Student.group).join(
            MCPGroup.major
        ).join(Major.department).filter(
            Department.faculty_id == faculty_id
        ).order_by(LogActivity.created_at.desc()).all()

    @staticmethod
    def find_by_mentor_students(mentor):
        student_ids = [s.id for group in mentor.groups for s in group.students]
        if not student_ids:
            return []
        return LogActivity.query.filter(
            LogActivity.student_id.in_(student_ids)
        ).order_by(LogActivity.created_at.desc()).all()

    @staticmethod
    def add(log_entry):
        if not log_entry.log_id or not str(log_entry.log_id).strip():
            return False
        if not log_entry.student_id:
            return False
        if not log_entry.function_access or not str(log_entry.function_access).strip():
            return False
        if not log_entry.login_time or not log_entry.logout_time:
            return False
        if log_entry.logout_time < log_entry.login_time:
            return False
        db.session.add(log_entry)
        db.session.commit()
        return True

    @staticmethod
    def create_activity(student, function_access, login_time=None, logout_time=None):
        login_time = login_time or local_now()
        logout_time = logout_time or local_now()
        if logout_time < login_time:
            logout_time = login_time + timedelta(seconds=1)
        log = LogActivity(
            log_id=f"L-{uuid.uuid4().hex[:10].upper()}",
            student_id=student.id,
            login_time=login_time,
            logout_time=logout_time,
            function_access=function_access,
        )
        return LogMapper.add(log), log

    @staticmethod
    def create_demo(student, function_access):
        # Demo logs are manually created from the log page. Give them a short
        # realistic session duration instead of identical login/logout times.
        now = local_now()
        return LogMapper.create_activity(
            student=student,
            function_access=function_access,
            login_time=now - timedelta(minutes=5),
            logout_time=now,
        )

    @staticmethod
    def update_logout_time_by_log_ids(log_ids, logout_time):
        if not log_ids:
            return 0
        rows = LogActivity.query.filter(LogActivity.log_id.in_(log_ids)).all()
        updated = 0
        for row in rows:
            if row.login_time and logout_time < row.login_time:
                row.logout_time = row.login_time + timedelta(seconds=1)
            else:
                row.logout_time = logout_time
            updated += 1
        if updated:
            db.session.commit()
        return updated


class RecordExportMapper:
    """Data mapper for record export operations."""

    @staticmethod
    def get_export_conditions():
        """Return selectable export filters even before any interview records exist.

        The export page is used in the checklist with academic year + department
        filters. The original implementation only looked at existing interview
        records, so a fresh seeded database displayed empty drop-downs because
        seed_data.py creates groups/students but no records. Pull the selectable
        values from the organization/allocation tables instead, while still
        including any values that may only exist on records.
        """
        records = Record.query.all()

        years = {
            group.academic_year
            for group in MCPGroup.query.all()
            if _not_blank(group.academic_year)
        }
        years.update(
            r.student.group.academic_year
            for r in records
            if r.student and r.student.group and _not_blank(r.student.group.academic_year)
        )

        mentors = {
            mentor.name
            for mentor in Mentor.query.all()
            if _not_blank(mentor.name)
        }
        mentors.update(
            r.mentor.name
            for r in records
            if r.mentor and _not_blank(r.mentor.name)
        )

        students = {
            student.name
            for student in Student.query.all()
            if _not_blank(student.name)
        }
        students.update(
            r.student.name
            for r in records
            if r.student and _not_blank(r.student.name)
        )

        departments = {
            department.name
            for department in Department.query.all()
            if _not_blank(department.name)
        }
        departments.update(
            r.student.group.major.department.name for r in records
            if r.student and r.student.group and r.student.group.major
            and r.student.group.major.department and _not_blank(r.student.group.major.department.name)
        )

        return sorted(years), sorted(mentors), sorted(students), sorted(departments)

    @staticmethod
    def export_to_docx(records, export_dir="exports", conditions=None):
        if not records:
            return False, "No records to export.", None

        os.makedirs(export_dir, exist_ok=True)
        file_id = f"WF-{uuid.uuid4().hex[:10].upper()}"
        filename = f"{file_id}_RecordSub_Export.docx"
        file_path = os.path.join(export_dir, filename)

        try:
            from docx import Document
            document = Document()
            document.add_heading("Mentor Caring System - Interview Records", level=1)

            if conditions:
                document.add_heading("Export Conditions", level=2)
                for key, value in conditions.items():
                    if isinstance(value, list):
                        display_value = ", ".join(value)
                    else:
                        display_value = value
                    if _not_blank(display_value):
                        document.add_paragraph(f"{key}: {display_value}")

            document.add_heading("Records", level=2)
            for index, record in enumerate(records, start=1):
                info = _get_student_detail_info(record.student.student_id)
                document.add_heading(f"Record {index}: {record.record_id}", level=3)
                document.add_paragraph(f"Student ID: {record.student.student_id}")
                document.add_paragraph(f"Student Name: {record.student.name}")
                document.add_paragraph(f"Mentor: {record.mentor.name}")
                document.add_paragraph(f"Date/Time: {record.interview_date} {record.interview_time}")
                document.add_paragraph(f"Faculty: {info['faculty'].name if info and info['faculty'] else 'N/A'}")
                document.add_paragraph(f"Department: {info['department'].name if info and info['department'] else 'N/A'}")
                document.add_paragraph(f"Major: {info['major'].name if info and info['major'] else 'N/A'}")
                document.add_paragraph(f"Problem Statement: {record.problem_statement}")
                document.add_paragraph(f"Interview Summary: {record.interview_summary}")
                document.add_paragraph(f"Follow-up Action: {record.followup_action}")
                document.add_paragraph("")

            document.save(file_path)
            content_summary = f"Exported {len(records)} interview record(s)."
        except Exception:
            file_path = os.path.join(export_dir, filename.replace(".docx", ".txt"))
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("Mentor Caring System - Interview Records\n")
                for record in records:
                    f.write(f"\n{record.record_id} | {record.student.student_id} | {record.student.name}\n")
                    f.write(f"Mentor: {record.mentor.name}\n")
                    f.write(f"Problem: {record.problem_statement}\n")
                    f.write(f"Summary: {record.interview_summary}\n")
                    f.write(f"Follow-up: {record.followup_action}\n")
            content_summary = f"Exported {len(records)} interview record(s) as text fallback."

        word_file = WordFileMapper.create(file_id, file_path, records, conditions)
        return True, content_summary, word_file
