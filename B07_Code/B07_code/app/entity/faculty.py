"""Faculty entity and OrganizationUnit mixin."""

from app.utils.time_utils import local_now

from app.extensions import db


class OrganizationUnit(object):
    """Pure mixin — no database access at class level."""

    unit_id = None
    name = None
    unit_type = None
    active = None
    created_date = None
    updated_date = None

    def getUnitId(self):
        return str(self.id)

    def getName(self):
        return self.name

    def setName(self, name):
        if name and name.strip():
            self.name = name.strip()
            db.session.commit()

    def getUnitType(self):
        return type(self).__name__

    def isActive(self):
        return bool(self.active)

    def validateName(self, name):
        if not name or not name.strip():
            return False
        return True


class Faculty(db.Model, OrganizationUnit):
    __tablename__ = "faculties"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=local_now)
    updated_at = db.Column(db.DateTime, default=local_now, onupdate=local_now)

    departments = db.relationship("Department", backref="faculty", lazy=True)

    def add_department(self, department):
        from app.mapper.organization_mapper import DepartmentMapper
        return DepartmentMapper.add_to_faculty(self, department)

    def addDepartment(self, department):
        return self.add_department(department)

    def remove_department(self, dept_name):
        dept = self.get_department(dept_name)
        if not dept:
            return False
        db.session.delete(dept)
        db.session.commit()
        return True

    def removeDepartment(self, dept_name):
        return self.remove_department(dept_name)

    def get_all_departments(self):
        from app.entity.department import Department
        return Department.query.filter_by(faculty_id=self.id, active=True).all()

    def getAllDepartments(self):
        return self.get_all_departments()

    def get_department(self, dept_name):
        from app.entity.department import Department
        return Department.query.filter_by(faculty_id=self.id, name=dept_name).first()

    def getDepartment(self, dept_name):
        return self.get_department(dept_name)

    def assign_consultant(self, consultant):
        from app.mapper.organization_mapper import FacultyMapper
        FacultyMapper.assign_consultant(self, consultant)

    def assignConsultant(self, consultant):
        return self.assign_consultant(consultant)

    def get_consultant(self):
        from app.mapper.organization_mapper import FacultyMapper
        return FacultyMapper.get_consultant(self)

    def getConsultant(self):
        return self.get_consultant()

    def has_department(self, dept_name):
        return self.get_department(dept_name) is not None

    def hasDepartment(self, dept_name):
        return self.has_department(dept_name)

    @property
    def consultant(self):
        from app.mapper.organization_mapper import FacultyMapper
        return FacultyMapper.get_consultant(self)


class UnitInfo:
    """Static helper — delegates to mapper layer."""

    @staticmethod
    def get_unit_list():
        from app.mapper.organization_mapper import OrganizationImportMapper
        return OrganizationImportMapper.get_unit_list()

    @staticmethod
    def unitList():
        return UnitInfo.get_unit_list()

    @staticmethod
    def import_organization(excel_file_path):
        from app.mapper.organization_mapper import OrganizationImportMapper
        return OrganizationImportMapper.import_organization(excel_file_path)

    @staticmethod
    def importOrganization(excel_file_path):
        return UnitInfo.import_organization(excel_file_path)

    @staticmethod
    def add_faculty(faculty_name):
        from app.mapper.organization_mapper import FacultyMapper
        return FacultyMapper.create(faculty_name)

    @staticmethod
    def addFaculty(faculty_name):
        return UnitInfo.add_faculty(faculty_name)

    @staticmethod
    def add_department(faculty_name, dept_name):
        from app.mapper.organization_mapper import FacultyMapper, DepartmentMapper
        faculty = FacultyMapper.find_by_name(faculty_name)
        if not faculty:
            return None
        return DepartmentMapper.create(faculty.id, dept_name)

    @staticmethod
    def addDepartment(faculty_name, dept_name):
        return UnitInfo.add_department(faculty_name, dept_name)

    @staticmethod
    def add_major(faculty_name, dept_name, major_name):
        from app.mapper.organization_mapper import DepartmentMapper, MajorMapper
        dept = DepartmentMapper.find_by_faculty_and_dept_name(faculty_name, dept_name)
        if not dept:
            return None
        return MajorMapper.create(dept.id, major_name)

    @staticmethod
    def addMajor(faculty_name, dept_name, major_name):
        return UnitInfo.add_major(faculty_name, dept_name, major_name)

    @staticmethod
    def get_faculty(faculty_name):
        from app.mapper.organization_mapper import FacultyMapper
        return FacultyMapper.find_by_name(faculty_name)

    @staticmethod
    def getFaculty(faculty_name):
        return UnitInfo.get_faculty(faculty_name)

    @staticmethod
    def get_department(faculty_name, dept_name):
        from app.mapper.organization_mapper import DepartmentMapper
        return DepartmentMapper.find_by_faculty_and_dept_name(faculty_name, dept_name)

    @staticmethod
    def getDepartment(faculty_name, dept_name):
        return UnitInfo.get_department(faculty_name, dept_name)

    @staticmethod
    def get_major(faculty_name, dept_name, major_name):
        from app.mapper.organization_mapper import MajorMapper
        return MajorMapper.find_by_path(faculty_name, dept_name, major_name)

    @staticmethod
    def getMajor(faculty_name, dept_name, major_name):
        return UnitInfo.get_major(faculty_name, dept_name, major_name)

    @staticmethod
    def remove_faculty(faculty_name):
        from app.mapper.organization_mapper import FacultyMapper
        faculty = FacultyMapper.find_by_name(faculty_name)
        if not faculty:
            return False
        FacultyMapper.soft_delete(faculty)
        return True

    @staticmethod
    def removeFaculty(faculty_name):
        return UnitInfo.remove_faculty(faculty_name)

    @staticmethod
    def remove_department(faculty_name, dept_name):
        from app.mapper.organization_mapper import DepartmentMapper
        return DepartmentMapper.soft_delete_by_name(faculty_name, dept_name)

    @staticmethod
    def removeDepartment(faculty_name, dept_name):
        return UnitInfo.remove_department(faculty_name, dept_name)

    @staticmethod
    def remove_major(faculty_name, dept_name, major_name):
        from app.mapper.organization_mapper import MajorMapper
        return MajorMapper.soft_delete_by_path(faculty_name, dept_name, major_name)

    @staticmethod
    def removeMajor(faculty_name, dept_name, major_name):
        return UnitInfo.remove_major(faculty_name, dept_name, major_name)
