"""Record, WordFile, and LogActivity entity classes."""

import json
from app.utils.time_utils import local_now

from app.extensions import db


word_file_records = db.Table(
    "word_file_records",
    db.Column("word_file_id", db.Integer, db.ForeignKey("word_files.id"), primary_key=True),
    db.Column("record_id", db.Integer, db.ForeignKey("records.id"), primary_key=True),
)


class Record(db.Model):
    __tablename__ = "records"

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.String(80), unique=True, nullable=False)

    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey("mentors.id"), nullable=False)

    interview_date = db.Column(db.Date, nullable=False)
    interview_time = db.Column(db.Time, nullable=False)

    problem_statement = db.Column(db.Text, nullable=False)
    interview_summary = db.Column(db.Text, nullable=False)
    followup_action = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=local_now)
    updated_at = db.Column(db.DateTime, default=local_now, onupdate=local_now)

    student = db.relationship("Student", backref="records")
    mentor = db.relationship("Mentor", backref="records")

    def add_record(self):
        from app.mapper.record_mapper import RecordMapper
        return RecordMapper.add(self)

    def addRecord(self):
        return self.add_record()

    def modify_record(self):
        from app.mapper.record_mapper import RecordMapper
        return RecordMapper.update(self)

    def modifyRecord(self):
        return self.modify_record()

    def delete_record(self):
        from app.mapper.record_mapper import RecordMapper
        return RecordMapper.delete(self)

    def deleteRecord(self):
        return self.delete_record()


class WordFile(db.Model):
    __tablename__ = "word_files"

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.String(80), unique=True, nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    faculty = db.Column(db.String(120))
    department = db.Column(db.String(120))
    major = db.Column(db.String(120))
    academic_year_list_json = db.Column(db.Text, default="[]", nullable=False)

    created_at = db.Column(db.DateTime, default=local_now)

    records = db.relationship(
        "Record",
        secondary=lambda: word_file_records,
        backref="word_files",
        lazy=True,
    )

    @property
    def academicYearList(self):
        try:
            return json.loads(self.academic_year_list_json or "[]")
        except json.JSONDecodeError:
            return []

    @academicYearList.setter
    def academicYearList(self, value):
        if isinstance(value, list):
            self.academic_year_list_json = json.dumps(value)
        else:
            self.academic_year_list_json = json.dumps([])

    @property
    def recordList(self):
        return self.records

    def set_export_condition(
        self,
        faculty=None,
        department=None,
        major=None,
        academic_year=None,
        academic_year_list=None,
        mentor_name=None,
        student_name=None,
    ):
        self.faculty = faculty
        self.department = department
        self.major = major
        if academic_year_list:
            self.academicYearList = [str(y) for y in academic_year_list]
        elif academic_year:
            self.academicYearList = [str(academic_year)]

    def setExportCondition(self, faculty=None, department=None, major=None,
                           academic_year=None, academic_year_list=None,
                           mentor_name=None, student_name=None):
        return self.set_export_condition(
            faculty, department, major, academic_year, academic_year_list, mentor_name, student_name
        )

    def generate_word(self):
        return bool(self.file_path)

    def generateWord(self):
        return self.generate_word()


class LogActivity(db.Model):
    __tablename__ = "log_activities"

    id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.String(80), unique=True, nullable=False)

    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)

    login_time = db.Column(db.DateTime, nullable=False)
    logout_time = db.Column(db.DateTime, nullable=False)

    function_access = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=local_now)

    student = db.relationship("Student", backref="log_activities")

    def add_log(self):
        from app.mapper.record_mapper import RecordMapper
        return RecordMapper.add_log(self)

    def addLog(self):
        return self.add_log()
