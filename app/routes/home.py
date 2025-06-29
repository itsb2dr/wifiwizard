from flask import Blueprint, render_template
from flask_login import current_user

home_blueprint = Blueprint('home', __name__)

@home_blueprint.route('/')
def home():
    return render_template('home.html')
