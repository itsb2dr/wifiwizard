import json
import os
from datetime import datetime

QR_DB = 'qrcodes.json'
CHAT_FILE = 'shared_messages.json'

def load_qr_codes():
    if not os.path.exists(QR_DB):
        return {}
    with open(QR_DB, 'r') as f:
        return json.load(f)

def load_shared_messages():
    if not os.path.exists(CHAT_FILE):
        return []
    with open(CHAT_FILE, 'r') as f:
        return json.load(f)

def save_shared_messages(messages):
    with open(CHAT_FILE, 'w') as f:
        json.dump(messages, f, indent=4)

def get_user_qrs(email):
    qr_data = load_qr_codes()
    return [qr for qr in qr_data.get(email, [])]

def share_qr_code(from_user, to_user, qr_id, message):
    all_qrs = load_qr_codes()
    sender_qrs = all_qrs.get(from_user, [])
    target_qr = next((qr for qr in sender_qrs if qr['id'] == qr_id), None)
    if not target_qr:
        return False

    messages = load_shared_messages()
    messages.append({
        "from": from_user,
        "to": to_user,
        "qr_data": target_qr,
        "message": message,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_shared_messages(messages)
    return True

def get_user_inbox(username):
    messages = load_shared_messages()
    return [msg for msg in messages if msg['to'] == username]
