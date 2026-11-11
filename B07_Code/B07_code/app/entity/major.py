"""Major entity class."""

from app.utils.time_utils import local_now

from app.extensions import db


class Major(db.Model):
    __tablename__ = "majors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=local_now)
    updated_at = db.Column(db.DateTime, default=local_now, onupdate=local_now)

    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)

    def get_department(self):
        from app.entity.department import Department
        return Department.query.get(self.department_id)

    def getDepartment(self):
        return self.get_department()

    def add_mentor(self, mentor):
        if not mentor:
            return False
        from app.entity.mcp_group import MCPGroup
        groups = MCPGroup.query.filter_by(major_id=self.id).all()
        for group in groups:
            if group.mentor_id == mentor.id:
                return False
        return True

    def addMentor(self, mentor):
        return self.add_mentor(mentor)

    def get_mentor(self, mentor_id):
        from app.entity.mcp_group import MCPGroup
        from app.entity.mentor import Mentor
        groups = MCPGroup.query.filter_by(major_id=self.id).all()
        for group in groups:
            if group.mentor_id == int(mentor_id):
                return Mentor.query.get(mentor_id)
        return None

    def getMentor(self, mentor_id):
        return self.get_mentor(mentor_id)

    def remove_mentor(self, mentor_id):
        from app.entity.mcp_group import MCPGroup
        groups = MCPGroup.query.filter_by(major_id=self.id, mentor_id=int(mentor_id)).all()
        if not groups:
            return False
        for group in groups:
            group.mentor_id = None
        db.session.commit()
        return True

    def removeMentor(self, mentor_id):
        return self.remove_mentor(mentor_id)

    def get_all_mentors(self):
        from app.entity.mcp_group import MCPGroup
        from app.entity.mentor import Mentor
        groups = MCPGroup.query.filter_by(major_id=self.id).all()
        mentor_ids = list(set(g.mentor_id for g in groups if g.mentor_id))
        return Mentor.query.filter(Mentor.id.in_(mentor_ids)).all() if mentor_ids else []

    def getAllMentors(self):
        return self.get_all_mentors()

    def add_group(self, group):
        if not group:
            return False
        group.major_id = self.id
        db.session.commit()
        return True

    def addGroup(self, group):
        return self.add_group(group)

    def remove_group(self, group_id):
        from app.entity.mcp_group import MCPGroup
        group = MCPGroup.query.get(group_id)
        if not group or group.major_id != self.id:
            return False
        group.major_id = None
        db.session.commit()
        return True

    def removeGroup(self, group_id):
        return self.remove_group(group_id)

    def get_group(self, group_id):
        from app.entity.mcp_group import MCPGroup
        return MCPGroup.query.filter_by(id=group_id, major_id=self.id).first()

    def getGroup(self, group_id):
        return self.get_group(group_id)

    def get_all_groups(self):
        from app.entity.mcp_group import MCPGroup
        return MCPGroup.query.filter_by(major_id=self.id).all()

    def getAllGroups(self):
        return self.get_all_groups()

    @property
    def mentorList(self):
        return self.get_all_mentors()

    @property
    def groupList(self):
        return self.get_all_groups()
