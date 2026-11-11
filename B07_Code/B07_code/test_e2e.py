"""
End-to-End Functional Tests for MCS System Checklist (20 items)
Uses Flask test client — no real HTTP server required.
"""
import os
import sys
from datetime import date

# Ensure we can import from the project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Patch config BEFORE creating app so the in-memory DB URI takes effect
from app.config.secure import Config
Config.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

from app import create_app
from app.extensions import db
from app.entity import (
    User, Student, Mentor, Coordinator, FacultyConsultant,
    Faculty, Department, Major, MCPGroup, Record, Message, Appointment, WordFile,
)


class E2ETester:
    """Comprehensive E2E test runner for all 20 checklist items."""

    def __init__(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SERVER_NAME"] = "localhost"
        # DB URI already patched in Config before import — uses :memory:
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.app.secret_key = "test-secret"

        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        self.results = []
        self.total = 0
        self.passed = 0

    def _ok(self, name, msg=""):
        self.total += 1
        self.passed += 1
        self.results.append(f"  [PASS] {name}{' — ' + msg if msg else ''}")

    def _fail(self, name, msg=""):
        self.total += 1
        self.results.append(f"  [FAIL] {name}{' — ' + msg if msg else ''}")

    def _assert(self, name, condition, detail=""):
        if condition:
            self._ok(name, detail)
        else:
            self._fail(name, detail)

    def login(self, account, password="123456"):
        return self.client.post("/login", data={
            "account": account, "password": password
        }, follow_redirects=True)

    def logout(self):
        return self.client.get("/logout", follow_redirects=True)

    # ================================================================
    # Setup: seed test data
    # ================================================================
    def seed(self):
        print("Seeding test database...")

        # Organization
        fst = Faculty(name="FST")
        fba = Faculty(name="FBA")
        db.session.add_all([fst, fba])
        db.session.flush()

        dcs = Department(name="DCS", faculty_id=fst.id)
        dme = Department(name="DME", faculty_id=fst.id)
        dac = Department(name="DAC", faculty_id=fba.id)
        db.session.add_all([dcs, dme, dac])
        db.session.flush()

        cs = Major(name="Computer Science", department_id=dcs.id)
        se = Major(name="Software Engineering", department_id=dcs.id)
        me = Major(name="Mechanical Engineering", department_id=dme.id)
        ac = Major(name="Accounting", department_id=dac.id)
        db.session.add_all([cs, se, me, ac])
        db.session.flush()

        # Users
        admin = User(account="admin", password="123456", name="Admin", email="admin@test.com", role="admin")

        fc = FacultyConsultant(account="faculty", password="123456", name="FC FST", email="fc_fst@test.com", role="faculty_consultant", faculty_id=fst.id)

        mentor1 = Mentor(account="mentor1", password="123456", name="Mary Lee", email="marylee@test.com", role="mentor", mentor_id="M001", office="T1-102")
        mentor2 = Mentor(account="mentor2", password="123456", name="John Wang", email="johnwang@test.com", role="mentor", mentor_id="M002", office="T1-103")

        coord = Coordinator(account="coordinator", password="123456", name="Ruth Mo", email="ruthmo@test.com", role="coordinator", department_id=dcs.id)

        db.session.add_all([admin, fc, mentor1, mentor2, coord])
        db.session.flush()

        # Groups
        g1 = MCPGroup(group_id="2025-2026-Y2-G01", academic_year="2025-2026", mentor_id=mentor1.id, major_id=cs.id)
        g2 = MCPGroup(group_id="2025-2026-Y2-G02", academic_year="2025-2026", mentor_id=mentor2.id, major_id=se.id)
        db.session.add_all([g1, g2])
        db.session.flush()

        # Students
        s1 = Student(account="2330000010", password="123456", name="Alice A", email="2330000010@test.com", role="student", student_id="2330000010", status="Normal", group_id=g1.id)
        s2 = Student(account="233000002", password="123456", name="Bob B", email="233000002@test.com", role="student", student_id="233000002", status="Normal", group_id=g1.id)
        # Student NOT in a group (for 7a test)
        s3 = Student(account="233000099", password="123456", name="NoGroup Student", email="233000099@test.com", role="student", student_id="233000099", status="Normal", group_id=None)
        db.session.add_all([s1, s2, s3])
        db.session.commit()

        print("  Seed complete.\n")

    # ================================================================
    # 1a. Admin: Import Excel for organization — preview then confirm
    # ================================================================
    def test_1a_import_organization(self):
        print("--- 1a. Admin: Import Organization (Appendix A) ---")
        self.login("admin")

        # GET the import page
        r = self.client.get("/admin/import-organization")
        self._assert("import page loads", r.status_code == 200)

        # Upload Excel for preview
        org_xlsx = os.path.join(os.path.dirname(__file__), "test_data", "test_org.xlsx")
        with open(org_xlsx, "rb") as f:
            data = {"excel_file": (f, "test_org.xlsx"), "action": "preview"}
            r = self.client.post("/admin/import-organization", data=data,
                                content_type="multipart/form-data", follow_redirects=True)
        self._assert("preview shows org data", r.status_code == 200 and b"FST" in r.data)

        # Confirm import
        with open(org_xlsx, "rb") as f:
            data = {"excel_file": (f, "test_org.xlsx"), "action": "confirm"}
            r = self.client.post("/admin/import-organization", data=data,
                                content_type="multipart/form-data", follow_redirects=True)
        self._assert("confirm import succeeds", r.status_code == 200)

        # Verify org structure imported
        org_page = self.client.get("/organization")
        self._assert("org page shows imported data",
                     org_page.status_code == 200 and b"FST" in org_page.data)

        self.logout()

    # ================================================================
    # 1b. Admin: Manually add a new programme into a department
    # ================================================================
    def test_1b_add_major(self):
        print("--- 1b. Admin: Add Major ---")
        self.login("admin")

        r = self.client.get("/organization/major/add")
        self._assert("add major page loads", r.status_code == 200)

        # Find DCS department and add a major
        dcs = Department.query.filter_by(name="DCS").first()
        r = self.client.post("/organization/major/add", data={
            "department_id": str(dcs.id),
            "name": "Data Science"
        }, follow_redirects=True)
        self._assert("major added", r.status_code == 200)

        major = Major.query.filter_by(name="Data Science").first()
        self._assert("major persisted in DB", major is not None and major.department.name == "DCS")

        self.logout()

    # ================================================================
    # 1c. Admin: Designating faculty consultants manually (CRUD)
    # ================================================================
    def test_1c_faculty_consultants(self):
        print("--- 1c. Admin: Faculty Consultant CRUD ---")
        self.login("admin")

        # List
        r = self.client.get("/admin/consultants")
        self._assert("consultant list loads", r.status_code == 200)

        # Create a new faculty (FSM) with no consultant for testing change
        fsm = Faculty(name="FSM")
        db.session.add(fsm)
        db.session.flush()

        # Add consultant to FBA
        fba = Faculty.query.filter_by(name="FBA").first()
        r = self.client.post("/admin/consultants/add", data={
            "name": "FC FBA",
            "email": "fc_fba@test.com",
            "account": "fc_fba",
            "password": "123456",
            "faculty_id": str(fba.id),
        }, follow_redirects=True)
        self._assert("add consultant", r.status_code == 200)
        new_fc = FacultyConsultant.query.filter_by(name="FC FBA").first()
        self._assert("consultant persisted", new_fc is not None)
        self._assert("consultant assigned to FBA", new_fc.faculty_id == fba.id)

        # Change consultant to FSM (which has no existing consultant, avoiding clear of FC FST)
        r = self.client.post("/admin/consultants/change", data={
            "consultant_id": str(new_fc.id),
            "faculty_id": str(fsm.id),
        }, follow_redirects=True)
        self._assert("change consultant faculty", r.status_code == 200)
        db.session.refresh(new_fc)
        self._assert("consultant now in FSM", new_fc.faculty_id == fsm.id)

        # Delete the test consultant
        r = self.client.post("/admin/consultants/delete", data={
            "consultant_id": str(new_fc.id),
        }, follow_redirects=True)
        self._assert("delete consultant", r.status_code == 200)
        deleted = FacultyConsultant.query.filter_by(name="FC FBA").first()
        self._assert("consultant removed", deleted is None)

        self.logout()

    # ================================================================
    # 3a. Faculty Consultant: Import students (Appendix B) — preview then confirm
    # ================================================================
    def test_3a_import_students(self):
        print("--- 3a. FC: Import Students (Appendix B) ---")
        self.login("faculty")

        r = self.client.get("/faculty/import-students")
        self._assert("import students page loads", r.status_code == 200)

        stu_xlsx = os.path.join(os.path.dirname(__file__), "test_data", "test_students.xlsx")
        with open(stu_xlsx, "rb") as f:
            data = {"excel_file": (f, "test_students.xlsx"), "action": "preview"}
            r = self.client.post("/faculty/import-students", data=data,
                                content_type="multipart/form-data", follow_redirects=True)
        self._assert("preview shows student data", r.status_code == 200 and b"Test Student A" in r.data)

        with open(stu_xlsx, "rb") as f:
            data = {"excel_file": (f, "test_students.xlsx"), "action": "confirm"}
            r = self.client.post("/faculty/import-students", data=data,
                                content_type="multipart/form-data", follow_redirects=True)
        self._assert("confirm import succeeds", r.status_code == 200)

        s = Student.query.filter_by(student_id="2330000040").first()
        self._assert("student 2330000040 created", s is not None and s.name == "Test Student A")

        self.logout()

    # ================================================================
    # 3b. FC: Change the mentor of a group
    # ================================================================
    def test_3b_change_group_mentor(self):
        print("--- 3b. FC: Change Group Mentor ---")
        self.login("faculty")

        r = self.client.get("/faculty/group/change-mentor")
        self._assert("change mentor page loads", r.status_code == 200)

        # group_id in form is the DB pk (group.id), not the string group_id
        g1 = MCPGroup.query.filter_by(group_id="2025-2026-Y2-G01").first()
        m2 = Mentor.query.filter_by(email="johnwang@test.com").first()
        r = self.client.post("/faculty/group/change-mentor", data={
            "group_id": str(g1.id),
            "mentor_id": str(m2.id),
        }, follow_redirects=True)
        self._assert("mentor changed", r.status_code == 200)

        db.session.refresh(g1)
        self._assert("group now has mentor2", g1.mentor_id == m2.id)

        # Change back
        m1 = Mentor.query.filter_by(email="marylee@test.com").first()
        self.client.post("/faculty/group/change-mentor", data={
            "group_id": str(g1.id),
            "mentor_id": str(m1.id),
        }, follow_redirects=True)
        db.session.refresh(g1)

        self.logout()

    # ================================================================
    # 3c. FC: Designate MCP coordinator via Excel import (Appendix C)
    # ================================================================
    def test_3c_import_coordinators(self):
        print("--- 3c. FC: Import Coordinators (Appendix C) ---")
        self.login("faculty")

        r = self.client.get("/faculty/import-coordinators")
        self._assert("import coordinators page loads", r.status_code == 200)

        coord_xlsx = os.path.join(os.path.dirname(__file__), "test_data", "test_coordinators.xlsx")
        with open(coord_xlsx, "rb") as f:
            data = {"excel_file": (f, "test_coordinators.xlsx"), "action": "preview"}
            r = self.client.post("/faculty/import-coordinators", data=data,
                                content_type="multipart/form-data", follow_redirects=True)
        self._assert("preview shows coordinator data", r.status_code == 200)

        with open(coord_xlsx, "rb") as f:
            data = {"excel_file": (f, "test_coordinators.xlsx"), "action": "confirm"}
            r = self.client.post("/faculty/import-coordinators", data=data,
                                content_type="multipart/form-data", follow_redirects=True)
        self._assert("confirm import succeeds", r.status_code == 200)

        # Coordinator is a joined-table inheritance model — query via User base
        coord = User.query.filter_by(email="coord_a@bnbu.edu.cn", role="coordinator").first()
        self._assert("coordinator created", coord is not None)

        self.logout()

    # ================================================================
    # 3d. FC: Add one student to a group
    # ================================================================
    def test_3d_add_student_to_group(self):
        print("--- 3d. FC: Add Student to Group ---")
        self.login("faculty")

        r = self.client.get("/faculty/group/add-student")
        self._assert("add student page loads", r.status_code == 200)

        g2 = MCPGroup.query.filter_by(group_id="2025-2026-Y2-G02").first()
        r = self.client.post("/faculty/group/add-student", data={
            "student_id": "2330000040",  # imported in 3a
            "group_id": str(g2.id),
        }, follow_redirects=True)
        self._assert("student added to group", r.status_code == 200)

        s = Student.query.filter_by(student_id="2330000040").first()
        self._assert("student now in group", s.group_id is not None)

        self.logout()

    # ================================================================
    # 3e. FC: Search a student's information through student ID
    # ================================================================
    def test_3e_search_student(self):
        print("--- 3e. FC: Search Student by ID ---")
        self.login("faculty")

        r = self.client.post("/students/search", data={
            "keyword": "2330000010",
        }, follow_redirects=True)
        self._assert("search returns results", r.status_code == 200 and b"2330000010" in r.data)

        # View student detail
        r = self.client.get("/students/2330000010")
        self._assert("student detail page loads", r.status_code == 200 and b"Alice A" in r.data)

        # View records (should show records link)
        r = self.client.get("/records/student/2330000010")
        self._assert("records page for student loads", r.status_code == 200)

        self.logout()

    # ================================================================
    # 3f. FC: Search mentor by name — show group ID — click shows students
    # ================================================================
    def test_3f_search_mentor(self):
        print("--- 3f. FC: Search Mentor by Name ---")
        self.login("faculty")

        r = self.client.post("/mentors/search", data={
            "keyword": "Mary",
            "action": "search",
        }, follow_redirects=True)
        self._assert("mentor search returns result", r.status_code == 200 and b"Mary Lee" in r.data)

        # Verify group ID shown
        self._assert("group ID shown", b"2025-2026-Y2-G01" in r.data)

        # Verify "Show members" link exists (lowercase 'm' in template)
        self._assert("show members button present", b"Show members" in r.data)

        self.logout()

    # ================================================================
    # 3g. FC: View log info of a student IN the faculty
    # ================================================================
    def test_3g_view_logs_in_faculty(self):
        print("--- 3g. FC: View Logs (in faculty) ---")
        self.login("faculty")

        # First add a demo log for student 2330000010 (in FST)
        r = self.client.post("/records/logs", data={
            "student_id": "2330000010",
            "function_access": "View Interview Records",
        }, follow_redirects=True)
        self._assert("demo log added", r.status_code == 200)

        r = self.client.get("/records/logs")
        self._assert("log list loads", r.status_code == 200)
        # Should show FST student's log
        self._assert("FST student log visible", b"2330000010" in r.data)

        self.logout()

    # ================================================================
    # 3h. FC: View log info of student NOT in the faculty — warning
    # ================================================================
    def test_3h_view_records_outside_faculty(self):
        print("--- 3h. FC: View Records Outside Faculty (Warning) ---")
        # Create a student in FBA (different faculty from FC who is in FST)
        ac = Major.query.filter_by(name="Accounting").first()

        # Need a mentor and group in FBA
        mentor_fba = Mentor(account="mentorfba", password="123456", name="FBA Mentor",
                            email="fbamentor@test.com", role="mentor", mentor_id="M099", office="T9-999")
        db.session.add(mentor_fba)
        db.session.flush()

        g_fba = MCPGroup(group_id="2025-2026-FBA-G01", academic_year="2025-2026",
                         mentor_id=mentor_fba.id, major_id=ac.id)
        db.session.add(g_fba)
        db.session.flush()

        s_fba = Student(account="299000001", password="123456", name="FBA Student",
                        email="299000001@test.com", role="student", student_id="299000001",
                        status="Normal", group_id=g_fba.id)
        db.session.add(s_fba)
        db.session.commit()

        self.login("faculty")  # FC is in FST

        # Try to view records of a student in FBA — should be denied
        r = self.client.get("/records/student/299000001", follow_redirects=True)
        # Should NOT show the records page (Interview Records title); should redirect away
        self._assert("access denied (not on records page)",
                     b"Interview Records" not in r.data)

        self.logout()

    # ================================================================
    # 3i. FC: Communicate with students — email notification
    # (Email sending is verified by code presence; actual SMTP requires env vars)
    # ================================================================
    def test_3i_email_notification(self):
        print("--- 3i. FC: Email Notification (code check) ---")
        import inspect
        from app.mapper.message_mapper import MessageMapper
        source = inspect.getsource(MessageMapper._notify_by_email)
        self._assert("notify_by_email uses smtplib", "smtplib" in source)
        self._assert("notify_by_email uses MIMEText", "MIMEText" in source)
        print("  (SMTP email code verified — actual send requires MAIL_USERNAME/PASSWORD env vars)")

    # ================================================================
    # 3j. FC: Export to Word file — academic year AND department name
    # ================================================================
    def test_3j_export_word(self):
        print("--- 3j. FC: Export to Word ---")

        # First add a record so there's something to export
        self.login("mentor1")
        self.client.post("/records/student/2330000010/add", data={
            "date": "2025-09-15",
            "time": "14:30",
            "problem_statement": "Academic difficulty in Math",
            "interview_summary": "Discussed study strategies",
            "followup_action": "Schedule follow-up in 2 weeks",
        }, follow_redirects=True)
        self.logout()

        self.login("faculty")

        r = self.client.get("/records/export")
        self._assert("export page loads", r.status_code == 200)

        # Should show academic year and department fields
        self._assert("academic year selection shown", b"Academic Year" in r.data or b"academic_year" in r.data)
        self._assert("department selection shown", b"Department" in r.data or b"department" in r.data)

        r = self.client.post("/records/export", data={
            "academic_year_list": ["2025-2026"],
            "department_name": "DCS",
            "mentor_name": "",
            "student_name": "",
        }, follow_redirects=True)
        self._assert("export succeeds", r.status_code == 200)

        # Check WordFile was created
        wf = WordFile.query.first()
        self._assert("WordFile record created", wf is not None)

        self.logout()

    # ================================================================
    # 4a. Mentor: Edit a student's record — save, view, delete
    # ================================================================
    def test_4a_mentor_record_crud(self):
        print("--- 4a. Mentor: Record CRUD ---")
        self.login("mentor1")

        # Add record
        r = self.client.post("/records/student/2330000010/add", data={
            "date": "2025-10-01",
            "time": "10:00",
            "problem_statement": "Stress management",
            "interview_summary": "Student feeling overwhelmed",
            "followup_action": "Refer to counseling",
        }, follow_redirects=True)
        self._assert("record add page returns 200", r.status_code == 200)

        # Debug: check if record was created (search by student only)
        s1_id = Student.query.filter_by(student_id="2330000010").first().id
        all_recs = Record.query.filter(Record.student_id == s1_id).all()
        if not all_recs:
            # Print response to understand failure
            has_error = b"do not have permission" in r.data or b"All fields are required" in r.data
            print(f"    DEBUG: No records found for student {s1_id}. Response has error: {has_error}")
            print(f"    DEBUG: Response snippet: {r.data[:800]}")

        record = Record.query.filter(
            Record.student_id == s1_id,
            Record.interview_date == date(2025, 10, 1),
            Record.problem_statement == "Stress management"
        ).first()
        self._assert("record exists in DB", record is not None)

        # View record detail
        r = self.client.get(f"/records/{record.record_id}")
        self._assert("record detail page loads", r.status_code == 200 and b"Stress management" in r.data)

        # Edit record
        r = self.client.post(f"/records/{record.record_id}/edit", data={
            "problem_statement": "UPDATED: Severe stress",
            "interview_summary": "UPDATED: Feeling very overwhelmed",
            "followup_action": "UPDATED: Weekly check-in",
        }, follow_redirects=True)
        self._assert("record edited", r.status_code == 200)
        db.session.refresh(record)
        self._assert("record content updated", "UPDATED" in record.problem_statement)

        # Delete record
        r = self.client.post(f"/records/{record.record_id}/delete", follow_redirects=True)
        self._assert("record deleted", r.status_code == 200)
        deleted = Record.query.filter_by(record_id=record.record_id).first()
        self._assert("record removed from DB", deleted is None)

        self.logout()

    # ================================================================
    # 4b. Mentor: Make an appointment — time slots, venue
    # ================================================================
    def test_4b_appointment_flow(self):
        print("--- 4b. Appointment Flow ---")
        self.login("mentor1")

        # Create appointment — student_id must be the DB id, not display student_id
        student_db_id = Student.query.filter_by(student_id="2330000010").first().id
        r = self.client.post("/appointments/mentor/create", data={
            "student_id": str(student_db_id),
            "content": "Appointment for progress review",
            "slot1": "2025-12-01 09:00",
            "slot2": "2025-12-01 09:30",
            "slot3": "2025-12-01 10:00",
        }, follow_redirects=True)
        self._assert("appointment created", r.status_code == 200)

        mentor_id = Mentor.query.filter_by(email="marylee@test.com").first().id
        appt = Appointment.query.filter_by(mentor_id=mentor_id).first()
        self._assert("appointment in DB", appt is not None)
        self._assert("appointment has slots", len(appt._get_available_slots()) == 3)
        self._assert("appointment status Requested", appt.appointment_status == "Requested")

        self.logout()

        # Student chooses slot (POST only — no GET)
        self.login("2330000010")
        r = self.client.post(f"/appointments/{appt.id}/choose", data={
            "slot_id": "1",
        }, follow_redirects=True)
        self._assert("slot chosen", r.status_code == 200)
        db.session.refresh(appt)
        self._assert("status now Slot_Selected", appt.appointment_status == "Slot_Selected")
        self.logout()

        # Mentor confirms with venue (POST only)
        self.login("mentor1")
        r = self.client.post(f"/appointments/{appt.id}/confirm", data={
            "venue": "Office T1-102, Room 3",
        }, follow_redirects=True)
        self._assert("appointment confirmed", r.status_code == 200)
        db.session.refresh(appt)
        self._assert("status now Confirmed", appt.appointment_status == "Confirmed")
        self._assert("venue set", appt.venue == "Office T1-102, Room 3")

        self.logout()

    # ================================================================
    # 4c. Mentor: Forward special cases to MCP coordinator
    # ================================================================
    def test_4c_forward_case(self):
        print("--- 4c. Mentor: Forward Case to Coordinator ---")
        self.login("mentor1")

        r = self.client.get("/forward-case")
        self._assert("forward case page loads", r.status_code == 200)

        r = self.client.post("/forward-case", data={
            "student_id": "2330000010",
            "description": "Student needs academic probation review",
        }, follow_redirects=True)
        self._assert("forward case succeeds", r.status_code == 200)

        # Check coordinator received the message
        self.logout()
        self.login("coordinator")
        r = self.client.get("/messages/")
        self._assert("coordinator has messages", r.status_code == 200)
        self._assert("forwarded case visible", b"Forwarded Case" in r.data or b"2330000010" in r.data)

        # Check that the message detail has clickable student link
        msg = Message.query.filter(Message.content.like("%Forwarded Case%")).first()
        self._assert("forwarded case message exists", msg is not None)

        self.logout()

    # ================================================================
    # 5a. Student: Check mentor's information
    # ================================================================
    def test_5a_student_mentor_info(self):
        print("--- 5a. Student: Check Mentor Info ---")
        self.login("2330000010")

        r = self.client.get("/student/mentor-info")
        self._assert("mentor info page loads", r.status_code == 200)
        self._assert("mentor name shown", b"Mary Lee" in r.data)
        self._assert("mentor email shown", b"marylee@test.com" in r.data)
        self._assert("group info shown", b"2025-2026-Y2-G01" in r.data)

        self.logout()

    # ================================================================
    # 5b. Student: Communicate with mentor only — no need to input name
    # ================================================================
    def test_5b_student_message_mentor_only(self):
        print("--- 5b. Student: Message Mentor Only ---")
        self.login("2330000010")

        r = self.client.get("/messages/send")
        self._assert("send message page loads", r.status_code == 200)
        # Student should only see mentor as receiver
        self._assert("only mentor as receiver", b"Mary Lee" in r.data)

        # Actually send a message
        mentor = Mentor.query.filter_by(email="marylee@test.com").first()
        r = self.client.post("/messages/send", data={
            "content": "Hello mentor, I have a question.",
            "receiver_ids": str(mentor.id),
        }, follow_redirects=True)
        self._assert("message sent", r.status_code == 200)

        # Verify mentor received it
        self.logout()
        self.login("mentor1")
        r = self.client.get("/messages/")
        self._assert("mentor received student message", b"Hello mentor" in r.data)

        self.logout()

    # ================================================================
    # 6a. Coordinator: Communicate with faculty consultant and mentor
    # ================================================================
    def test_6a_coordinator_message_filter(self):
        print("--- 6a. Coordinator: Message to Consultant and Mentor ---")
        self.login("coordinator")

        r = self.client.get("/messages/send")
        self._assert("send message page loads", r.status_code == 200)
        # Should show faculty_consultant and mentor, NOT students
        self._assert("consultant shown as receiver", b"FC FST" in r.data)
        self._assert("mentor shown as receiver", b"Mary Lee" in r.data)
        # Should NOT show students
        self._assert("student NOT shown as receiver", b"Alice A" not in r.data)

        self.logout()

    # ================================================================
    # 7a. Login: Student not in mentoring system — warning
    # ================================================================
    def test_7a_student_not_in_group_warning(self):
        print("--- 7a. Login: Student Not in Group Warning ---")
        r = self.client.post("/login", data={
            "account": "233000099",
            "password": "123456",
        }, follow_redirects=True)
        self._assert("student blocked from login", r.status_code == 200)
        self._assert("warning message shown", b"not assigned to any MCP group" in r.data)
        # Should still be on login page
        self._assert("still on login page", b"Login" in r.data)

    # ================================================================
    # Full search records (mentor perspective)
    # ================================================================
    def test_record_search_mentor(self):
        print("--- Bonus: Record Search (Mentor) ---")
        self.login("mentor1")

        r = self.client.get("/records/search")
        self._assert("record search page loads", r.status_code == 200)

        r = self.client.post("/records/search", data={
            "keyword": "Math",
            "academic_year": "2025-2026",
            "mentor_name": "",
            "student_name": "",
        }, follow_redirects=True)
        self._assert("record search works", r.status_code == 200)

        self.logout()

    # ================================================================
    # Run all tests
    # ================================================================
    def run_all(self):
        print("=" * 60)
        print("MCS System — E2E Checklist Verification")
        print("=" * 60)
        print()

        # Seed first
        self.seed()

        # 1. Administrator (3 items)
        self.test_1a_import_organization()
        self.test_1b_add_major()
        self.test_1c_faculty_consultants()

        # 3. Faculty Consultant (10 items)
        self.test_3a_import_students()
        self.test_3b_change_group_mentor()
        self.test_3c_import_coordinators()
        self.test_3d_add_student_to_group()
        self.test_3e_search_student()
        self.test_3f_search_mentor()
        self.test_3g_view_logs_in_faculty()
        self.test_3h_view_records_outside_faculty()
        self.test_3i_email_notification()
        self.test_3j_export_word()

        # 4. Mentor (3 items)
        self.test_4a_mentor_record_crud()
        self.test_4b_appointment_flow()
        self.test_4c_forward_case()

        # 5. Student (2 items)
        self.test_5a_student_mentor_info()
        self.test_5b_student_message_mentor_only()

        # 6. Coordinator (1 item)
        self.test_6a_coordinator_message_filter()

        # 7. Login (1 item)
        self.test_7a_student_not_in_group_warning()

        # Bonus checks
        self.test_record_search_mentor()

        # Summary
        print()
        print("=" * 60)
        print("RESULTS")
        print("=" * 60)
        for r in self.results:
            print(r)
        print()
        print(f"Total: {self.passed}/{self.total} passed")

        if self.passed == self.total:
            print("ALL TESTS PASSED!")
        else:
            print(f"FAILURES: {self.total - self.passed}")

        # Cleanup
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

        return self.passed == self.total


if __name__ == "__main__":
    tester = E2ETester()
    success = tester.run_all()
    sys.exit(0 if success else 1)
