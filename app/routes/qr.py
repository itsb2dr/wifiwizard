import os
import json
import base64
from datetime import datetime, timedelta
from flask import Blueprint, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from app.utils.qr_utils import generate_qr_with_logo

qr_bp = Blueprint("qr", __name__, url_prefix="/qr")

QR_DB_FILE = "qrcodes.json"

def load_qr_data():
    if os.path.exists(QR_DB_FILE):
        with open(QR_DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_qr_data(data):
    with open(QR_DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

@qr_bp.route("/generate", methods=["POST"])
@login_required
def generate_qr():
    ssid = request.form.get("ssid")
    password = request.form.get("password")
    scan_text = request.form.get("scan_text")
    canvas_data = request.form.get("canvas_data")

    if not all([ssid, password, scan_text, canvas_data]):
        flash("Missing QR data. Please try again.", "danger")
        return redirect(url_for("home.home"))

    user_id = current_user.get_id()
    image_path = generate_qr_with_logo(ssid, password, canvas_data, user_id, scan_text)

    if not image_path:
        flash("Failed to save QR code.", "danger")
        return redirect(url_for("home.home"))

    flash("QR Code saved successfully.", "success")
    session['show_download'] = True  # ✅ THIS IS THE KEY FIX
    return redirect(url_for("home.home"))

# ✅ Add this endpoint to support JS check after redirect
@qr_bp.route("/check_download")
def check_download():
    show = session.pop('show_download', False)
    return jsonify({"show_download": show})
