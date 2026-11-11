# Mentor Caring System (MCS)

BNBU Mentor Caring System, built with Flask, SQLAlchemy, and SQLite. The project follows a strict three-layer MVC architecture.

---

## Project Structure

```text
P1ANDP4/
├── teamwork.py                         # Application entry point
├── seed_data.py                        # Seed data script for creating the demo database
├── test_e2e.py                         # End-to-end functional tests, 84 tests
├── requirements.txt                    # Python dependencies
│
├── app/
│   ├── __init__.py                     # Flask app factory and 9 Blueprint registrations
│   ├── extensions.py                   # db (SQLAlchemy) and login_manager (Flask-Login)
│   │
│   ├── config/
│   │   └── secure.py                   # Application configuration: database URI, SECRET_KEY, SMTP mail
│   │
│   ├── entity/                         # Pure ORM entity models, 13 files
│   │   ├── enums.py                    # MessageStatus, AppointmentStatus
│   │   ├── user.py                     # User, FacultyMember
│   │   ├── faculty.py                  # Faculty, OrganizationUnit, UnitInfo
│   │   ├── department.py               # Department
│   │   ├── major.py                    # Major
│   │   ├── mcp_group.py                # MCPGroup
│   │   ├── student.py                  # Student, MCPInfo
│   │   ├── mentor.py                   # Mentor
│   │   ├── coordinator.py              # Coordinator, CoordinatorInfo
│   │   ├── faculty_consultant.py       # FacultyConsultant
│   │   ├── record.py                   # Record, WordFile, LogActivity
│   │   ├── message.py                  # Message
│   │   └── appointment.py              # Appointment
│   │
│   ├── mapper/                         # Data access layer, 8 files
│   │   ├── user_mapper.py              # UserMapper, StudentMapper, FacultyMemberMapper
│   │   ├── student_mapper.py           # Student-specific queries, MCPInfoImportMapper
│   │   ├── mentor_mapper.py            # MentorMapper, CoordinatorMapper, FacultyConsultantMapper
│   │   ├── appointment_mapper.py       # AppointmentMapper
│   │   ├── message_mapper.py           # MessageMapper with SMTP notification support
│   │   ├── record_mapper.py            # RecordMapper, WordFileMapper, LogMapper, RecordExportMapper
│   │   ├── mcp_group_mapper.py         # GroupMapper
│   │   └── organization_mapper.py      # FacultyMapper, DepartmentMapper, MajorMapper, OrganizationImportMapper
│   │
│   ├── control/                        # Business logic layer, 8 files
│   │   ├── auth_control.py             # Login, logout, password change, current user lookup
│   │   ├── organization_control.py     # Organization CRUD, Excel preview, and import
│   │   ├── mentor_allocation_control.py # Group, mentor, student, and faculty consultant management
│   │   ├── record_control.py           # Interview record CRUD, search, and permission control
│   │   ├── report_control.py           # Export conditions and Word file generation
│   │   ├── message_control.py          # Message sending, inbox, detail view, and reply
│   │   ├── appointment_control.py      # Appointment creation, time-slot selection, confirmation, cancellation
│   │   └── log_control.py              # Log activity management and filtering
│   │
│   ├── boundary/                       # HTTP routing layer, Flask Blueprints, 9 files
│   │   ├── auth_boundary.py            # Login, logout, password change, faculty member homepage
│   │   ├── admin_boundary.py           # Admin organization management and Excel import
│   │   ├── consultant_boundary.py      # Faculty consultant group, student, mentor, and coordinator workflows
│   │   ├── mentor_boundary.py          # Mentor homepage and case referral to coordinator
│   │   ├── coordinator_boundary.py     # Coordinator homepage and case referral to faculty consultant
│   │   ├── student_boundary.py         # Student homepage and mentor information
│   │   ├── message_boundary.py         # Message sending, inbox, details, and replies
│   │   ├── appointment_boundary.py     # Appointment creation, time-slot choice, confirmation, cancellation
│   │   └── report_boundary.py          # Record CRUD, search, Word export, and log viewing
│   │
│   ├── templates/                      # Jinja2 HTML templates, 30+ files
│   └── static/                         # Static assets
```

---

## Three-Layer Calling Chain

```text
HTTP Request
    |
    v
Boundary (Flask Blueprint routes)
- validates input
- renders templates
- flashes messages
- imports only app.control.*

    |
    v
Control (Business logic)
- coordinates workflows
- checks permissions
- creates entity objects
- imports only app.mapper.* and app.entity.*

    |
    v
Mapper (Data access)
- runs ORM queries
- handles transactions
- persists data
- imports only app.entity.* and app.extensions

    |
    v
Entity (Data models)
- defines SQLAlchemy models
- imports only app.extensions

    |
    v
Database (SQLite)
```

---

## Architecture Rules

| Rule | Description |
|------|-------------|
| Boundary -> Control only | Boundary calls Control only; it does not directly call Mapper or Entity. |
| Control -> Mapper only | Control does not directly use `db.session` or `.query`; all data operations go through Mapper. |
| Mapper has no web dependency | Mapper does not import `flask_login` and does not handle HTTP requests. |
| Entity is data-only | Entity defines fields and `db.relationship` only, without business logic. |

---

## Requirements

- Python 3.12+
- pip

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Database Initialization

```bash
python seed_data.py
```

This creates the SQLite database `instance/mcs.db` and fills it with demo seed data, including test users and the organization structure.

---

## Start the Application

```bash
python teamwork.py
```

Open the application at:

```text
http://127.0.0.1:5000
```

---

## Test Accounts

| Role | Username | Password | Notes |
|------|----------|----------|-------|
| Admin | admin | 123456 | |
| Faculty Consultant (FST) | faculty | 123456 | |
| Faculty Member | faculty_member | 123456 | |
| Mentor | mentor1 | 123456 | Mentor Mary Lee, FST |
| Mentor | mentor2 | 123456 | Mentor John Wang, FST |
| Mentor | mentor3 | 123456 | Mentor Alice Chen, FHSS |
| Coordinator | coordinator | 123456 | DCS department |
| Student | 2330000010 | 123456 | FST/CST, group G01 |
| Student | 2330000020 | 123456 | FHSS/COMM, group G03, cross-faculty test case |
| Student | 2330000030 | 123456 | No assigned group, login warning test case |

---

## Student ID Format

Student IDs must be exactly 10 digits, for example `2330000010`.

The system performs backend validation in 3 Boundary files using `isdigit()` and length checking. It also performs frontend HTML5 validation in 2 forms using `pattern="\d{10}"`.

---

## Run Tests

```bash
python test_e2e.py
```

The test suite contains 84 end-to-end tests covering all 7 roles and 21 functional requirements.

---

## Mail Notification

The system sends mail notifications through SMTP. Configure the mail server with environment variables:

| Environment Variable | Default Value |
|----------------------|---------------|
| `MAIL_SERVER` | `smtp.qq.com` |
| `MAIL_PORT` | `587` |
| `MAIL_USERNAME` | empty |
| `MAIL_PASSWORD` | empty |
| `MAIL_DEFAULT_SENDER` | `noreply@bnbu.edu.cn` |

If SMTP credentials are not configured, mail sending fails silently and does not affect the rest of the system.

---

## Functional Coverage

| Role | Functions |
|------|-----------|
| Admin | Import organization Excel files with preview and confirmation, manually add majors, manually assign faculty consultants. |
| Supporting Staff | View activity logs by student ID, including login, communication, and mentor information access. |
| Faculty Consultant | Import student and coordinator Excel files, change group mentors, add students to groups, search students and mentors, view logs with cross-faculty warnings, send messages with mail notifications, export Word reports. |
| Mentor | Create, read, update, and delete student interview records; create appointment time slots; confirm appointment location; refer cases to coordinators with clickable student links. |
| Student | View mentor information and communicate only with the assigned mentor, without manually entering names. |
| Coordinator | Communicate with faculty consultants and mentors, and refer cases to faculty consultants. |
| Login | Students outside the mentoring system receive a warning after login; the warning disappears after the student is imported into the mentoring list. |

