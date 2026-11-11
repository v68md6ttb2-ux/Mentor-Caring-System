"""Mentor allocation, group/student management control logic."""

from flask_login import current_user

from app.mapper.user_mapper import UserMapper, StudentMapper
from app.mapper.mentor_mapper import MentorMapper, FacultyConsultantMapper
from app.mapper.mcp_group_mapper import GroupMapper
from app.mapper.organization_mapper import FacultyMapper


# ── Student / Group queries ───────────────────────────────────────────

def get_student_mentor_info():
    student = StudentMapper.find_by_id(current_user.id)
    if not student:
        return None
    if not student.group:
        return {
            "student": student, "group": None, "mentor": None,
            "major": None, "department": None, "faculty": None,
        }
    group = student.group
    mentor = group.mentor
    major = group.major
    department = major.department if major else None
    faculty = department.faculty if department else None
    return {
        "student": student, "group": group, "mentor": mentor,
        "major": major, "department": department, "faculty": faculty,
    }


def get_student_by_student_id(student_id):
    student_id = student_id.strip() if student_id else ""
    if not student_id:
        return None
    return StudentMapper.find_by_student_id(student_id)


def get_student_detail_info(student_id):
    student = get_student_by_student_id(student_id)
    if not student:
        return None
    group = student.group
    mentor = group.mentor if group else None
    major = group.major if group else None
    department = major.department if major else None
    faculty = department.faculty if department else None
    return {
        "student": student, "group": group, "mentor": mentor,
        "major": major, "department": department, "faculty": faculty,
    }


def get_all_students():
    return StudentMapper.find_all()


def get_students_by_group_id(group_id):
    group = GroupMapper.find_by_display_id(group_id)
    if not group:
        return []
    return group.students


# ── MCP Group management ──────────────────────────────────────────────

def get_all_mcp_groups():
    return GroupMapper.find_all()


def get_group_by_display_group_id(group_id):
    return GroupMapper.find_by_display_id(group_id)


def change_group_mentor(group_id, mentor_id):
    if not group_id:
        return False, "Group ID is required."
    if not mentor_id:
        return False, "Mentor is required."
    group = GroupMapper.find_by_id(group_id)
    if not group:
        return False, "MCP group not found."
    mentor = MentorMapper.find_by_id(mentor_id)
    if not mentor:
        return False, "Mentor not found."
    group.mentor_id = mentor.id
    GroupMapper.commit()
    return True, "Group mentor changed successfully."


def add_student_to_group(student_id, group_id):
    student_id = student_id.strip()
    if not student_id:
        return False, "Student ID is required."
    if not group_id:
        return False, "MCP group is required."
    group = GroupMapper.find_by_id(group_id)
    if not group:
        return False, "MCP group not found."
    student = StudentMapper.find_by_student_id(student_id)
    if not student:
        return False, "Student not found."
    student.group_id = group.id
    GroupMapper.commit()
    return True, "Student added to group successfully."


def remove_student_from_group(student_id):
    student_id = student_id.strip()
    if not student_id:
        return False, "Student ID is required."
    if not GroupMapper.remove_student_anywhere(student_id):
        return False, "Student not found or not in any group."
    return True, "Student removed from group successfully. Student record is kept."


# ── Mentor queries ────────────────────────────────────────────────────

def get_all_mentors():
    return MentorMapper.find_all()


def get_mentor_by_email(email):
    return MentorMapper.find_by_email(email)


def can_mentor_access_student(mentor_user_id, student_id):
    mentor = MentorMapper.find_by_id(mentor_user_id)
    student = StudentMapper.find_by_student_id(student_id)
    if not mentor or not student or not student.group:
        return False
    return student.group.mentor_id == mentor.id


def search_mentor_info(keyword):
    keyword = keyword.strip() if keyword else ""
    if not keyword:
        return []
    groups_by_group_id = GroupMapper.search_by_keyword(keyword)
    mentors = MentorMapper.search_by_keyword(keyword)
    groups_by_mentor = []
    for mentor in mentors:
        groups_by_mentor.extend(mentor.groups)
    result = []
    seen_group_ids = set()
    for group in groups_by_group_id + groups_by_mentor:
        if group.id not in seen_group_ids:
            result.append(group)
            seen_group_ids.add(group.id)
    return result


# ── Faculty Consultant management ─────────────────────────────────────

def get_all_faculty_consultants():
    return FacultyConsultantMapper.find_all()


def get_faculties_without_consultant():
    return FacultyMapper.find_without_consultant()


def add_faculty_consultant(account, password, name, email, faculty_id):
    account = account.strip() if account else ""
    password = password.strip() if password else ""
    name = name.strip() if name else ""
    email = email.strip() if email else ""
    faculty_id = faculty_id.strip() if isinstance(faculty_id, str) else faculty_id

    if not all([account, password, name, email]):
        return False, "All fields are required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    existing = UserMapper.find_by_account_or_email(account, email)
    if existing:
        return False, "Account or email already exists."

    if faculty_id:
        faculty = FacultyMapper.find_by_id(faculty_id)
        if not faculty:
            return False, "Faculty not found."

    FacultyConsultantMapper.create_consultant(account, password, name, email, faculty_id)
    return True, "Faculty consultant added successfully."


def change_faculty_consultant(consultant_id, faculty_id):
    consultant = FacultyConsultantMapper.find_by_id(consultant_id)
    if not consultant:
        return False, "Faculty consultant not found."

    if faculty_id:
        faculty = FacultyMapper.find_by_id(faculty_id)
        if not faculty:
            return False, "Faculty not found."

    FacultyConsultantMapper.reassign_consultant(consultant, faculty_id)
    return True, "Faculty consultant reassigned successfully."


def delete_faculty_consultant(consultant_id):
    consultant = FacultyConsultantMapper.find_by_id(consultant_id)
    if not consultant:
        return False, "Faculty consultant not found."
    FacultyConsultantMapper.delete_consultant_by_id(consultant)
    return True, "Faculty consultant deleted successfully."


# ── Excel import preview ──────────────────────────────────────────────

def preview_student_excel(file_path):
    import os
    if not file_path or not os.path.exists(file_path):
        return False, "File not found.", []
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path)
        ws = wb.active
        rows = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row:
                continue
            rows.append({
                "student_id": str(row[0]).strip() if row[0] else "",
                "student_name": str(row[1]).strip() if row[1] else "",
                "major": str(row[2]).strip() if len(row) > 2 and row[2] else "",
                "status": str(row[3]).strip() if len(row) > 3 and row[3] else "Normal",
                "group_id": str(row[4]).strip() if len(row) > 4 and row[4] else "",
                "mentor_name": str(row[5]).strip() if len(row) > 5 and row[5] else "",
                "office": str(row[6]).strip() if len(row) > 6 and row[6] else "",
                "mentor_email": str(row[7]).strip() if len(row) > 7 and row[7] else "",
            })
        return True, f"Found {len(rows)} rows.", rows
    except Exception as e:
        return False, str(e), []


def preview_coordinator_excel(file_path):
    import os
    if not file_path or not os.path.exists(file_path):
        return False, "File not found.", []
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path)
        ws = wb.active
        rows = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row:
                continue
            rows.append({
                "name": str(row[0]).strip() if row[0] else "",
                "email": str(row[1]).strip() if row[1] else "",
                "department": str(row[2]).strip() if len(row) > 2 and row[2] else "",
                "account": str(row[3]).strip() if len(row) > 3 and row[3] else "",
            })
        return True, f"Found {len(rows)} rows.", rows
    except Exception as e:
        return False, str(e), []


def get_group_by_db_id(group_id):
    return GroupMapper.find_by_id(group_id)


def import_mcp_info(file_path):
    from app.entity.student import MCPInfo
    return MCPInfo.import_mcp_info(file_path)


def import_coordinator_info(file_path):
    from app.entity.coordinator import CoordinatorInfo
    return CoordinatorInfo.import_coordinator_info(file_path)
