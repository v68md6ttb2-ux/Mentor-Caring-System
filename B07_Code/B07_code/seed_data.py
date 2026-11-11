import os

from app import create_app
from app.extensions import db
from app.entity import (
    User,
    Faculty,
    Department,
    Major,
    Mentor,
    Coordinator,
    FacultyConsultant,
    MCPGroup,
    Student,
)
from app.entity.user import FacultyMember

app = create_app()


def seed_data():
    with app.app_context():
        os.makedirs("instance", exist_ok=True)

        # Warning: this will delete all existing data.
        db.drop_all()
        db.create_all()

        # -------------------------
        # Organization
        # -------------------------
        fst = Faculty(name="FST")
        fhss = Faculty(name="FHSS")
        fsm = Faculty(name="FSM")
        dcc = Faculty(name="DCC")

        db.session.add_all([fst, fhss, fsm, dcc])
        db.session.flush()

        dcs = Department(name="DCS", faculty_id=fst.id)
        dcomm = Department(name="DCOMM", faculty_id=fhss.id)
        db.session.add_all([dcs, dcomm])
        db.session.flush()

        cst = Major(name="CST", department_id=dcs.id)
        ai = Major(name="AI", department_id=dcs.id)
        comm = Major(name="COMM", department_id=dcomm.id)

        db.session.add_all([cst, ai, comm])
        db.session.flush()

        # -------------------------
        # Users (joined-table inheritance: subclasses ARE users)
        # -------------------------
        admin_user = User(
            account="admin",
            password="123456",
            name="System Admin",
            email="admin@bnbu.edu.cn",
            role="admin",
        )

        faculty_consultant = FacultyConsultant(
            account="faculty",
            password="123456",
            name="Faculty Consultant",
            email="faculty@bnbu.edu.cn",
            role="faculty_consultant",
            faculty_id=fst.id,
        )

        mentor1 = Mentor(
            account="mentor1",
            password="123456",
            name="Mary Lee",
            email="marylee@bnbu.edu.cn",
            role="mentor",
            mentor_id="M001",
            office="T1-102",
        )

        mentor2 = Mentor(
            account="mentor2",
            password="123456",
            name="John Wang",
            email="johnwang@bnbu.edu.cn",
            role="mentor",
            mentor_id="M002",
            office="T1-103",
        )

        mentor3 = Mentor(
            account="mentor3",
            password="123456",
            name="Alice Chen",
            email="alicechen@bnbu.edu.cn",
            role="mentor",
            mentor_id="M003",
            office="T2-201",
        )

        faculty_member = FacultyMember(
            account="faculty_member",
            password="123456",
            name="Supporting Staff",
            email="staff@bnbu.edu.cn",
            role="faculty_member",
            faculty_id=fst.id,
        )

        coordinator = Coordinator(
            account="coordinator",
            password="123456",
            name="Ruth Mo",
            email="ruthmo@bnbu.edu.cn",
            role="coordinator",
            department_id=dcs.id,
        )

        db.session.add_all([
            admin_user,
            faculty_consultant,
            faculty_member,
            mentor1,
            mentor2,
            mentor3,
            coordinator,
        ])
        db.session.flush()

        # -------------------------
        # MCP Groups
        # -------------------------
        group1 = MCPGroup(
            group_id="2025-2026-Y2-G01",
            academic_year="2025-2026",
            mentor_id=mentor1.id,
            major_id=cst.id,
        )

        group2 = MCPGroup(
            group_id="2025-2026-Y2-G02",
            academic_year="2025-2026",
            mentor_id=mentor2.id,
            major_id=ai.id,
        )

        group3 = MCPGroup(
            group_id="2025-2026-Y2-G03",
            academic_year="2025-2026",
            mentor_id=mentor3.id,
            major_id=comm.id,
        )

        db.session.add_all([group1, group2, group3])
        db.session.flush()

        # -------------------------
        # Students
        # -------------------------
        student1 = Student(
            account="2330000010",
            password="123456",
            name="Bnbuer One",
            email="2330000010@bnbu.edu.cn",
            role="student",
            student_id="2330000010",
            status="Normal",
            group_id=group1.id,
        )

        student2 = Student(
            account="2330000020",
            password="123456",
            name="Bnbuer Two",
            email="2330000020@bnbu.edu.cn",
            role="student",
            student_id="2330000020",
            status="Normal",
            group_id=group3.id,
        )

        student3 = Student(
            account="2330000030",
            password="123456",
            name="Bnbuer Three",
            email="2330000030@bnbu.edu.cn",
            role="student",
            student_id="2330000030",
            status="Probation",
            group_id=None,
        )

        db.session.add_all([student1, student2, student3])

        db.session.commit()

        print("Database initialized successfully.")
        print("Test accounts:")
        print("admin / 123456")
        print("faculty / 123456")
        print("faculty_member / 123456")
        print("mentor1 / 123456")
        print("mentor2 / 123456")
        print("mentor3 / 123456")
        print("coordinator / 123456")
        print("2330000010 / 123456")
        print("2330000020 / 123456")
        print("2330000030 / 123456")


if __name__ == "__main__":
    seed_data()
