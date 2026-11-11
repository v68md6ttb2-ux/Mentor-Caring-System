"""Enumeration types used across entities."""

import enum


class MessageStatus(enum.Enum):
    Unrespond = "Unrespond"
    Read = "Read"
    Respond = "Respond"


class AppointmentStatus(enum.Enum):
    Requested = "Requested"
    Slot_Selected = "Slot_Selected"
    Confirmed = "Confirmed"
    Cancelled = "Cancelled"
