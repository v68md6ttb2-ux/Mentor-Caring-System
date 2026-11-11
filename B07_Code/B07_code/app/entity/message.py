"""Message entity class."""

import json
import uuid
from app.utils.time_utils import local_now

from app.extensions import db
from app.entity.enums import MessageStatus


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.String(80), unique=True, nullable=False,
                           default=lambda: f"MSG-{uuid.uuid4().hex[:10].upper()}")
    content = db.Column(db.Text, nullable=False)
    attachment = db.Column(db.String(255), nullable=True)
    sent_datetime = db.Column(db.DateTime, default=local_now, nullable=False)
    status = db.Column(db.String(30), default=MessageStatus.Unrespond.value, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_data_json = db.Column(db.Text, default="[]", nullable=False)
    parent_message_id = db.Column(db.Integer, db.ForeignKey("messages.id"), nullable=True)

    sender = db.relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    parent_message = db.relationship("Message", remote_side=[id], backref="replies")

    def _get_receiver_data(self):
        try:
            return json.loads(self.receiver_data_json or "[]")
        except json.JSONDecodeError:
            return []

    def _set_receiver_data(self, data):
        self.receiver_data_json = json.dumps(data)

    def set(self, content, attachment=None):
        self.content = content
        self.attachment = attachment

    def get_receiver_ids(self):
        data = self._get_receiver_data()
        return [int(e["receiver_id"]) for e in data]

    def get_receiver_status(self, receiver_id):
        data = self._get_receiver_data()
        for entry in data:
            if str(entry["receiver_id"]) == str(receiver_id):
                return entry["status"]
        return None

    def update(self, new_content, new_attachment=None):
        from app.mapper.message_mapper import MessageMapper
        return MessageMapper.update(self, new_content, new_attachment)

    def send(self, sender_id, receiver_id_list):
        from app.mapper.message_mapper import MessageMapper
        return MessageMapper.send(self, sender_id, receiver_id_list)

    def mark_as_read(self, receiver_id):
        from app.mapper.message_mapper import MessageMapper
        MessageMapper.mark_as_read(self, receiver_id)
        return

    def respond(self, responder_id, reply_content):
        from app.mapper.message_mapper import MessageMapper
        return MessageMapper.respond(self, responder_id, reply_content)

    @property
    def receiver_users(self):
        from app.mapper.message_mapper import MessageMapper
        return MessageMapper.get_receiver_users(self)

    def notify_by_email(self):
        from app.mapper.message_mapper import MessageMapper
        return MessageMapper._notify_by_email(self)

    def markAsRead(self, receiver_id):
        self.mark_as_read(receiver_id)

    def notifyByEmail(self):
        return self.notify_by_email()
