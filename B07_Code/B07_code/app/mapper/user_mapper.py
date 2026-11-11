"""Data mappers for User and basic Student queries."""

from app.extensions import db
from app.entity.user import User
from app.entity.student import Student


class UserMapper:
    """Data mapper for User entity."""

    @staticmethod
    def find_by_account(account):
        return User.query.filter_by(account=account).first()

    @staticmethod
    def find_by_id(user_id):
        return User.query.get(int(user_id))

    @staticmethod
    def find_by_ids(user_ids):
        return User.query.filter(User.id.in_(user_ids)).all()

    @staticmethod
    def find_all_except(user_id):
        return User.query.filter(User.id != user_id).all()

    @staticmethod
    def find_by_roles(roles, exclude_id=None):
        q = User.query.filter(User.role.in_(roles))
        if exclude_id:
            q = q.filter(User.id != exclude_id)
        return q.all()

    @staticmethod
    def find_by_account_or_email(account, email):
        return User.query.filter(
            (User.account == account) | (User.email == email)
        ).first()

    @staticmethod
    def change_password(user, old_password, new_password):
        if not old_password or not new_password:
            return False
        if user.password != old_password:
            return False
        if len(new_password) < 6:
            return False
        user.password = new_password
        db.session.commit()
        return True

    @staticmethod
    def login(account, password):
        if not account or not password:
            return None
        user = User.query.filter_by(account=account).first()
        if not user or user.password != password:
            return None
        return user

    @staticmethod
    def add(user):
        db.session.add(user)
        db.session.commit()

    @staticmethod
    def delete(user):
        db.session.delete(user)
        db.session.commit()

    @staticmethod
    def flush():
        db.session.flush()


class StudentMapper:
    """Data mapper for Student entity — basic queries."""

    @staticmethod
    def find_by_id(user_id):
        return Student.query.get(user_id)

    @staticmethod
    def find_by_student_id(student_id):
        return Student.query.filter_by(student_id=student_id).first()

    @staticmethod
    def find_all():
        return Student.query.all()

    @staticmethod
    def is_in_group(student):
        return student.group_id is not None


class FacultyMemberMapper:
    """Data mapper for FacultyMember — base class for mentor/coordinator/FC/faculty_member."""

    @staticmethod
    def find_by_id(user_id):
        from app.entity.user import FacultyMember
        return FacultyMember.query.get(user_id)
