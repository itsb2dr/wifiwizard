import os
import json
import base64
from PIL import Image
from io import BytesIO

QR_DB = 'qrcodes.json'
IMAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'images'))

def generate_qr_with_logo(ssid, password, canvas_data_base64, user_id, scan_text):
    qr_id = get_next_qr_id()
    filename = f'{qr_id}.png'
    img_path = os.path.join(IMAGE_DIR, filename)
    web_path = f'images/{filename}'  # used in HTML via url_for('static', filename=web_path)

    os.makedirs(IMAGE_DIR, exist_ok=True)

    try:
        img_data = base64.b64decode(canvas_data_base64.split(",")[1])
        img = Image.open(BytesIO(img_data))
        img.save(img_path)
    except Exception as e:
        print("QR Save Error:", e)
        return None

    save_qr_to_json(qr_id, user_id, ssid, password, web_path, scan_text)
    return web_path

def get_next_qr_id():
    if not os.path.exists(QR_DB):
        return "qr1"
    try:
        with open(QR_DB, 'r') as f:
            qrs = json.load(f)
    except:
        return "qr1"
    if not qrs:
        return "qr1"
    max_id = max([int(k[2:]) for k in qrs if k.startswith('qr') and k[2:].isdigit()], default=0)
    return f"qr{max_id + 1}"

def save_qr_to_json(qr_id, user_id, ssid, password, image_path, scan_text):
    qrs = {}
    if os.path.exists(QR_DB):
        try:
            with open(QR_DB, 'r') as f:
                qrs = json.load(f)
        except:
            pass

    qrs[qr_id] = {
        "user_id": user_id,
        "ssid": ssid,
        "password": password,
        "image_path": image_path,  # This is already relative: images/filename.png
        "scan_text": scan_text
    }

    with open(QR_DB, 'w') as f:
        json.dump(qrs, f, indent=4)
