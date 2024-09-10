import json
import asyncio
from flask import Blueprint, request, jsonify, render_template, g
from extensions import db
from models import Message, Role, User
from assistant import Assistant
import logging
from load_user import load_user

# --- admin_routes.py ---
admin_bp = Blueprint('admin', __name__)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@admin_bp.before_request
def before_request():
    response = load_user()
    if response.status_code != 200 and response.status_code != 201:
        return response
    
    # Извлекаем данные пользователя из ответа
    user_data = response.get_json()
    g.user_id = user_data.get('user_id')
    g.cookie_id = user_data.get('cookie_id')

@admin_bp.route('/')
def admin():
    roles = Role.query.all()
    return render_template('admin.html', roles=roles)

@admin_bp.route('/update_settings', methods=['POST'])
def update_settings():
    temperature = request.form.get('temperature')
    top_p = request.form.get('top_p')
    top_k = request.form.get('top_k')
    return jsonify({'status': 'Settings updated'}), 200

@admin_bp.route('/send_message', methods=['POST'])
def send_message():
    try:
        content = request.form['message']
        role_name = request.form['role']  # Получаем имя роли из формы
        user_id = g.user_id  # Используем ID текущего пользователя

        # Создаем ассистента с выбранной ролью
        assistant = Assistant(role_name)
        
        # Используем asyncio.run для выполнения асинхронной функции
        response = asyncio.run(assistant.send_message(content, 'gemini'))

        # Сохраняем сообщение и ответ в базе данных
        message = Message(content=content, user_id=user_id)
        response_message = Message(content=response, user_id=0)
        db.session.add(message)
        db.session.add(response_message)
        db.session.commit()

        return jsonify({"status": "Message sent", "response": response})
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/get_instructions', methods=['POST'])
def get_instructions():
    try:
        role_name = request.form['role']
        role = Role.query.filter_by(name=role_name).first()
        if role:
            return jsonify({"instructions": role.instructions})
        else:
            return jsonify({"instructions": ""})
    except Exception as e:
        logger.error(f"Error fetching instructions: {e}")
        return jsonify({"error": "Internal server error"}), 500

@admin_bp.route('/save_instructions', methods=['POST'])
def save_instructions():
    try:
        role_name = request.form['role']
        instructions = request.form['instructions']
        logger.info(f"Saving instructions for role: {role_name}, instructions: {instructions}")
        
        role = Role.query.filter_by(name=role_name).first()
        if role:
            role.instructions = instructions
        else:
            role = Role(name=role_name, instructions=instructions)
            db.session.add(role)

        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error saving instructions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@admin_bp.route('/admin', methods=['GET'])
def admin_page():
    messages = Message.query.all()
    roles = Role.query.all()
    return render_template('admin.html', messages=messages, roles=roles)
