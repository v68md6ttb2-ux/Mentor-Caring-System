# MCS (Mentor Caring System) — Checklist & Architecture Verification Report

**Date**: 2026-05-22
**Test Status**: 84/84 E2E tests passed | 52/52 runtime verification checks passed
**Student ID Format**: 10-digit numeric (e.g., `2330000010`)
**Architecture**: Three-tier MVC (Boundary → Control → Mapper → Entity)

---

## Part A: Architecture Compliance

### Directory Structure

```
P1ANDP4/
├── teamwork.py                    (root entry point)
├── app/
│   ├── __init__.py               (Flask app factory, blueprint registration)
│   ├── extensions.py             (db, login_manager — framework infrastructure)
│   ├── config/secure.py          (application configuration)
│   ├── entity/                   (13 files — pure ORM entity objects)
│   ├── mapper/                   (8 files — data access layer)
│   ├── control/                  (8 files — business logic layer)
│   ├── boundary/                 (9 files — HTTP route/Flask Blueprint layer)
│   ├── templates/                (HTML Jinja2 templates)
│   └── static/                   (static assets)
```

### Layer Dependency Verification

| Layer | Imports From | Status |
|-------|-------------|--------|
| **Boundary** (9 files) | `app.control.*` only | ✅ Clean — 0 mapper/entity imports |
| **Control** (8 files) | `app.mapper.*`, `app.control.*` (cross-control), `app.entity.*` (object creation only) | ✅ Clean — 0 `db.session` operations |
| **Mapper** (8 files) | `app.entity.*`, `app.extensions` | ✅ Clean — 0 flask_login/web dependencies (except `current_app` for email config) |
| **Entity** (13 files) | `app.extensions`, `flask_login` (UserMixin only) | ✅ Clean — 0 business logic or web dependencies |

### Call Chain (every request follows this path)

```
HTTP Request
    ↓
Boundary (Flask route — validates input, renders templates)
    ↓
Control (business logic — orchestrates operations)
    ↓
Mapper (data access — queries, persistence)
    ↓
Entity (SQLAlchemy models — data structure)
    ↓
Database
```

### Architecture Rules Enforced

1. **Boundary** never imports Mapper or Entity directly — all data access goes through Control
2. **Control** never calls `db.session.add/commit/delete/flush` — all persistence goes through Mapper
3. **Control** never calls `.query.filter()` directly — all queries go through Mapper
4. **Mapper** never imports from Boundary or Control — no upward dependencies
5. **Mapper** never calls Flask request/response functions — no web framework coupling
6. **Entity** contains only data structure definitions and `db.relationship` declarations

### Input Validation: Student ID

Student ID is validated as **10-digit numeric** at 3 boundary points:

| Boundary File | Validation | Error Message |
|--------------|-----------|---------------|
| `consultant_boundary.py:18` | `isdigit() and len() == 10` | "Student ID must be 10 digits." |
| `mentor_boundary.py:12` | `isdigit() and len() == 10` | "Student ID must be 10 digits." |
| `coordinator_boundary.py:12` | `isdigit() and len() == 10` | "Student ID must be 10 digits." |

HTML5 client-side validation via `pattern="\d{10}"` in `forward_case.html` and `forward_case_to_consultant.html`.

---

## Part B: Checklist Verification

### 1. Administrator

| # | Requirement | Implementation | File Reference |
|---|------------|---------------|----------------|
| 1.1 | Import organization Excel (show content first, then import) | Preview → Confirm two-step flow. Template shows **Faculty \| Department \| Major** preview table matching Appendix A format | `admin_boundary.py:144-175`, `organization_control.py:49-68`, `import_org.html` |
| 1.2 | Manually add a new programme into a department | Form with department dropdown, validates name uniqueness | `admin_boundary.py:67-81`, `organization_control.py:35-46` |
| 1.3 | Designate faculty consultants manually | Form with faculty dropdown, creates FacultyConsultant with account/password/name/email | `admin_boundary.py:94-111`, `mentor_allocation_control.py:163-195` |

### 2. Supporting Staff (faculty_member role)

| # | Requirement | Implementation | File Reference |
|---|------------|---------------|----------------|
| 2.1 | View student log by student ID | Log page with student ID search filter; logs filtered by faculty scope; displays **Log ID \| Student \| Login \| Logout \| Function Access** | `report_boundary.py:174-203`, `log_control.py:7-28`, `log_list.html` |

### 3. Faculty Consultant

| # | Requirement | Implementation | File Reference |
|---|------------|---------------|----------------|
| 3.1 | Import students' name list (preview → import) | Preview → Confirm flow with **Student ID \| Name \| Major \| Status \| Group ID \| Mentor \| Office \| Email** table matching Appendix B | `consultant_boundary.py:127-158`, `mentor_allocation_control.py:228-250`, `import_students.html` |
| 3.2 | Change the mentor of a group | Select group + new mentor → updates `group.mentor_id` | `consultant_boundary.py:37-52`, `mentor_allocation_control.py:80-93` |
| 3.3 | Designate MCP coordinator via Excel (preview → import) | Preview → Confirm flow with **Name \| Email \| Department \| Account** table matching Appendix C | `consultant_boundary.py:161-192`, `mentor_allocation_control.py:254-274`, `import_coordinators.html` |
| 3.4 | Add one student to a group | Select student + group → sets `student.group_id` | `consultant_boundary.py:55-70`, `mentor_allocation_control.py:96-110` |
| 3.5 | Search student by ID (records displayed) | 10-digit ID search → student detail page with "View Interview Records" link → record list | `consultant_boundary.py:89-124`, `student_detail.html:74-98` |
| 3.6 | Search mentor by name (show group ID, click ID → student list) | Search by name/email/group ID → table with clickable student IDs linking to `student_detail` | `consultant_boundary.py:195-232`, `mentor_search.html:121-125` |
| 3.7 | View log of student IN faculty | Logs filtered via `LogMapper.find_by_faculty(faculty_id)` joining Student → Group → Major → Department | `report_boundary.py:187-188`, `record_mapper.py:164-169` |
| 3.8 | View log of student NOT in faculty (warning) | `can_current_user_view_student_records()` checks `student_fac_id == consultant_faculty_id`; flashes warning if mismatch | `report_boundary.py:22-27`, `record_control.py:50-58` |
| 3.9 | Communicate with students (student gets email) | SMTP email via `smtplib` with `[MCS] New message from {sender}` subject; `_notify_by_email()` called on send and reply | `message_mapper.py:152-188` |
| 3.10 | Export Word by academic year AND department | Multi-select academic year list + department dropdown → generates .docx with conditions header | `report_boundary.py:132-157`, `export_records.html`, `record_mapper.py:225-245` |

### 4. Mentor

| # | Requirement | Implementation | File Reference |
|---|------------|---------------|----------------|
| 4.1 | Edit student record (save, view, delete) | Full CRUD: `add_record_page`, `edit_record_page`, `delete_record_page`, `record_detail`; only mentor can edit (coordinator/FC read-only) | `report_boundary.py:37-109`, `record_control.py:69-73` |
| 4.2 | Make appointment (30-min slots, venue confirmation, notify) | Mentor creates 3 time slots (format: `YYYY-MM-DD HH:MM`, each +30min); student chooses slot; mentor inputs venue and confirms | `appointment_boundary.py:35-83`, `appointment_mapper.py:62-119`, `appointment_mentor.html` |
| 4.3 | Forward case to coordinator (clickable student name → records) | Creates `[Forwarded Case] Student: {ID} {Name}` message; coordinator sees highlighted box with clickable student name linking to `student_detail` → records | `mentor_boundary.py:22-49`, `mentor_mapper.py:59-75`, `message_detail.html:23-36` |

### 5. Student

| # | Requirement | Implementation | File Reference |
|---|------------|---------------|----------------|
| 5.1 | Check mentor's information | Displays student info, organization, MCP group, and **Mentor (Name, Email, Office)** | `student_boundary.py:17-27`, `student_mentor_info.html` |
| 5.2 | Communicate with mentor only (no name input) | `get_available_receivers()` returns only `[student.group.mentor]`; student sees single checkbox, cannot type names | `message_control.py:10-15`, `message_send.html` |

### 6. Coordinator

| # | Requirement | Implementation | File Reference |
|---|------------|---------------|----------------|
| 6.1 | Communicate with FC and mentor (show they get info) | Receivers = `["faculty_consultant", "mentor"]` roles; email notification sent via SMTP | `message_control.py:16-17`, `message_mapper.py:152-188` |

### 7. Login

| # | Requirement | Implementation | File Reference |
|---|------------|---------------|----------------|
| 7.1 | Student not in MCP system → warning; after import → no warning | `is_in_group()` check on login; flashes "You are not assigned to any MCP group" and blocks login; after student added to group → login succeeds | `auth_boundary.py:28-32` |

---

## Part C: Summary

### Checklist Status

| Role | Items | Status |
|------|-------|--------|
| Administrator | 3 | ✅ All implemented |
| Supporting Staff | 1 | ✅ All implemented |
| Faculty Consultant | 10 | ✅ All implemented |
| Mentor | 3 | ✅ All implemented |
| Student | 2 | ✅ All implemented |
| Coordinator | 1 | ✅ All implemented |
| Login | 1 | ✅ All implemented |
| **Total** | **21** | **21/21 ✅** |

### Architecture Status

| Check | Result |
|-------|--------|
| Boundary → Mapper violations | **0** |
| Boundary → Entity violations | **0** |
| Control → db.session violations | **0** |
| Control → direct .query violations | **0** |
| Mapper → flask_login violations | **0** |
| Strict three-tier call chain | ✅ Boundary → Control → Mapper → Entity |
| E2E Tests | **84/84 passed** |
| Runtime Verification | **52/52 passed** (verify_checklist_runtime.py) |

### Seed Data Structure

| Faculty | Department | Major | Group | Mentor | Students |
|---------|-----------|-------|-------|--------|----------|
| FST | DCS | CST | G01 | mentor1 (Mary Lee) | 2330000010 |
| FST | DCS | AI | G02 | mentor2 (John Wang) | (empty) |
| FHSS | DCOMM | COMM | G03 | mentor3 (Alice Chen) | 2330000020 |
| — | — | — | — | — | 2330000030 (no group) |
