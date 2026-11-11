"""Mentor entity class."""

import uuid

from app.extensions import db
from app.entity.user import FacultyMember


class Mentor(FacultyMember):
    __tablename__ = "mentors"

    id = db.Column(db.Integer, db.ForeignKey("faculty_members.id"), primary_key=True)
    mentor_id = db.Column(db.String(50), unique=True)
    office = db.Column(db.String(120))

    __mapper_args__ = {
        "polymorphic_identity": "mentor",
    }

    def forward_case(self, student_id, description):
        from app.mapper.mentor_mapper import MentorMapper
        return MentorMapper.forward_case(self, student_id, description)

    def forwardCase(self, student_id, description):
        return self.forward_case(student_id, description)

    def create_appointment(self, student_id, slot_list):
        from app.mapper.appointment_mapper import AppointmentMapper
        return AppointmentMapper.create_from_mentor(self, student_id, slot_list)

    def createAppointment(self, student_id, slot_list):
        return self.create_appointment(student_id, slot_list)

    def add_record(self, student_id, date, time, problem_statement, interview_summary, followup_action):
        from app.mapper.student_mapper import StudentMapper
        from app.mapper.record_mapper import RecordMapper
        from app.entity.record import Record
        student = StudentMapper.find_by_student_id(student_id)
        if not student:
            return False
        record = Record(
            record_id=f"R-{uuid.uuid4().hex[:10].upper()}",
            student_id=student.id,
            mentor_id=self.id,
            interview_date=date,
            interview_time=time,
            problem_statement=problem_statement,
            interview_summary=interview_summary,
            followup_action=followup_action,
        )
        return RecordMapper.add(record)

    def addRecord(self, student_id, date, time, problem_statement, interview_summary, followup_action):
        return self.add_record(student_id, date, time, problem_statement, interview_summary, followup_action)

    def modify_record(self, record_id, problem_statement, interview_summary, followup_action):
        from app.mapper.record_mapper import RecordMapper
        record = RecordMapper.find_by_record_id(record_id)
        if not record or record.mentor_id != self.id:
            return False
        if not problem_statement or not interview_summary or not followup_action:
            return False
        record.problem_statement = problem_statement
        record.interview_summary = interview_summary
        record.followup_action = followup_action
        return RecordMapper.update(record)

    def modifyRecord(self, record_id, problem_statement, interview_summary, followup_action):
        return self.modify_record(record_id, problem_statement, interview_summary, followup_action)

    def delete_record(self, record_id):
        from app.mapper.record_mapper import RecordMapper
        record = RecordMapper.find_by_record_id(record_id)
        if not record or record.mentor_id != self.id:
            return False
        return RecordMapper.delete(record)

    def deleteRecord(self, record_id):
        return self.delete_record(record_id)

    def export_record(self, student_id_list, file_path):
        import os
        from app.mapper.record_mapper import RecordMapper
        records = RecordMapper.find_by_mentor_and_student_ids(self.id, student_id_list)
        if not records:
            return False
        try:
            from docx import Document
            doc = Document()
            doc.add_heading("Interview Records Export", level=1)
            for r in records:
                doc.add_paragraph(f"Student: {r.student.student_id} - {r.student.name}")
                doc.add_paragraph(f"Date: {r.interview_date} {r.interview_time}")
                doc.add_paragraph(f"Problem: {r.problem_statement}")
                doc.add_paragraph(f"Summary: {r.interview_summary}")
                doc.add_paragraph(f"Follow-up: {r.followup_action}")
                doc.add_paragraph("")
            doc.save(file_path)
        except Exception:
            with open(file_path, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(f"{r.record_id} | {r.student.student_id}\n")
        return True

    def exportRecord(self, student_id_list, file_path):
        return self.export_record(student_id_list, file_path)
