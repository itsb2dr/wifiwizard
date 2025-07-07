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
        self.username = None
        self.avatar = None
        self.gender = None

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, 'r') as file:
        return json.load(file)

def save_users(users):
    with open(USER_FILE, 'w') as file:
        json.dump(users, file, indent=4)

def authenticate_user(login_input, password):
    users = load_users()
    for user_data in users.values():
        if (user_data.get('email', '').lower() == login_input.lower() or
            user_data.get('username', '').lower() == login_input.lower()):
            if user_data['password'] == password:
                u = User(user_data['id'], user_data['email'], user_data['password'], user_data.get('role', 'user'))
                u.avatar = user_data.get('avatar')
                u.username = user_data.get('username')
                u.gender = user_data.get('gender')
                return u
    return None

def register_user(email, password, username, gender):
    users = load_users()
    for user_data in users.values():
        if user_data.get('email') == email or user_data.get('username') == username:
            return False

    import uuid
    user_id = str(uuid.uuid4())
    avatar_url = f"https://avatar.iran.liara.run/public/{gender}?username={username}"
    users[email] = {
        "id": user_id,
        "username": username,
        "email": email,
        "password": password,
        "role": "user",
        "is_verified": False,
        "verification_code": None,
        "reset_code": None,
        "gender": gender,
        "avatar": avatar_url
    }
    save_users(users)
    return True
