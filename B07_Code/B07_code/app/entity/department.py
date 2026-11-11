"""Department entity class."""

from app.utils.time_utils import local_now

from app.extensions import db


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=local_now)
    updated_at = db.Column(db.DateTime, default=local_now, onupdate=local_now)

    faculty_id = db.Column(db.Integer, db.ForeignKey("faculties.id"), nullable=False)

    majors = db.relationship("Major", backref="department", lazy=True)

    def get_faculty(self):
        from app.entity.faculty import Faculty
        return Faculty.query.get(self.faculty_id)

    def getFaculty(self):
        return self.get_faculty()

    def add_major(self, major):
        if not major:
            return False
        if self.has_major(major.name):
            return False
        major.department_id = self.id
        db.session.add(major)
        db.session.commit()
        return True

    def addMajor(self, major):
        return self.add_major(major)

    def remove_major(self, major_name):
        major = self.get_major(major_name)
        if not major:
            return False
        db.session.delete(major)
        db.session.commit()
        return True

    def removeMajor(self, major_name):
        return self.remove_major(major_name)

    def get_major(self, major_name):
        from app.entity.major import Major
        return Major.query.filter_by(department_id=self.id, name=major_name).first()

    def getMajor(self, major_name):
        return self.get_major(major_name)

    def get_all_majors(self):
        from app.entity.major import Major
        return Major.query.filter_by(department_id=self.id, active=True).all()

    def getAllMajors(self):
        return self.get_all_majors()

    def assign_coordinator(self, coordinator):
        from app.mapper.organization_mapper import DepartmentMapper
        DepartmentMapper.assign_coordinator(self, coordinator)

    def assignCoordinator(self, coordinator):
        return self.assign_coordinator(coordinator)

    def get_coordinator(self):
        from app.entity.coordinator import Coordinator
        return Coordinator.query.filter_by(department_id=self.id).first()

    def getCoordinator(self):
        return self.get_coordinator()

    def has_major(self, major_name):
        return self.get_major(major_name) is not None

    def hasMajor(self, major_name):
        return self.has_major(major_name)
