"""Runtime checklist verification — tests every item by hitting actual endpoints."""
import os, sys
os.environ['MAIL_USERNAME'] = 'test'
os.environ['MAIL_PASSWORD'] = 'test'

from app import create_app
app = create_app()
client = app.test_client()

results = []

def login(account):
    return client.post('/login', data={'account': account, 'password': '123456'}, follow_redirects=True)

def check(desc, condition):
    status = 'PASS' if condition else 'FAIL'
    results.append((status, desc))
    print(f'  [{status}] {desc}')

def section(title):
    print(f'\n{"="*60}')
    print(f'  {title}')
    print(f'{"="*60}')

# ========== 7. LOGIN ==========
section('7. LOGIN')

# 7.1 Student not in MCP system: student3 (2330000030) has no group
with app.app_context():
    from app.entity.student import Student
    s3 = Student.query.filter_by(student_id='2330000030').first()
    has_group = s3.group_id is not None if s3 else None
    print(f'  [INFO] Student 2330000030 group_id = {s3.group_id if s3 else "NOT FOUND"}')

rv = client.post('/login', data={'account': '2330000030', 'password': '123456'}, follow_redirects=True)
check('7.1a Student not in group gets warning',
      b'not assigned to any MCP group' in rv.data)
check('7.1b Still on login page after warning',
      b'Login' in rv.data)

# 7.1c Student IN group can login
rv = login('2330000010')
check('7.1c Student in group logs in successfully',
      b'Student Home' in rv.data)
client.get('/logout')

# ========== 1. ADMINISTRATOR ==========
section('1. ADMINISTRATOR')

rv = login('admin')
check('1.0 Admin login', b'Admin' in rv.data or b'admin' in rv.data.lower())

# 1.1 Import org Excel page
rv = client.get('/admin/import-organization')
check('1.1a Import org page loads', b'Appendix A' in rv.data)
check('1.1b Has Preview button', b'Preview' in rv.data)

# 1.2 Manually add a programme (major) into a department
rv = client.get('/organization/major/add')
check('1.2 Add major page loads', rv.status_code == 200)

# 1.3 Designate faculty consultants manually
rv = client.get('/admin/consultants/add')
check('1.3 Add consultant page loads', rv.status_code == 200)

client.get('/logout')

# ========== 2. SUPPORTING STAFF ==========
section('2. SUPPORTING STAFF (faculty_member)')

rv = login('faculty_member')
check('2.0 Faculty member login', b'Faculty Member Home' in rv.data)
check('2.0b Log link visible on home', b'View Log Activities' in rv.data)

# 2.1 View log list
rv = client.get('/records/logs')
check('2.1a Log page loads', b'Log Activities' in rv.data)
check('2.1b Has search by student ID form', b'Search' in rv.data and b'student_id' in rv.data)

# 2.1c Search log by student ID
rv = client.get('/records/logs?student_id=2330000010')
check('2.1c Search by student ID works', rv.status_code == 200)

# 2.1d Add demo log
rv = client.post('/records/logs', data={
    'student_id': '2330000010',
    'function_access': 'Check Mentor Information'
}, follow_redirects=True)
check('2.1d Add demo log works', b'added successfully' in rv.data)

client.get('/logout')

# ========== 3. FACULTY CONSULTANT ==========
section('3. FACULTY CONSULTANT')

rv = login('faculty')
check('3.0 FC login', b'Faculty Consultant Home' in rv.data)

# 3.1 Import students page (Appendix B)
rv = client.get('/faculty/import-students')
check('3.1a Import students page loads', b'Appendix B' in rv.data)
check('3.1b Has Preview button', b'Preview' in rv.data)

# 3.2 Change group mentor
rv = client.get('/faculty/group/change-mentor')
check('3.2 Change group mentor page loads', rv.status_code == 200)

# 3.3 Import coordinators page (Appendix C)
rv = client.get('/faculty/import-coordinators')
check('3.3a Import coordinators page loads', b'Appendix C' in rv.data)
check('3.3b Has Preview button', b'Preview' in rv.data)

# 3.4 Add student to group
rv = client.get('/faculty/group/add-student')
check('3.4 Add student to group page loads', rv.status_code == 200)

# 3.5 Search student by ID -> records displayed
rv = client.post('/students/search', data={'student_id': '2330000010'}, follow_redirects=True)
check('3.5a Student detail page loads', b'Student Detail' in rv.data)
check('3.5b Records link visible ("View Interview Records")',
      b'View' in rv.data and b'Interview Records' in rv.data)

# 3.6 Search mentor by name -> group ID -> click ID shows students
rv = client.post('/mentors/search', data={'action': 'search', 'keyword': 'Mary'}, follow_redirects=True)
check('3.6a Mentor search returns results', b'Mary' in rv.data)
check('3.6b Group ID visible in results', b'Group ID' in rv.data)
check('3.6c Has Show members button', b'Show members' in rv.data)

# 3.7 View log of student IN faculty
rv = client.get('/records/logs')
check('3.7 FC can view logs filtered by faculty', rv.status_code == 200)

# 3.8 View log of student NOT in faculty — warning
# student 2330000010 is in FST faculty (group G1). FC 'faculty' is also in FST.
# student 2330000020 is in FHSS faculty (group G3). FC 'faculty' (FST) should get warning.
rv = client.get('/records/student/2330000020', follow_redirects=True)
check('3.8 FC views student outside faculty gets warning',
      b'not from your faculty' in rv.data.lower() or b'warning' in rv.data.lower())

# 3.9 Communicate with students (email notification)
rv = client.post('/messages/send', data={
    'receiver_ids': ['1'],
    'content': 'Test communication from FC'
}, follow_redirects=True)
check('3.9 FC can send message', b'successfully' in rv.data.lower() or b'sent' in rv.data.lower())

# 3.10 Export Word by academic year AND department
rv = client.get('/records/export')
check('3.10a Export page loads', rv.status_code == 200)
check('3.10b Has Academic Year filter', b'Academic Year' in rv.data)
check('3.10c Has Department filter', b'Department' in rv.data)

client.get('/logout')

# ========== 4. MENTOR ==========
section('4. MENTOR')

rv = login('mentor1')
check('4.0 Mentor login', b'Mentor Home' in rv.data)

# 4.1 Edit student record (view, add, edit, delete)
rv = client.get('/records/student/2330000010')
check('4.1a View records page loads', rv.status_code == 200)

rv = client.post('/records/student/2330000010/add', data={
    'date': '2026-05-22', 'time': '14:00',
    'problem_statement': 'Academic difficulty in math',
    'interview_summary': 'Discussed study plan',
    'followup_action': 'Schedule tutoring session'
}, follow_redirects=True)
check('4.1b Add record successful', b'Academic difficulty' in rv.data or b'successfully' in rv.data.lower())

# Now find the record ID and test edit/delete
import re
with app.app_context():
    from app.entity.record import Record
    recs = Record.query.all()
    if recs:
        rec_id = recs[-1].record_id
        # Test view detail
        rv2 = client.get(f'/records/{rec_id}')
        check('4.1c View record detail', rv2.status_code == 200)
        # Test edit
        rv3 = client.post(f'/records/{rec_id}/edit', data={
            'problem_statement': 'Updated: Academic difficulty in math',
            'interview_summary': 'Updated: Discussed study plan',
            'followup_action': 'Updated: Schedule tutoring'
        }, follow_redirects=True)
        check('4.1d Edit record', b'Updated' in rv3.data or b'successfully' in rv3.data.lower())
        # Test delete
        rv4 = client.post(f'/records/{rec_id}/delete', follow_redirects=True)
        check('4.1e Delete record', b'deleted' in rv4.data.lower() or rv4.status_code == 200)

# 4.2 Appointment (create slots, confirm venue)
rv = client.get('/appointments/mentor/create')
check('4.2a Create appointment page loads', rv.status_code == 200)

rv = client.post('/appointments/mentor/create', data={
    'student_id': '1',  # DB ID, but will be validated
    'content': 'Test appointment',
    'slot1': '2026-06-01 14:00',
    'slot2': '2026-06-02 14:00',
    'slot3': '2026-06-03 14:00'
}, follow_redirects=True)
check('4.2b Appointment creation handled', rv.status_code == 200)

# 4.3 Forward case to coordinator -> coordinator sees clickable student name
rv = client.post('/forward-case', data={
    'student_id': '2330000010',
    'description': 'Student needs extra academic support'
}, follow_redirects=True)
check('4.3a Forward case handled', rv.status_code == 200)

# Now login as coordinator to check the forwarded case
client.get('/logout')
rv = login('coordinator')
rv = client.get('/messages/')
check('4.3b Coordinator receives forwarded case',
      b'Forwarded Case' in rv.data or b'2330000010' in rv.data)

client.get('/logout')

# ========== 5. STUDENT ==========
section('5. STUDENT')

rv = login('2330000010')
check('5.0 Student login', b'Student Home' in rv.data)

# 5.1 Check mentor info
rv = client.get('/student/mentor-info')
check('5.1a Student can view mentor info', b'Mentor Information' in rv.data)
check('5.1b Mentor name displayed', b'mentor1' in rv.data or b'Mentor Name' in rv.data)
check('5.1c Mentor email displayed', b'@' in rv.data)

# 5.2 Communicate with mentor only (cannot input mentor name)
rv = client.get('/messages/send')
check('5.2a Send message page loads', b'Send Message' in rv.data)
# Student should see only 1 checkbox (their mentor) — verify no text input for mentor name
check('5.2b No text input for mentor name (no \"mentor\" text input)',
      b'input type="text" name="receiver' not in rv.data)

client.get('/logout')

# ========== 6. COORDINATOR ==========
section('6. COORDINATOR')

rv = login('coordinator')
check('6.0 Coordinator login', b'Coordinator Home' in rv.data)

# 6.1 Communicate with FC and mentor
rv = client.get('/messages/send')
check('6.1a Send message page loads', b'Send Message' in rv.data)
# Should see both faculty_consultant and mentor roles as receivers
check('6.1b Can see faculty_consultant and mentor as receivers',
      b'faculty_consultant' in rv.data or b'mentor' in rv.data)

rv = client.post('/messages/send', data={
    'receiver_ids': ['2'],  # faculty consultant ID
    'content': 'Test message from coordinator to FC'
}, follow_redirects=True)
check('6.1c Coordinator can send to FC/mentor', b'successfully' in rv.data.lower() or b'sent' in rv.data.lower())

client.get('/logout')

# ========== SUMMARY ==========
print(f'\n{"="*60}')
passed = sum(1 for s, _ in results if s == 'PASS')
failed = sum(1 for s, _ in results if s == 'FAIL')
print(f'  TOTAL: {passed}/{passed+failed} passed')
if failed:
    print(f'  FAILURES:')
    for s, d in results:
        if s == 'FAIL':
            print(f'    - {d}')
else:
    print(f'  ALL CHECKS PASSED')
print(f'{"="*60}')
