"""Data mappers for Faculty, Department, Major entities and organization import."""

from app.extensions import db
from app.entity.faculty import Faculty
from app.entity.department import Department
from app.entity.major import Major
from app.entity.coordinator import Coordinator
from app.entity.faculty_consultant import FacultyConsultant


class FacultyMapper:
    """Data mapper for Faculty entity."""

    @staticmethod
    def find_all_active():
        return Faculty.query.filter_by(active=True).all()

    @staticmethod
    def find_by_id(faculty_id):
        return Faculty.query.get(faculty_id)

    @staticmethod
    def find_by_name(name):
        return Faculty.query.filter_by(name=name.strip()).first()

    @staticmethod
    def find_without_consultant():
        assigned_ids = {
            fc.faculty_id for fc in FacultyConsultant.query.filter(
                FacultyConsultant.faculty_id.isnot(None)
            ).all()
        }
        if assigned_ids:
            return Faculty.query.filter(
                Faculty.active == True,
                ~Faculty.id.in_(assigned_ids)
            ).all()
        return Faculty.query.filter(Faculty.active == True).all()

    @staticmethod
    def create(name):
        name = name.strip()
        if not name:
            return None
        existing = Faculty.query.filter_by(name=name).first()
        if existing:
            return existing
        faculty = Faculty(name=name, active=True)
        db.session.add(faculty)
        db.session.commit()
        return faculty

    @staticmethod
    def soft_delete(faculty):
        faculty.active = False
        db.session.commit()

    @staticmethod
    def assign_consultant(faculty, consultant):
        if not consultant:
            return
        old = FacultyConsultant.query.filter_by(faculty_id=faculty.id).first()
        if old and old.id != consultant.id:
            old.faculty_id = None
        consultant.faculty_id = faculty.id
        db.session.commit()

    @staticmethod
    def get_consultant(faculty):
        return FacultyConsultant.query.filter_by(faculty_id=faculty.id).first()


class DepartmentMapper:
    """Data mapper for Department entity."""

    @staticmethod
    def find_all_active():
        return Department.query.filter_by(active=True).all()

    @staticmethod
    def find_by_name(name):
        return Department.query.filter_by(name=name.strip()).first()

    @staticmethod
    def find_by_id(dept_id):
        return Department.query.get(dept_id)

    @staticmethod
    def find_by_faculty_and_name(faculty_id, name):
        return Department.query.filter_by(faculty_id=faculty_id, name=name).first()

    @staticmethod
    def find_by_faculty_and_dept_name(faculty_name, dept_name):
        return Department.query.join(Faculty).filter(
            Faculty.name == faculty_name, Department.name == dept_name
        ).first()

    @staticmethod
    def find_active_by_faculty(faculty_id):
        return Department.query.filter_by(faculty_id=faculty_id, active=True).all()

    @staticmethod
    def create(faculty_id, name):
        name = name.strip()
        if not name:
            return None
        existing = Department.query.filter_by(faculty_id=faculty_id, name=name).first()
        if existing:
            return existing
        dept = Department(name=name, faculty_id=faculty_id, active=True)
        db.session.add(dept)
        db.session.commit()
        return dept

    @staticmethod
    def add_to_faculty(faculty, department):
        if not department:
            return False
        if DepartmentMapper.find_by_faculty_and_name(faculty.id, department.name):
            return False
        department.faculty_id = faculty.id
        db.session.add(department)
        db.session.commit()
        return True

    @staticmethod
    def soft_delete_by_name(faculty_name, dept_name):
        dept = DepartmentMapper.find_by_faculty_and_dept_name(faculty_name, dept_name)
        if not dept:
            return False
        dept.active = False
        db.session.commit()
        return True

    @staticmethod
    def assign_coordinator(department, coordinator):
        if not coordinator:
            return
        old = Coordinator.query.filter_by(department_id=department.id).first()
        if old and old.id != coordinator.id:
            old.department_id = None
        coordinator.department_id = department.id
        db.session.commit()

    @staticmethod
    def get_coordinator(department):
        return Coordinator.query.filter_by(department_id=department.id).first()


class MajorMapper:
    """Data mapper for Major entity."""

    @staticmethod
    def find_by_id(major_id):
        return Major.query.get(major_id)

    @staticmethod
    def find_by_department_and_name(department_id, name):
        return Major.query.filter_by(department_id=department_id, name=name).first()

    @staticmethod
    def find_by_path(faculty_name, dept_name, major_name):
        return Major.query.join(Department).join(Faculty).filter(
            Faculty.name == faculty_name,
            Department.name == dept_name,
            Major.name == major_name,
        ).first()

    @staticmethod
    def find_active_by_department(department_id):
        return Major.query.filter_by(department_id=department_id, active=True).all()

    @staticmethod
    def create(department_id, name):
        name = name.strip()
        if not name:
            return None
        existing = Major.query.filter_by(department_id=department_id, name=name).first()
        if existing:
            return existing
        major = Major(name=name, department_id=department_id, active=True)
        db.session.add(major)
        db.session.commit()
        return major

    @staticmethod
    def soft_delete_by_path(faculty_name, dept_name, major_name):
        major = MajorMapper.find_by_path(faculty_name, dept_name, major_name)
        if not major:
            return False
        major.active = False
        db.session.commit()
        return True


class OrganizationImportMapper:
    """Data mapper for organization unit import (formerly UnitInfo)."""

    @staticmethod
    def get_unit_list():
        units = []
        for f in Faculty.query.filter_by(active=True).all():
            units.append(f)
        for d in Department.query.filter_by(active=True).all():
            units.append(d)
        for m in Major.query.filter_by(active=True).all():
            units.append(m)
        return units

    @staticmethod
    def import_organization(excel_file_path):
        import os
        if not excel_file_path or not os.path.exists(excel_file_path):
            return False
        try:
            import openpyxl
            wb = openpyxl.load_workbook(excel_file_path)
            ws = wb.active
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or len(row) < 3:
                    continue
                faculty_name = str(row[0]).strip() if row[0] else None
                dept_name = str(row[1]).strip() if row[1] else None
                major_name = str(row[2]).strip() if row[2] else None
                if not faculty_name:
                    continue
                faculty = FacultyMapper.create(faculty_name)
                if dept_name and faculty:
                    department = DepartmentMapper.create(faculty.id, dept_name)
                    if major_name and department:
                        MajorMapper.create(department.id, major_name)
            return True
        except Exception:
            return False
