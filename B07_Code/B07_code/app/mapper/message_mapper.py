"""Data mapper for Message entity."""

import json
from app.utils.time_utils import local_now, local_now_iso

from app.extensions import db
from app.entity.user import User
from app.entity.message import Message
from app.entity.enums import MessageStatus


class MessageMapper:
    """Data mapper for Message entity."""

    @staticmethod
    def find_by_id(message_id):
        return Message.query.get(message_id)

    @staticmethod
    def find_received_by_user(user_id):
        all_messages = Message.query.filter(
            Message.receiver_data_json.contains(str(user_id))
        ).order_by(Message.sent_datetime.desc()).all()
        result = []
        for msg in all_messages:
            receiver_data = MessageMapper._get_receiver_data(msg)
            for entry in receiver_data:
                if str(entry["receiver_id"]) == str(user_id):
                    result.append((msg, entry))
                    break
        return result

    @staticmethod
    def find_sent_by_user(user_id):
        return (
            Message.query
            .filter_by(sender_id=user_id)
            .order_by(Message.sent_datetime.desc())
            .all()
        )

    @staticmethod
    def _get_receiver_data(message):
        try:
            return json.loads(message.receiver_data_json or "[]")
        except json.JSONDecodeError:
            return []

    @staticmethod
    def _set_receiver_data(message, data):
        message.receiver_data_json = json.dumps(data)

    @staticmethod
    def send(message, sender_id, receiver_id_list):
        if not sender_id or not receiver_id_list:
            return False
        message.sender_id = sender_id
        message.sent_datetime = local_now()
        message.status = MessageStatus.Unrespond.value
        receiver_data = []
        for rid in receiver_id_list:
            receiver_data.append({
                "receiver_id": str(rid),
                "status": MessageStatus.Unrespond.value,
                "read_at": None,
                "responded_at": None
            })
        message.receiver_data_json = json.dumps(receiver_data)
        db.session.add(message)
        db.session.commit()
        MessageMapper._notify_by_email(message)
        return True

    @staticmethod
    def update(message, new_content, new_attachment=None):
        if not new_content:
            return False
        message.content = new_content
        message.attachment = new_attachment
        db.session.commit()
        return True

    @staticmethod
    def mark_as_read(message, receiver_id):
        receiver_data = MessageMapper._get_receiver_data(message)
        for entry in receiver_data:
            if str(entry["receiver_id"]) == str(receiver_id):
                entry["status"] = MessageStatus.Read.value
                entry["read_at"] = local_now_iso()
                MessageMapper._set_receiver_data(message, receiver_data)
                if all(e["status"] != MessageStatus.Unrespond.value for e in receiver_data):
                    message.status = MessageStatus.Read.value
                db.session.commit()
                return
        return

    @staticmethod
    def respond(message, responder_id, reply_content):
        if not reply_content:
            return False
        receiver_data = MessageMapper._get_receiver_data(message)
        found = False
        for entry in receiver_data:
            if str(entry["receiver_id"]) == str(responder_id):
                entry["status"] = MessageStatus.Respond.value
                entry["responded_at"] = local_now_iso()
                found = True
                break
        if not found:
            return False
        MessageMapper._set_receiver_data(message, receiver_data)
        message.status = MessageStatus.Respond.value
        reply_message = Message(
            content=reply_content,
            sender_id=responder_id,
            parent_message_id=message.id
        )
        reply_receiver_data = [{
            "receiver_id": str(message.sender_id),
            "status": MessageStatus.Unrespond.value,
            "read_at": None,
            "responded_at": None
        }]
        reply_message.receiver_data_json = json.dumps(reply_receiver_data)
        db.session.add(reply_message)
        db.session.commit()
        MessageMapper._notify_by_email(reply_message)
        return True

    @staticmethod
    def get_receiver_ids(message):
        data = MessageMapper._get_receiver_data(message)
        return [int(e["receiver_id"]) for e in data]

    @staticmethod
    def get_receiver_status(message, receiver_id):
        data = MessageMapper._get_receiver_data(message)
        for entry in data:
            if str(entry["receiver_id"]) == str(receiver_id):
                return entry["status"]
        return None

    @staticmethod
    def get_receiver_users(message):
        data = MessageMapper._get_receiver_data(message)
        ids = [int(e["receiver_id"]) for e in data]
        if not ids:
            return []
        return User.query.filter(User.id.in_(ids)).all()

    @staticmethod
    def _notify_by_email(message):
        """Send email notifications to all receivers of this message."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from flask import current_app

            sender = User.query.get(message.sender_id)
            sender_name = sender.name if sender else "MCS System"
            sender_email = current_app.config.get("MAIL_DEFAULT_SENDER", "noreply@bnbu.edu.cn")

            server = current_app.config.get("MAIL_SERVER", "")
            port = current_app.config.get("MAIL_PORT", 587)
            username = current_app.config.get("MAIL_USERNAME", "")
            password = current_app.config.get("MAIL_PASSWORD", "")

            if not server or not username or not password:
                return False

            for receiver in MessageMapper.get_receiver_users(message):
                if not receiver.email:
                    continue
                msg = MIMEMultipart()
                msg["From"] = sender_email
                msg["To"] = receiver.email
                msg["Subject"] = f"[MCS] New message from {sender_name}"
                body = f"Dear {receiver.name},\n\nYou have received a new message from {sender_name} in the Mentor Caring System.\n\nMessage: {message.content}\n\nPlease log in to respond."
                msg.attach(MIMEText(body, "plain"))

                with smtplib.SMTP(server, port) as smtp:
                    smtp.starttls()
                    smtp.login(username, password)
                    smtp.sendmail(sender_email, receiver.email, msg.as_string())
            return True
        except Exception:
            return False
