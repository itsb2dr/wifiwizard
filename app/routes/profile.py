import os
import json
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.utils.email_utils import send_verification_email

profile_blueprint = Blueprint('profile', __name__, url_prefix='/profile')

USERS_FILE = 'users.json'
QRCODE_FILE = 'qrcodes.json'

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def load_qrcodes():
    if not os.path.exists(QRCODE_FILE):
        return {}
    with open(QRCODE_FILE, 'r') as f:
        return json.load(f)

def save_qrcodes(qrcodes):
    with open(QRCODE_FILE, 'w') as f:
        json.dump(qrcodes, f, indent=4)

@profile_blueprint.route('/')
@login_required
def view():
    users = load_users()
    current_data = next((u for u in users.values() if u['id'] == current_user.id), {})
    current_user.username = current_data.get("username", "")
    current_user.email = current_data.get("email", "")

    qrcodes = load_qrcodes()
    history = {k: v for k, v in qrcodes.items() if v.get('user_id') == current_user.id}
    return render_template('profile.html', qr_history=history.items(), qr_count=len(history))

@profile_blueprint.route('/avatar', methods=['POST'])
@login_required
def change_avatar():
    new_avatar = request.form.get('avatar')
    if new_avatar:
        users = load_users()
        for email, user in users.items():
            if user.get("id") == current_user.id:
                user['avatar'] = new_avatar
                save_users(users)
                flash("Avatar updated successfully.", "success")
                break
    return redirect(url_for('profile.view'))

@profile_blueprint.route('/update', methods=['POST'])
@login_required
def update_account():
    new_username = request.form.get('username', '').strip()
    new_email = request.form.get('email', '').strip().lower()

    if not new_username and not new_email:
        flash("At least one field must be filled.", "danger")
        return redirect(url_for('profile.view'))

    users = load_users()
    original_email = None
    current_data = None

    # Find the current user by id
    for email, user in users.items():
        if user.get('id') == current_user.id:
            current_data = user
            original_email = email
            break

    if not current_data:
        flash("User not found.", "danger")
        return redirect(url_for('profile.view'))

    # Check for duplicates
    for email, data in users.items():
        if data.get("id") != current_user.id:
            if new_username and data.get("username") == new_username:
                flash("Username already taken.", "danger")
                return redirect(url_for('profile.view'))
            if new_email and email == new_email:
                flash("Email already in use.", "danger")
                return redirect(url_for('profile.view'))

    # Update email key if changed
    if new_email and new_email != original_email:
        users[new_email] = users.pop(original_email)
        users[new_email]['email'] = new_email
        users[new_email]['is_verified'] = False
        code = ''.join([str(i) for i in os.urandom(3)])
        users[new_email]['verification_code'] = code
        save_users(users)
        send_verification_email(new_email, code)
        flash("Email updated. Please verify again.", "info")
        return redirect(url_for('auth.verify_email', email=new_email))

    if new_username:
        current_data['username'] = new_username
        current_user.username = new_username

    save_users(users)
    flash("Account updated successfully.", "success")
    return redirect(url_for('profile.view'))

@profile_blueprint.route('/delete_qr/<qr_id>', methods=['POST'])
@login_required
def delete_qr(qr_id):
    qrcodes = load_qrcodes()
    if qr_id in qrcodes and qrcodes[qr_id].get('user_id') == current_user.id:
        del qrcodes[qr_id]
        save_qrcodes(qrcodes)
        flash("QR code deleted.", "success")
    else:
        flash("QR not found or permission denied.", "danger")
    return redirect(url_for('profile.view'))
