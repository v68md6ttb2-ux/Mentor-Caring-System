"""Message business logic control."""

from flask_login import current_user

from app.entity.message import Message
from app.mapper.user_mapper import UserMapper, StudentMapper
from app.mapper.message_mapper import MessageMapper


def get_available_receivers():
    if current_user.role == "student":
        student = StudentMapper.find_by_id(current_user.id)
        if student and student.group and student.group.mentor:
            return [student.group.mentor]
        return []
    if current_user.role == "coordinator":
        return UserMapper.find_by_roles(["faculty_consultant", "mentor"], exclude_id=current_user.id)
    return UserMapper.find_all_except(current_user.id)


def send_message(receiver_id_list, content, attachment=None):
    content = content.strip() if content else ""
    if not content:
        return False, "Message content cannot be empty."
    if not receiver_id_list:
        return False, "Please select at least one receiver."

    receiver_ids = []
    for rid in receiver_id_list:
        try:
            receiver_ids.append(int(rid))
        except ValueError:
            return False, "Invalid receiver."

    receivers = UserMapper.find_by_ids(receiver_ids)
    if len(receivers) != len(receiver_ids):
        return False, "One or more receivers do not exist."

    message = Message(content=content, attachment=attachment, sender_id=current_user.id)
    success = MessageMapper.send(message, current_user.id, receiver_ids)
    if not success:
        return False, "Failed to send message."
    return True, "Message sent successfully."


def get_received_messages():
    return MessageMapper.find_received_by_user(current_user.id)


def get_sent_messages():
    return MessageMapper.find_sent_by_user(current_user.id)


def get_message_detail(message_id):
    message = MessageMapper.find_by_id(message_id)
    if not message:
        return None
    if message.sender_id == current_user.id:
        return message
    receiver_ids = message.get_receiver_ids()
    if current_user.id in receiver_ids:
        return message
    return None


def mark_message_as_read(message_id):
    message = MessageMapper.find_by_id(message_id)
    if not message:
        return False, "Message not found."
    receiver_ids = message.get_receiver_ids()
    if current_user.id not in receiver_ids:
        return False, "You cannot mark this message as read."
    MessageMapper.mark_as_read(message, current_user.id)
    return True, "Message marked as read."


def reply_message(message_id, reply_content):
    reply_content = reply_content.strip() if reply_content else ""
    if not reply_content:
        return False, "Reply content cannot be empty."
    message = MessageMapper.find_by_id(message_id)
    if not message:
        return False, "Message not found."
    success = MessageMapper.respond(message, current_user.id, reply_content)
    if not success:
        return False, "You cannot reply to this message."
    return True, "Reply sent successfully."
