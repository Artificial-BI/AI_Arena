from flask import Blueprint, render_template, jsonify

viewer_bp = Blueprint('viewer_bp', __name__)

# Вспомогательная функция
def fetch_battle_updates():
    # Ваш код для получения обновлений битвы
    return []

@viewer_bp.route('/')
def viewer():
    return render_template('viewer.html')

@viewer_bp.route('/get_battle_updates')
def get_battle_updates():
    updates = fetch_battle_updates()
    return jsonify(updates)
