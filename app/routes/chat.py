# app/routes/chat.py
import os
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from datetime import datetime, timedelta

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

QR_DB = 'qrcodes.json'
SHARED_DB = 'shared_messages.json'
USER_DB = 'users.json'


def load_users():
    if not os.path.exists(USER_DB):
        return {}
    with open(USER_DB, 'r') as f:
        return json.load(f)


def load_qrcodes():
    if not os.path.exists(QR_DB):
        return []
    with open(QR_DB, 'r') as f:
        data = json.load(f)
        if isinstance(data, dict):
            return [dict(id=k, **v) for k, v in data.items() if isinstance(v, dict)]
        return data


def load_messages():
    if not os.path.exists(SHARED_DB):
        return []
    with open(SHARED_DB, 'r') as f:
        return json.load(f)


def save_messages(data):
    with open(SHARED_DB, 'w') as f:
        json.dump(data, f, indent=4)


def parse_minutes(expire_value):
    if not expire_value or expire_value == "0" or expire_value.lower() == "never":
        return 0
    try:
        return int(expire_value)
    except ValueError:
        units = {
            "minute": 1, "minutes": 1,
            "hour": 60, "hours": 60,
            "day": 1440, "days": 1440
        }
        parts = expire_value.lower().split()
        if len(parts) == 2 and parts[1] in units:
            return int(parts[0]) * units[parts[1]]
    return 0


def is_expired(msg):
    try:
        expire_in = msg.get("expire_in")
        if isinstance(expire_in, str) and not expire_in.isdigit():
            return False  # not a numeric value, skip expiration
        expire_minutes = int(expire_in)
        if expire_minutes == 0:
            return False
        sent_time = datetime.strptime(msg.get("time"), "%Y-%m-%d %H:%M:%S")
        return datetime.now() > sent_time + timedelta(minutes=expire_minutes)
    except:
        return False


@chat_bp.route('/', methods=['GET', 'POST'], endpoint='chat')
@login_required
def chat():
    users = load_users()
    all_messages = load_messages()
    all_qrcodes = load_qrcodes()

    my_email = current_user.id
    my_username = users.get(my_email, {}).get("username")

    if request.method == 'POST':
        recipient_username = request.form.get('recipient')
        qr_id = request.form.get('qr_id')
        message = request.form.get('message', '')
        expire_value = request.form.get('expire_in', '0') or '0'

        if recipient_username == my_username:
            flash("You cannot send a QR to yourself.", "danger")
            return redirect(url_for('chat.chat'))

        qr_entry = next((q for q in all_qrcodes if q.get('id') == qr_id and q.get('user_id') == my_email), None)
        if not qr_entry:
            flash("QR code not found or unauthorized.", "danger")
            return redirect(url_for('chat.chat'))

        recipient_email = next((email for email, info in users.items() if info.get("username") == recipient_username), None)
        if not recipient_email:
            flash("Recipient username not found.", "danger")
            return redirect(url_for('chat.chat'))

        all_messages.append({
            "id": qr_id,
            "from": my_username,
            "to": recipient_username,
            "qr_id": qr_id,
            "qr_data": qr_entry,
            "message": message,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "expire_in": str(parse_minutes(expire_value)),  # ✅ SAVE AS MINUTES STRING
            "read": False,
            "deleted_by": []
        })
        save_messages(all_messages)
        flash("QR Code shared successfully.", "success")
        session.modified = True
        return redirect(url_for('chat.chat'))

    updated = False
    for m in all_messages:
        if m.get('to') == my_username and not m.get('read'):
            m['read'] = True
            updated = True
    if updated:
        save_messages(all_messages)

    inbox = [
        m for m in all_messages
        if (m.get('to') == my_username or m.get('from') == my_username)
        and my_username not in m.get('deleted_by', [])
        and not is_expired(m)  # ✅ THIS IS FIXED TOO
    ]
    my_qrs = [q for q in all_qrcodes if q.get('user_id') == my_email]

    return render_template('chat.html', my_username=my_username, inbox=inbox, my_qrs=my_qrs)
