"""MCPGroup entity class."""

from app.extensions import db


class MCPGroup(db.Model):
    __tablename__ = "mcp_groups"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.String(120), unique=True, nullable=False)
    academic_year = db.Column(db.String(50), nullable=False)

    mentor_id = db.Column(db.Integer, db.ForeignKey("mentors.id"), nullable=False)
    major_id = db.Column(db.Integer, db.ForeignKey("majors.id"))

    mentor = db.relationship("Mentor", backref="groups")
    major = db.relationship("Major", backref="mcp_groups")

    def add_student(self, student_id):
        from app.mapper.mcp_group_mapper import GroupMapper
        return GroupMapper.add_student_to_group(student_id, self)

    def addStudent(self, student_id):
        return self.add_student(student_id)

    def remove_student(self, student_id):
        from app.mapper.mcp_group_mapper import GroupMapper
        return GroupMapper.remove_student_from_group(student_id, self)

    def removeStudent(self, student_id):
        return self.remove_student(student_id)

    def change_mentor(self, mentor_email):
        from app.mapper.mcp_group_mapper import GroupMapper
        return GroupMapper.change_mentor(self, mentor_email)

    def changeMentor(self, mentor_email):
        return self.change_mentor(mentor_email)

    def get_student_list(self):
        return self.students

    def getStudentList(self):
        return self.get_student_list()
