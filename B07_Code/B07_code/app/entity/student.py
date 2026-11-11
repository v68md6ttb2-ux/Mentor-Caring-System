"""Student entity and MCPInfo import data structure."""

import uuid

from app.extensions import db
from app.entity.user import User


class Student(User):
    __tablename__ = "students"

    id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(50), default="Normal")
    group_id = db.Column(db.Integer, db.ForeignKey("mcp_groups.id"))

    group_id_str = db.Column(db.String(120))
    mentor_name_str = db.Column(db.String(120))
    faculty_str = db.Column(db.String(120))
    department_str = db.Column(db.String(120))
    major_str = db.Column(db.String(120))

    group = db.relationship("MCPGroup", backref="students")

    __mapper_args__ = {
        "polymorphic_identity": "student",
    }

    def is_in_group(self):
        return self.group_id is not None

    def isInGroup(self):
        return self.is_in_group()

    def check_mentor_info(self):
        if not self.group:
            return None
        return self.group.mentor

    def checkMentorInfo(self):
        return self.check_mentor_info()


class MCPInfo:
    """Pure data structure for MCP allocation import."""

    def __init__(self, file_path=None):
        self.file_path = file_path
        self.valid = False
        self._map_info_list = []

    @property
    def mapInfoList(self):
        return self._map_info_list

    def validate_info(self):
        self.valid = self.file_path is not None and bool(self.file_path.strip())
        return self.valid

    def validateInfo(self):
        return self.validate_info()

    @staticmethod
    def import_mcp_info(file_path):
        from app.mapper.student_mapper import MCPInfoImportMapper
        return MCPInfoImportMapper.import_from_excel(file_path)

    @staticmethod
    def importMCPInfo(file_path):
        return MCPInfo.import_mcp_info(file_path)
