"""Data mapper for MCPGroup entity."""

from app.extensions import db
from app.entity.mcp_group import MCPGroup
from app.entity.student import Student
from app.entity.mentor import Mentor


class GroupMapper:
    """Data mapper for MCPGroup entity."""

    @staticmethod
    def find_by_id(group_id):
        return MCPGroup.query.get(group_id)

    @staticmethod
    def find_by_display_id(display_group_id):
        if not display_group_id or not display_group_id.strip():
            return None
        return MCPGroup.query.filter_by(group_id=display_group_id.strip()).first()

    @staticmethod
    def find_all():
        return MCPGroup.query.all()

    @staticmethod
    def find_by_major(major_id):
        return MCPGroup.query.filter_by(major_id=major_id).all()

    @staticmethod
    def find_by_academic_years(years):
        return MCPGroup.query.filter(MCPGroup.academic_year.in_(years)).all()

    @staticmethod
    def add_student_to_group(student_id, group):
        student = Student.query.filter_by(student_id=student_id).first()
        if not student:
            return False
        student.group_id = group.id
        db.session.commit()
        return True

    @staticmethod
    def remove_student_from_group(student_id, group):
        student = Student.query.filter_by(student_id=student_id, group_id=group.id).first()
        if not student:
            return False
        student.group_id = None
        db.session.commit()
        return True

    @staticmethod
    def change_mentor(group, mentor_email):
        mentor = Mentor.query.filter_by(email=mentor_email).first()
        if not mentor:
            return False
        group.mentor_id = mentor.id
        db.session.commit()
        return True

    @staticmethod
    def change_mentor_by_display_id(group_id, mentor_email):
        group = GroupMapper.find_by_display_id(group_id)
        if not group:
            return False
        return GroupMapper.change_mentor(group, mentor_email)

    @staticmethod
    def remove_student_anywhere(student_id):
        student = Student.query.filter_by(student_id=student_id).first()
        if not student or not student.group_id:
            return False
        student.group_id = None
        db.session.commit()
        return True

    @staticmethod
    def search_by_keyword(keyword):
        return MCPGroup.query.filter(MCPGroup.group_id.contains(keyword)).all()

    @staticmethod
    def commit():
        db.session.commit()
