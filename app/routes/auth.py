import json, os, random, string
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.utils.auth_utils import User
from app.utils.email_utils import send_verification_email, send_reset_code_email
from app import login_manager
import re
import uuid

auth_blueprint = Blueprint('auth', __name__, url_prefix='/auth')

USER_FILE = 'users.json'

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        gender = request.form.get('gender', 'boy')

        if not all([username, email, password, confirm]):
            flash("All fields are required.", "danger")
            return render_template('register.html')

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')

        users = load_users()

        for u in users.values():
            if u.get("username") == username:
                flash("Username already taken.", "danger")
                return render_template('register.html')

        if email in users:
            flash("Email already registered.", "danger")
        else:
            code = generate_code()
            user_id = str(uuid.uuid4())
            avatar_url = f"https://avatar.iran.liara.run/public/{gender}?username={username}"
            users[email] = {
                "id": user_id,
                "username": username,
                "email": email,
                "password": password,
                "role": "user",
                "is_verified": False,
                "verification_code": code,
                "reset_code": None,
                "gender": gender,
                "avatar": avatar_url
            }
            save_users(users)
            send_verification_email(email, code)
            flash("Check your email for a verification code.", "info")
            return redirect(url_for('auth.verify_email', email=email))
    return render_template('register.html')

@auth_blueprint.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    email = request.args.get('email')
    if not email:
        return redirect(url_for('auth.register'))

    if request.method == 'POST':
        code = request.form.get('code')
        if not code:
            flash("Verification code is required.", "danger")
            return render_template('verify_email.html', email=email)

        users = load_users()
        user = users.get(email)

        if user and user['verification_code'] == code:
            user['is_verified'] = True
            user['verification_code'] = None
            save_users(users)
            flash("Email verified. You can now log in.", "success")
            return redirect(url_for('auth.login'))
        else:
            flash("Invalid code.", "danger")

    return render_template('verify_email.html', email=email)

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form.get('login', '').strip().lower()
        password = request.form.get('password')
        users = load_users()

        matched_email = None
        for email, data in users.items():
            if login_input == email.lower() or login_input == data.get('username', '').lower():
                matched_email = email
                break

        if matched_email:
            user = users[matched_email]
            if user['password'] == password:
                if not user.get('is_verified', False):
                    flash("Please verify your email before logging in.", "warning")
                    return redirect(url_for('auth.verify_email', email=matched_email))

                u = User(user['id'], user['email'], user['password'], user.get('role', 'user'))
                u.avatar = user.get('avatar')
                u.username = user.get('username')
                u.gender = user.get('gender')
                login_user(u)
                return redirect(url_for('home.home'))

        flash("Invalid credentials.", "danger")

    return render_template('login.html')

@auth_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_blueprint.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash("Please enter your email address.", "danger")
            return render_template('forgot_password.html')

        users = load_users()
        user = users.get(email)
        if user:
            code = generate_code()
            user['reset_code'] = code
            save_users(users)
            send_reset_code_email(email, code)
            flash("Reset code sent to your email.", "info")
            return redirect(url_for('auth.reset_password', email=email))
        else:
            flash("Email not found.", "danger")
            return render_template('forgot_password.html')
    return render_template('forgot_password.html')

@auth_blueprint.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    email = request.args.get('email')
    if not email:
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        code = request.form.get('code')
        new_password = request.form.get('new_password')

        users = load_users()
        user = users.get(email)

        if user and user.get('reset_code') == code:
            user['password'] = new_password
            user['reset_code'] = None
            save_users(users)
            flash("Password updated. You can now log in.", "success")
            return redirect(url_for('auth.login'))
        else:
            flash("Invalid code.", "danger")

    return render_template('reset_password.html', email=email)

@auth_blueprint.route('/qr_saved_alert')
def qr_saved_alert():
    flash("QR Code Saved Successfully.", "success")
    return redirect(url_for('home.home'))

@auth_blueprint.route('/status')
def auth_status():
    return {"logged_in": current_user.is_authenticated}

@login_manager.user_loader
def load_user(user_id):
    users = load_users()
    for email, data in users.items():
        if data.get("id") == user_id:
            u = User(data['id'], data['email'], data['password'], data.get('role', 'user'))
            u.avatar = data.get('avatar')
            u.username = data.get('username')
            u.gender = data.get('gender')
            return u
    return None