from flask import Blueprint, render_template

common_bp = Blueprint('common_bp', __name__)

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
