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


def convert_to_label(minutes):
    if minutes == 0:
        return "Never"
    if minutes < 60:
        return f"{minutes} minutes"
    elif minutes < 1440:
        return f"{minutes // 60} hours"
    else:
        days = minutes // 1440
        hours = (minutes % 1440) // 60
        mins = minutes % 60
        label = f"{days} days"
        if hours > 0:
            label += f" {hours} hrs"
        if mins > 0:
            label += f" {mins} mins"
        return label


def is_expired(msg):
    try:
        expire_min = int(msg.get("expire_min", 0))
        if expire_min == 0:
            return False
        sent_time = datetime.strptime(msg.get("time"), "%Y-%m-%d %H:%M:%S")
        return datetime.now() > sent_time + timedelta(minutes=expire_min)
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

        expire_minutes = parse_minutes(expire_value)
        expire_label = convert_to_label(expire_minutes)

        all_messages.append({
            "id": qr_id,
            "from": my_username,
            "to": recipient_username,
            "qr_id": qr_id,
            "qr_data": qr_entry,
            "message": message,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "expire_in": expire_label,
            "expire_min": expire_minutes,
            "read": False,
            "deleted_by": []
        })
        save_messages(all_messages)
        flash("QR Code shared successfully.", "success")
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
        and not is_expired(m)
    ]
    my_qrs = [q for q in all_qrcodes if q.get('user_id') == my_email]

    return render_template('chat.html', my_username=my_username, inbox=inbox, my_qrs=my_qrs)


@chat_bp.route('/has_new')
@login_required
def has_new():
    users = load_users()
    all_messages = load_messages()
    my_username = users.get(current_user.id, {}).get("username")
    new_messages = any(
        m.get('to') == my_username and not m.get('read') and my_username not in m.get('deleted_by', []) and not is_expired(m)
        for m in all_messages
    )
    return {"new_messages": new_messages}


@chat_bp.route('/delete', methods=['POST'])
@login_required
def delete_message():
    users = load_users()
    all_messages = load_messages()
    my_username = users.get(current_user.id, {}).get("username")
    data = request.get_json()
    delete_id = data.get('delete_id')

    for msg in all_messages:
        if msg.get('id') == delete_id:
            if 'deleted_by' not in msg:
                msg['deleted_by'] = []
            if my_username not in msg['deleted_by']:
                msg['deleted_by'].append(my_username)

    save_messages(all_messages)
    return '', 204
