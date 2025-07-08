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
        return {}
    with open(QR_DB, 'r') as f:
        return json.load(f)


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
        expire_in = msg.get("expire_in")
        if not expire_in or expire_in == "0" or expire_in.lower() == "never":
            return False
        sent_time = datetime.strptime(msg.get("time"), "%Y-%m-%d %H:%M:%S")
        expire_minutes = parse_minutes(msg.get("expire_in"))
        return datetime.now() > sent_time + timedelta(minutes=expire_minutes)
    except:
        return False


@chat_bp.route('/', methods=['GET', 'POST'], endpoint='chat')
@login_required
def chat():
    users = load_users()
    all_messages = load_messages()
    all_qrcodes = load_qrcodes()

    my_id = current_user.id
    my_user = next((u for u in users.values() if u.get("id") == my_id), None)
    my_username = my_user.get("username")

    if request.method == 'POST':
        recipient_raw = request.form.get('recipient', '')
        recipient_usernames = [r.strip() for r in recipient_raw.split(',') if r.strip()]
        qr_id = request.form.get('qr_id')
        message = request.form.get('message', '')
        expire_value = request.form.get('expire_in', '0') or '0'

        if not recipient_usernames:
            flash("Please enter at least one recipient.", "danger")
            return redirect(url_for('chat.chat'))

        if my_username in recipient_usernames:
            flash("You cannot send a QR to yourself.", "danger")
            return redirect(url_for('chat.chat'))

        qr_entry = next((v for k, v in all_qrcodes.items() if k == qr_id and v.get('user_id') == my_id), None)
        if not qr_entry:
            flash("QR code not found or unauthorized.", "danger")
            return redirect(url_for('chat.chat'))

        invalid_recipients = [r for r in recipient_usernames if not any(u for u in users.values() if u.get("username") == r)]
        if invalid_recipients:
            flash("Invalid usernames: " + ", ".join(invalid_recipients), "danger")
            return redirect(url_for('chat.chat'))

        for recipient_username in recipient_usernames:
            recipient_user = next((u for u in users.values() if u.get("username") == recipient_username), None)
            if not recipient_user:
                continue

            new_id = f"{qr_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            all_messages.append({
                "id": new_id,
                "from": my_username,
                "to": recipient_username,
                "qr_id": qr_id,
                "qr_data": qr_entry,
                "message": message,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "expire_in": expire_value,
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

    inbox = []
    for m in all_messages:
        if (m.get('to') == my_username or m.get('from') == my_username) and my_username not in m.get('deleted_by', []) and not is_expired(m):
            msg_copy = m.copy()
            msg_copy['from_display'] = "You" if msg_copy['from'] == my_username else msg_copy['from']
            inbox.append(msg_copy)

    my_qrs = [
        {"id": k, **v}
        for k, v in all_qrcodes.items()
        if v.get("user_id") == my_id
    ]

    return render_template('chat.html',
                           my_username=my_username,
                           inbox=inbox,
                           my_qrs=my_qrs,
                           avatar=current_user.avatar)


@chat_bp.route('/validate-users', methods=['POST'])
@login_required
def validate_users():
    data = request.get_json()
    usernames = [u.strip() for u in data.get('recipients', []) if u.strip()]
    users = load_users()
    all_usernames = [u['username'] for u in users.values()]
    invalid = [u for u in usernames if u not in all_usernames]
    return jsonify({'valid': len(invalid) == 0, 'invalid': invalid})


@chat_bp.route('/has_new')
@login_required
def has_new():
    users = load_users()
    all_messages = load_messages()
    my_user = next((u for u in users.values() if u.get("id") == current_user.id), None)
    my_username = my_user.get("username")

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
    my_user = next((u for u in users.values() if u.get("id") == current_user.id), None)
    my_username = my_user.get("username")

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
