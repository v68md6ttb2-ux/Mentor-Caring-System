"""FacultyConsultant entity class."""

from app.extensions import db
from app.entity.user import FacultyMember


class FacultyConsultant(FacultyMember):
    __tablename__ = "faculty_consultants"

    id = db.Column(db.Integer, db.ForeignKey("faculty_members.id"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": "faculty_consultant",
    }

    def change_group_mentor(self, group_id, mentor_email):
        from app.mapper.mcp_group_mapper import GroupMapper
        return GroupMapper.change_mentor_by_display_id(group_id, mentor_email)

    def changeGroupMentor(self, group_id, mentor_email):
        return self.change_group_mentor(group_id, mentor_email)

    def designate_coordinator(self, department_name, coordinator_name):
        from app.mapper.organization_mapper import DepartmentMapper
        from app.mapper.mentor_mapper import MentorMapper
        department = DepartmentMapper.find_by_name(department_name)
        if not department:
            return False
        coordinator = MentorMapper.find_coordinator_by_name(coordinator_name)
        if not coordinator:
            return False
        DepartmentMapper.assign_coordinator(department, coordinator)
        return True

    def designateCoordinator(self, department_name, coordinator_name):
        return self.designate_coordinator(department_name, coordinator_name)

    def add_student_to_group(self, student_id, group_id):
        from app.mapper.mcp_group_mapper import GroupMapper
        group = GroupMapper.find_by_display_id(group_id)
        if not group:
            return False
        return GroupMapper.add_student_to_group(student_id, group)

    def addStudentToGroup(self, student_id, group_id):
        return self.add_student_to_group(student_id, group_id)

    def delete_student_from_group(self, student_id, group_id):
        from app.mapper.mcp_group_mapper import GroupMapper
        group = GroupMapper.find_by_display_id(group_id)
        if not group:
            return False
        return GroupMapper.remove_student_from_group(student_id, group)

    def deleteStudentFromGroup(self, student_id, group_id):
        return self.delete_student_from_group(student_id, group_id)

    def view_log(self, student_id):
        from app.mapper.record_mapper import RecordMapper
        from app.mapper.student_mapper import StudentMapper
        student = StudentMapper.find_by_student_id(student_id)
        if not student:
            return []
        return RecordMapper.find_log_by_student_id(student.id)

    def viewLog(self, student_id):
        return self.view_log(student_id)

    def export_word_file(self, academic_year_list, department_name, major_name, mentor_name, student_name, file_path):
        from app.mapper.record_mapper import RecordMapper
        records = RecordMapper.search(
            academic_year_list=academic_year_list,
            department_name=department_name,
            mentor_name=mentor_name,
            student_name=student_name,
        )
        if not records:
            return False
        try:
            from docx import Document
            doc = Document()
            doc.add_heading("MCS Export", level=1)
            for r in records:
                doc.add_paragraph(f"Record: {r.record_id}")
                doc.add_paragraph(f"Student: {r.student.name}")
                doc.add_paragraph(f"Mentor: {r.mentor.name}")
                doc.add_paragraph("")
            doc.save(file_path)
        except Exception:
            with open(file_path, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(f"{r.record_id}\n")
        return True

    def exportWordFile(self, academic_year_list, department_name, major_name, mentor_name, student_name, file_path):
        return self.export_word_file(academic_year_list, department_name, major_name, mentor_name, student_name, file_path)

    def import_mcp_info(self, file_path):
        from app.mapper.student_mapper import MCPInfoImportMapper
        return MCPInfoImportMapper.import_from_excel(file_path)

    def importMCPInfo(self, file_path):
        return self.import_mcp_info(file_path)

    def import_coordinator_info(self, file_path):
        from app.mapper.student_mapper import CoordinatorInfoImportMapper
        return CoordinatorInfoImportMapper.import_from_excel(file_path)

    def importCoordinatorInfo(self, file_path):
        return self.import_coordinator_info(file_path)

    def search_mentor(self, keyword):
        from app.mapper.mentor_mapper import MentorMapper
        return MentorMapper.search_with_groups(keyword)

    def searchMentor(self, keyword):
        return self.search_mentor(keyword)
