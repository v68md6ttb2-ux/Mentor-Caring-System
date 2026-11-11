"""Authentication and user session control logic."""

from flask_login import current_user

from app.mapper.user_mapper import UserMapper, StudentMapper
from app.mapper.mentor_mapper import MentorMapper, CoordinatorMapper, FacultyConsultantMapper


def get_current_student():
    return StudentMapper.find_by_id(current_user.id)


def get_student_by_user_db_id(user_id):
    return StudentMapper.find_by_id(user_id)


def get_current_mentor():
    return MentorMapper.find_by_id(current_user.id)


def get_current_faculty_consultant():
    return FacultyConsultantMapper.find_by_id(current_user.id)


def get_current_coordinator():
    return CoordinatorMapper.find_by_id(current_user.id)


def get_current_faculty_member():
    from app.mapper.user_mapper import FacultyMemberMapper
    return FacultyMemberMapper.find_by_id(current_user.id)


def get_user_by_id(user_id):
    return UserMapper.find_by_id(user_id)


def get_user_by_account(account):
    return UserMapper.find_by_account(account)


def is_role(user, role):
    return user and user.role == role


def is_any_role(user, roles):
    return user and user.role in roles


def change_password(user, old_password, new_password):
    return UserMapper.change_password(user, old_password, new_password)
