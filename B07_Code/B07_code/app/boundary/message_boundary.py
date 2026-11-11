"""Message boundary — message routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.control.message_control import (
    get_available_receivers, send_message, get_received_messages,
    get_sent_messages, get_message_detail, mark_message_as_read, reply_message,
)
from app.control.log_control import add_student_activity_log

message_bp = Blueprint("message", __name__, url_prefix="/messages")


@message_bp.route("/")
@login_required
def message_home():
    received_messages = get_received_messages()
    sent_messages = get_sent_messages()
    if current_user.role == "student":
        add_student_activity_log("View Messages")
    return render_template("message_home.html", received_messages=received_messages, sent_messages=sent_messages)


@message_bp.route("/send", methods=["GET", "POST"])
@login_required
def send_message_page():
    receivers = get_available_receivers()
    if request.method == "POST":
        receiver_id_list = request.form.getlist("receiver_ids")
        content = request.form.get("content", "")
        attachment = request.form.get("attachment", "")
        success, message = send_message(receiver_id_list=receiver_id_list, content=content, attachment=attachment)
        if success and current_user.role == "student":
            add_student_activity_log("Send Message")
        flash(message)
        if success:
            return redirect(url_for("message.message_home"))
    return render_template("message_send.html", receivers=receivers)


@message_bp.route("/<int:message_id>")
@login_required
def message_detail(message_id):
    message = get_message_detail(message_id)
    if not message:
        flash("Message not found or you do not have permission to view it.")
        return redirect(url_for("message.message_home"))
    if current_user.role == "student":
        add_student_activity_log("Read Message")
    return render_template("message_detail.html", message=message)


@message_bp.route("/<int:message_id>/read", methods=["POST"])
@login_required
def mark_read(message_id):
    success, message = mark_message_as_read(message_id)
    flash(message)
    return redirect(url_for("message.message_detail", message_id=message_id))


@message_bp.route("/<int:message_id>/reply", methods=["POST"])
@login_required
def reply(message_id):
    reply_content = request.form.get("reply_content", "")
    success, message = reply_message(message_id, reply_content)
    flash(message)
    return redirect(url_for("message.message_detail", message_id=message_id))
