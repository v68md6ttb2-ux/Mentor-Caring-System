"""Time helpers for the Mentor Caring System.

All system-generated timestamps are stored as naive datetimes in the
application timezone used by the coursework/demo environment. This avoids
saving UTC while the UI displays the values as local China time.

Important: this file intentionally does NOT use zoneinfo.ZoneInfo("Asia/Shanghai").
On some Windows Python installations, the IANA timezone database is not installed,
which raises ZoneInfoNotFoundError. A fixed UTC+8 offset is enough for China time
because China does not use daylight saving time.
"""

from datetime import datetime, timedelta, timezone

# China Standard Time, UTC+8. China has no daylight-saving switch in this project.
CHINA_TZ = timezone(timedelta(hours=8), name="CST")


def local_now():
    """Return current China local time as a naive datetime for SQLAlchemy."""
    return datetime.now(CHINA_TZ).replace(tzinfo=None)


def local_now_iso():
    """Return current China local time in ISO format for JSON fields."""
    return local_now().isoformat()
