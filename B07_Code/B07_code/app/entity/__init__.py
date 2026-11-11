"""Entity objects — pure ORM definitions in dependency order."""

from app.entity.enums import MessageStatus, AppointmentStatus
from app.entity.user import User, FacultyMember
from app.entity.faculty import Faculty, OrganizationUnit, UnitInfo
from app.entity.department import Department
from app.entity.major import Major
from app.entity.mcp_group import MCPGroup
from app.entity.student import Student, MCPInfo
from app.entity.mentor import Mentor
from app.entity.coordinator import Coordinator, CoordinatorInfo
from app.entity.faculty_consultant import FacultyConsultant
from app.entity.record import Record, WordFile, LogActivity, word_file_records
from app.entity.message import Message
from app.entity.appointment import Appointment
