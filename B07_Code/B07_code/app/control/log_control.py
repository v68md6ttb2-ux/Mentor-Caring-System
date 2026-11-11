"""Log activity control logic."""

from datetime import datetime, timedelta

from flask import session

from app.mapper.record_mapper import LogMapper
from app.mapper.user_mapper import StudentMapper
from app.control.mentor_allocation_control import get_student_by_student_id
from app.utils.time_utils import local_now, local_now_iso


def _parse_session_login_time():
    """Return the current student's login time stored in Flask session."""
    raw_value = session.get("student_login_time")
    if not raw_value:
        return None
    try:
        return datetime.fromisoformat(raw_value)
    except (TypeError, ValueError):
        return None


def add_demo_log(display_student_id, function_access):
    student = get_student_by_student_id(display_student_id)
    if not student:
        return False, "Student not found."
    success, _ = LogMapper.create_demo(student, function_access)
    if success:
        return True, "Log activity added successfully."
    return False, "Failed to add log activity."


def get_logs_by_faculty(faculty_id):
    return LogMapper.find_by_faculty(faculty_id)


def get_logs_by_mentor(mentor):
    return LogMapper.find_by_mentor_students(mentor) if mentor else []


def get_all_logs():
    return LogMapper.find_all_ordered()


def add_student_activity_log(function_access):
    """Create a log entry for the currently logged-in student.

    The old implementation used one timestamp for both login_time and
    logout_time, so the activity log showed identical Login/Logout values.
    Now every student activity uses the real session login time and a current
    timestamp. When the student logs out, all logs in the same session are
    updated to the actual logout time.
    """
    try:
        from flask_login import current_user

        if not getattr(current_user, "is_authenticated", False):
            return False, "Current user is not authenticated."
        if getattr(current_user, "role", None) != "student":
            return False, "Current user is not a student."

        student = StudentMapper.find_by_id(current_user.id)
        if not student:
            return False, "Student profile not found."

        login_time = _parse_session_login_time()
        if login_time is None:
            login_time = local_now()
            session["student_login_time"] = local_now_iso()
            session["student_session_log_ids"] = []
            session.modified = True

        logout_time = local_now()
        if logout_time < login_time:
            logout_time = login_time + timedelta(seconds=1)

        success, log = LogMapper.create_activity(
            student=student,
            function_access=function_access or "Access student page",
            login_time=login_time,
            logout_time=logout_time,
        )
        if success:
            log_ids = session.get("student_session_log_ids", [])
            if log.log_id not in log_ids:
                log_ids.append(log.log_id)
            session["student_session_log_ids"] = log_ids
            session.modified = True
            return True, "Log activity added successfully."
        return False, "Failed to add log activity."
    except Exception as exc:
        # Do not let logging failure break the page the student is visiting.
        return False, f"Failed to add log activity: {exc}"


def close_student_activity_session(add_logout_log=True):
    """Finalize the current student's activity logs with the real logout time."""
    try:
        from flask_login import current_user

        if not getattr(current_user, "is_authenticated", False):
            return False, "Current user is not authenticated."
        if getattr(current_user, "role", None) != "student":
            return False, "Current user is not a student."

        student = StudentMapper.find_by_id(current_user.id)
        if not student:
            return False, "Student profile not found."

        login_time = _parse_session_login_time() or local_now()
        logout_time = local_now()
        if logout_time < login_time:
            logout_time = login_time + timedelta(seconds=1)

        log_ids = list(session.get("student_session_log_ids", []))

        if add_logout_log:
            success, log = LogMapper.create_activity(
                student=student,
                function_access="Logout",
                login_time=login_time,
                logout_time=logout_time,
            )
            if success and log.log_id not in log_ids:
                log_ids.append(log.log_id)

        if log_ids:
            LogMapper.update_logout_time_by_log_ids(log_ids, logout_time)

        session.pop("student_login_time", None)
        session.pop("student_session_log_ids", None)
        session.modified = True
        return True, "Student activity session closed."
    except Exception as exc:
        return False, f"Failed to close student activity session: {exc}"
