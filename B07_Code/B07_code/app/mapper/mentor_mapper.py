"""Data mappers for Mentor, Coordinator, and FacultyConsultant entities."""

from app.extensions import db
from app.entity.mentor import Mentor
from app.entity.coordinator import Coordinator
from app.entity.faculty_consultant import FacultyConsultant
from app.entity.student import Student
from app.entity.mcp_group import MCPGroup
from app.entity.message import Message


class MentorMapper:
    """Data mapper for Mentor entity."""

    @staticmethod
    def find_by_id(mentor_id):
        return Mentor.query.get(mentor_id)

    @staticmethod
    def find_by_email(email):
        if not email or not email.strip():
            return None
        return Mentor.query.filter_by(email=email.strip()).first()

    @staticmethod
    def find_all():
        return Mentor.query.all()

    @staticmethod
    def search_by_keyword(keyword):
        keyword = keyword.strip() if keyword else ""
        if not keyword:
            return []
        mentors = Mentor.query.filter(
            (Mentor.name.contains(keyword)) | (Mentor.email.contains(keyword))
        ).all()
        result = []
        seen = set()
        for m in mentors:
            if m.id not in seen:
                result.append(m)
                seen.add(m.id)
        return result

    @staticmethod
    def search_with_groups(keyword):
        keyword = keyword.strip() if keyword else ""
        if not keyword:
            return None
        return Mentor.query.outerjoin(Mentor.groups).filter(
            db.or_(
                Mentor.name.contains(keyword),
                Mentor.email.contains(keyword),
                MCPGroup.group_id == keyword
            )
        ).first()

    @staticmethod
    def forward_case(mentor, student_id, description):
        student = Student.query.filter_by(student_id=student_id).first()
        if not student:
            return False
        if not student.group or student.group.mentor_id != mentor.id:
            return False
        coordinator = None
        if student.group and student.group.major and student.group.major.department:
            coordinator = Coordinator.query.filter_by(
                department_id=student.group.major.department_id
            ).first()
        if not coordinator:
            return False
        content = f"[Forwarded Case] Student: {student.student_id} {student.name}\n{description}"
        msg = Message(content=content, sender_id=mentor.id)
        msg.send(mentor.id, [coordinator.id])
        return True


class CoordinatorMapper:
    """Data mapper for Coordinator entity."""

    @staticmethod
    def find_by_id(coordinator_id):
        return Coordinator.query.get(coordinator_id)

    @staticmethod
    def find_by_name(name):
        return Coordinator.query.filter_by(name=name.strip()).first()

    @staticmethod
    def find_by_department_id(department_id):
        return Coordinator.query.filter_by(department_id=department_id).first()

    @staticmethod
    def find_by_email(email):
        return Coordinator.query.filter_by(email=email).first()

    @staticmethod
    def clear_department(department_id):
        old = Coordinator.query.filter_by(department_id=department_id).first()
        if old:
            old.department_id = None

    @staticmethod
    def forward_case_to_consultant(coordinator, student_id, description):
        student = Student.query.filter_by(student_id=student_id).first()
        if not student:
            return False
        consultant = None
        if student.group and student.group.major and student.group.major.department:
            dept = student.group.major.department
            if dept.faculty:
                consultant = FacultyConsultant.query.filter_by(
                    faculty_id=dept.faculty_id
                ).first()
        if not consultant:
            return False
        content = f"[Escalated Case] Student: {student.student_id} {student.name}\n{description}"
        msg = Message(content=content, sender_id=coordinator.id)
        msg.send(coordinator.id, [consultant.id])
        return True

    @staticmethod
    def find_coordinator_by_name(name):
        """Alias for find_by_name used by FacultyConsultant entity."""
        return CoordinatorMapper.find_by_name(name)


class FacultyConsultantMapper:
    """Data mapper for FacultyConsultant entity."""

    @staticmethod
    def find_by_id(fc_id):
        return FacultyConsultant.query.get(fc_id)

    @staticmethod
    def find_by_faculty_id(faculty_id):
        return FacultyConsultant.query.filter_by(faculty_id=faculty_id).first()

    @staticmethod
    def find_all():
        return FacultyConsultant.query.order_by(FacultyConsultant.name).all()

    @staticmethod
    def get_assigned_faculty_ids():
        return {
            fc.faculty_id for fc in FacultyConsultant.query.filter(
                FacultyConsultant.faculty_id.isnot(None)
            ).all()
        }

    @staticmethod
    def clear_faculty(faculty_id, exclude_id=None):
        old = FacultyConsultant.query.filter_by(faculty_id=faculty_id).first()
        if old and (exclude_id is None or old.id != exclude_id):
            old.faculty_id = None

    @staticmethod
    def assign_to_faculty(consultant, faculty):
        if not consultant or not faculty:
            return
        FacultyConsultantMapper.clear_faculty(faculty.id, exclude_id=consultant.id)
        consultant.faculty_id = faculty.id
        db.session.commit()

    @staticmethod
    def create_consultant(account, password, name, email, faculty_id=None):
        from app.mapper.organization_mapper import FacultyMapper
        consultant = FacultyConsultant(
            account=account, password=password, name=name, email=email,
            role="faculty_consultant",
        )
        db.session.add(consultant)
        db.session.flush()
        if faculty_id:
            faculty = FacultyMapper.find_by_id(faculty_id)
            if faculty:
                FacultyConsultantMapper.clear_faculty(faculty.id)
                consultant.faculty_id = faculty.id
        db.session.commit()
        return consultant

    @staticmethod
    def reassign_consultant(consultant, faculty_id):
        from app.mapper.organization_mapper import FacultyMapper
        faculty = FacultyMapper.find_by_id(faculty_id) if faculty_id else None
        if faculty:
            FacultyConsultantMapper.clear_faculty(faculty.id, exclude_id=consultant.id)
            consultant.faculty_id = faculty.id
        else:
            consultant.faculty_id = None
        db.session.commit()

    @staticmethod
    def delete_consultant_by_id(consultant):
        db.session.delete(consultant)
        db.session.commit()
