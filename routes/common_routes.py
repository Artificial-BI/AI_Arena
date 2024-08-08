from flask import Blueprint, render_template, jsonify, g
from models import db, User
import logging
from load_user import load_user

common_bp = Blueprint('common_bp', __name__)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@common_bp.before_app_request
def before_request():
    response = load_user()
    if response:
        return response

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
