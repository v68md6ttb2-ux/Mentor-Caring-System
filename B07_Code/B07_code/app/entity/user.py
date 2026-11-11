"""User and FacultyMember entity classes."""

import uuid

from flask_login import UserMixin

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), unique=True, nullable=False,
                       default=lambda: f"U-{uuid.uuid4().hex[:10].upper()}")
    account = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    role = db.Column(db.String(50), nullable=False)
    user_type = db.Column(db.String(30), nullable=False, default="user")

    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": user_type,
    }

    def get_role(self):
        return self.role

    def getRole(self):
        return self.get_role()

    def change_password(self, old_password, new_password):
        from app.mapper.user_mapper import UserMapper
        return UserMapper.change_password(self, old_password, new_password)

    def changePassword(self, old_password, new_password):
        return self.change_password(old_password, new_password)


class FacultyMember(User):
    __tablename__ = "faculty_members"

    id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculties.id"))

    faculty = db.relationship("Faculty", backref="members")

    __mapper_args__ = {
        "polymorphic_identity": "faculty_member",
    }

    def search_student(self, student_id):
        from app.mapper.student_mapper import StudentMapper
        return StudentMapper.find_by_student_id(student_id)

    def searchStudent(self, student_id):
        return self.search_student(student_id)
