"""Data mappers for student-specific operations and Excel imports."""

import uuid

from app.extensions import db
from app.entity.student import Student
from app.entity.mcp_group import MCPGroup
from app.entity.major import Major
from app.entity.mentor import Mentor
from app.entity.department import Department
from app.entity.coordinator import Coordinator


class MCPInfoImportMapper:
    """Data mapper for importing MCP allocation from Excel (Appendix B)."""

    @staticmethod
    def import_from_excel(file_path):
        import os
        if not file_path or not os.path.exists(file_path):
            return False
        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path)
            ws = wb.active
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or len(row) < 3:
                    continue
                student_id_str = str(row[0]).strip() if row[0] else None
                student_name = str(row[1]).strip() if row[1] else None
                major_name = str(row[2]).strip() if len(row) > 2 and row[2] else None
                status = str(row[3]).strip() if len(row) > 3 and row[3] else "Normal"
                group_id_str = str(row[4]).strip() if len(row) > 4 and row[4] else None
                mentor_name = str(row[5]).strip() if len(row) > 5 and row[5] else None
                office = str(row[6]).strip() if len(row) > 6 and row[6] else None
                mentor_email = str(row[7]).strip() if len(row) > 7 and row[7] else None

                if not student_id_str or not student_name:
                    continue

                student = Student.query.filter_by(student_id=student_id_str).first()
                if not student:
                    email = f"{student_id_str}@bnbu.edu.cn"
                    student = Student(
                        account=student_id_str,
                        password="123456",
                        name=student_name,
                        email=email,
                        role="student",
                        student_id=student_id_str,
                    )
                    db.session.add(student)
                    db.session.flush()
                student.status = status if status else student.status

                group = None
                if group_id_str:
                    group = MCPGroup.query.filter_by(group_id=group_id_str).first()
                    if not group:
                        parts = group_id_str.split("-")
                        academic_year = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else group_id_str
                        group = MCPGroup(
                            group_id=group_id_str,
                            academic_year=academic_year,
                            mentor_id=None,
                            major_id=None,
                        )
                        db.session.add(group)
                        db.session.flush()

                if major_name and group:
                    major = Major.query.filter_by(name=major_name).first()
                    if major:
                        group.major_id = major.id

                if mentor_name and mentor_email:
                    mentor = Mentor.query.filter_by(email=mentor_email).first()
                    if not mentor:
                        mentor = Mentor(
                            account=mentor_email.split("@")[0] if "@" in mentor_email else mentor_email,
                            password="123456",
                            name=mentor_name,
                            email=mentor_email,
                            role="mentor",
                            mentor_id=f"M-{uuid.uuid4().hex[:8].upper()}",
                            office=office or "",
                        )
                        db.session.add(mentor)
                        db.session.flush()
                    elif office:
                        mentor.office = office
                    if group:
                        group.mentor_id = mentor.id

                if group:
                    student.group_id = group.id

            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False


class CoordinatorInfoImportMapper:
    """Data mapper for importing coordinators from Excel (Appendix C)."""

    @staticmethod
    def import_from_excel(file_path):
        import os
        if not file_path or not os.path.exists(file_path):
            return False
        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path)
            ws = wb.active
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or len(row) < 4:
                    continue
                name = str(row[0]).strip() if row[0] else None
                email = str(row[1]).strip() if row[1] else None
                department_name = str(row[2]).strip() if row[2] else None
                account = str(row[3]).strip() if row[3] else name
                if not name or not email:
                    continue
                existing = Coordinator.query.filter_by(email=email).first()
                if existing:
                    continue
                c = Coordinator(
                    account=account,
                    password="123456",
                    name=name,
                    email=email,
                    role="coordinator",
                )
                if department_name:
                    dept = Department.query.filter_by(name=department_name).first()
                    if dept:
                        c.department_id = dept.id
                db.session.add(c)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
