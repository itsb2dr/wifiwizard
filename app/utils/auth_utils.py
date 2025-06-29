import json
from flask_login import UserMixin
import os

USER_FILE = 'users.json'

class User(UserMixin):
    def __init__(self, id, email, password, role='user'):
        self.id = id
        self.email = email
        self.password = password
        self.role = role

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, 'r') as file:
        return json.load(file)

def save_users(users):
    with open(USER_FILE, 'w') as file:
        json.dump(users, file, indent=4)

def get_next_user_id(users):
    if not users:
        return "1"
    return str(max([int(uid) for uid in users.keys()]) + 1)

def authenticate_user(email, password):
    users = load_users()
    for user_id, user_data in users.items():
        if user_data['email'] == email and user_data['password'] == password:
            return User(user_id, user_data['email'], user_data['password'], user_data.get('role', 'user'))
    return None

def register_user(email, password):
    users = load_users()
    if any(u['email'] == email for u in users.values()):
        return False

    new_id = get_next_user_id(users)
    users[new_id] = {
        'email': email,
        'password': password,
        'role': 'user',
        'is_verified': False,
        'verification_code': None,
        'reset_code': None
    }
    save_users(users)
    return True
