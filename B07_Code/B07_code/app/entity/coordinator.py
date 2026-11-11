"""Coordinator entity class and CoordinatorInfo import data structure."""

from app.extensions import db
from app.entity.user import FacultyMember


class Coordinator(FacultyMember):
    __tablename__ = "coordinators"

    id = db.Column(db.Integer, db.ForeignKey("faculty_members.id"), primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), unique=True)

    department = db.relationship("Department", backref=db.backref("coordinator", uselist=False))

    __mapper_args__ = {
        "polymorphic_identity": "coordinator",
    }

    def search_mentor(self, keyword):
        from app.mapper.mentor_mapper import MentorMapper
        return MentorMapper.search_by_keyword(keyword)

    def searchMentor(self, keyword):
        return self.search_mentor(keyword)

    def forward_case_to_consultant(self, student_id, description):
        from app.mapper.mentor_mapper import MentorMapper
        return MentorMapper.forward_case_to_consultant(self, student_id, description)

    def forwardCaseToConsultant(self, student_id, description):
        return self.forward_case_to_consultant(student_id, description)


class CoordinatorInfo:
    """Pure data structure for coordinator import."""

    def __init__(self, file_path=None):
        self.file_path = file_path
        self.valid = False
        self._coordinator_list = []

    @property
    def coordinatorList(self):
        return self._coordinator_list

    def validate_info(self):
        self.valid = self.file_path is not None and bool(self.file_path.strip())
        return self.valid

    def validateInfo(self):
        return self.validate_info()

    @staticmethod
    def import_coordinator_info(file_path):
        from app.mapper.student_mapper import CoordinatorInfoImportMapper
        return CoordinatorInfoImportMapper.import_from_excel(file_path)

    @staticmethod
    def importCoordinatorInfo(file_path):
        return CoordinatorInfo.import_coordinator_info(file_path)
