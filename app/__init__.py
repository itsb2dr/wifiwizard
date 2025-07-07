import os
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from app.config import Config

mail = Mail()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mail.init_app(app)
    login_manager.init_app(app)

    # Import and register blueprints
    from app.routes.auth import auth_blueprint
    from app.routes.qr import qr_bp as qr_blueprint
    from app.routes.admin import admin_blueprint
    from app.routes.home import home_blueprint
    from app.routes.chat import chat_bp  # ✅ Chat blueprint import
    from app.routes.profile import profile_blueprint  # ✅ Profile blueprint import

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(qr_blueprint)
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(home_blueprint)
    app.register_blueprint(chat_bp)  # ✅ Chat blueprint registration
    app.register_blueprint(profile_blueprint)  # ✅ Profile blueprint registration

    return app
