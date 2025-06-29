from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
import json, os

admin_blueprint = Blueprint('admin', __name__, url_prefix='/admin')

USER_FILE = 'users.json'
QR_FILE = 'qrcodes.json'
MSG_FILE = 'shared_messages.json'

@admin_blueprint.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash("Access denied", "danger")
        return redirect(url_for('qr.generate_qr'))

    # Load users
    with open(USER_FILE, 'r') as f:
        users = json.load(f)

    # Load QR codes
    qrs = {}
    if os.path.exists(QR_FILE):
        with open(QR_FILE, 'r') as f:
            qrs = json.load(f)

    # Load message stats
    msg_stats = {}
    if os.path.exists(MSG_FILE):
        with open(MSG_FILE, 'r') as f:
            all_msgs = json.load(f)
            for msg in all_msgs:
                sender = msg.get('sender')
                receiver = msg.get('receiver')
                msg_stats[sender] = msg_stats.get(sender, {'sent': 0, 'received': 0})
                msg_stats[receiver] = msg_stats.get(receiver, {'sent': 0, 'received': 0})
                msg_stats[sender]['sent'] += 1
                msg_stats[receiver]['received'] += 1

    return render_template(
        'admin_dashboard.html',
        users=users,
        qrcodes=qrs,
        message_stats=msg_stats
    )

@admin_blueprint.route('/delete_user', methods=['POST'])
@login_required
def delete_user():
    if current_user.role != 'admin':
        flash("Unauthorized", "danger")
        return redirect(url_for('admin.dashboard'))

    email = request.form.get('email')
    if not email:
        flash("Email missing", "danger")
        return redirect(url_for('admin.dashboard'))

    with open(USER_FILE, 'r') as f:
        users = json.load(f)

    if email in users and email != current_user.email:
        del users[email]
        with open(USER_FILE, 'w') as f:
            json.dump(users, f, indent=4)
        flash(f"User {email} deleted.", "success")
    else:
        flash("You cannot delete yourself.", "warning")

    return redirect(url_for('admin.dashboard'))

@admin_blueprint.route('/edit_user', methods=['POST'])
@login_required
def edit_user():
    if current_user.role != 'admin':
        flash("Unauthorized", "danger")
        return redirect(url_for('admin.dashboard'))

    old_email = request.form.get('old_email')
    new_email = request.form.get('new_email', '').strip()
    new_username = request.form.get('new_username', '').strip()
    new_password = request.form.get('new_password', '').strip()

    if not old_email or not new_email or not new_username:
        flash("Missing fields", "danger")
        return redirect(url_for('admin.dashboard'))

    with open(USER_FILE, 'r') as f:
        users = json.load(f)

    if old_email not in users:
        flash("User not found.", "danger")
        return redirect(url_for('admin.dashboard'))

    if old_email != new_email and new_email in users:
        flash("New email is already in use.", "danger")
        return redirect(url_for('admin.dashboard'))

    # Update user
    user = users.pop(old_email)
    user['username'] = new_username
    if new_password:
        user['password'] = new_password
    users[new_email] = user

    with open(USER_FILE, 'w') as f:
        json.dump(users, f, indent=4)

    flash(f"User {old_email} updated successfully.", "success")
    return redirect(url_for('admin.dashboard'))
