"""Organization structure CRUD control logic."""

from app.mapper.organization_mapper import FacultyMapper, DepartmentMapper, MajorMapper


def get_organization_structure():
    return FacultyMapper.find_all_active()


def add_faculty(name):
    name = name.strip()
    if not name:
        return False, "Faculty name cannot be empty."
    existing = FacultyMapper.find_by_name(name)
    if existing:
        return False, "Faculty already exists."
    FacultyMapper.create(name)
    return True, "Faculty added successfully."


def add_department(faculty_id, name):
    name = name.strip()
    if not name:
        return False, "Department name cannot be empty."
    faculty = FacultyMapper.find_by_id(faculty_id)
    if not faculty:
        return False, "Faculty not found."
    existing = DepartmentMapper.find_by_faculty_and_name(faculty_id, name)
    if existing:
        return False, "Department already exists under this faculty."
    DepartmentMapper.create(faculty_id, name)
    return True, "Department added successfully."


def add_major(department_id, name):
    name = name.strip()
    if not name:
        return False, "Major name cannot be empty."
    department = DepartmentMapper.find_by_id(department_id)
    if not department:
        return False, "Department not found."
    existing = MajorMapper.find_by_department_and_name(department_id, name)
    if existing:
        return False, "Major already exists under this department."
    MajorMapper.create(department_id, name)
    return True, "Major added successfully."


def preview_org_excel(file_path):
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
                "faculty": str(row[0]).strip() if row[0] else "",
                "department": str(row[1]).strip() if len(row) > 1 and row[1] else "",
                "major": str(row[2]).strip() if len(row) > 2 and row[2] else "",
            })
        return True, f"Found {len(rows)} rows.", rows
    except Exception as e:
        return False, str(e), []


def get_all_active_faculties():
    return FacultyMapper.find_all_active()


def get_all_active_departments():
    return DepartmentMapper.find_all_active()


def import_organization(file_path):
    from app.mapper.organization_mapper import OrganizationImportMapper
    return OrganizationImportMapper.import_organization(file_path)
