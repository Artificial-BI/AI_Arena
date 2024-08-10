from flask import Blueprint, render_template, jsonify, g
from models import db, User
import logging
from load_user import load_user

common_bp = Blueprint('common_bp', __name__)
# -- common_routes.py --
# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@common_bp.route('/some_route')
def some_route():
    response = load_user()
    if response.status_code != 200 and response.status_code != 201:
        return response  # Вернуть ответ, если что-то пошло не так
    user_data = response.get_json()
    user_id = user_data.get('user_id')

@common_bp.route('/initialize_user')
def initialize_user():
    return jsonify({'user_id': g.user.cookie_id})

@common_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')

@common_bp.route('/terms')
def terms():
    return render_template('terms.html')

@common_bp.route('/about')
def about():
    return render_template('about.html')

@common_bp.route('/contacts')
def contacts():
    return render_template('contacts.html')
