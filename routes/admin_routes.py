# admin_routes.py

import json
import asyncio
from flask import Blueprint, request, jsonify, render_template
from extensions import db
from models import Message, Role
from gemini import GeminiAssistant
import logging

admin_bp = Blueprint('admin', __name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@admin_bp.route('/update_settings', methods=['POST'])
def update_settings():
    temperature = request.form.get('temperature')
    top_p = request.form.get('top_p')
    top_k = request.form.get('top_k')
    return jsonify({'status': 'Settings updated'}), 200

@admin_bp.route('/add_referee_prompt', methods=['POST'])
def add_referee_prompt():
    prompt_text = request.form.get('referee_prompt')
    return jsonify({'status': 'Referee prompt added'}), 200

@admin_bp.route('/select_referee_prompt', methods=['POST'])
def select_referee_prompt():
    prompt_id = request.form.get('existing_prompts')
    return jsonify({'status': 'Referee prompt selected'}), 200

@admin_bp.route('/add_commentator_prompt', methods=['POST'])
def add_commentator_prompt():
    prompt_text = request.form.get('commentator_prompt')
    return jsonify({'status': 'Commentator prompt added'}), 200

@admin_bp.route('/select_commentator_prompt', methods=['POST'])
def select_commentator_prompt():
    prompt_id = request.form.get('existing_commentator_prompts')
    return jsonify({'status': 'Commentator prompt selected'}), 200

@admin_bp.route('/send_message', methods=['POST'])
def send_message():
    try:
        content = request.form['message']
        user_id = 1  # Замените на идентификатор текущего пользователя

        # Создаем ассистента при каждом вызове
        assistant = GeminiAssistant("role_characters.json")
        
        # Используем asyncio.run для выполнения асинхронной функции
        logger.info(f"Sending message to assistant: {content}")
        response = asyncio.run(assistant.send_message(content))
        logger.info(f"Received response from assistant: {response}")

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
    role_name = request.form.get('role')
    role = Role.query.filter_by(name=role_name).first()
    if role:
        return jsonify({"instructions": role.instructions})
    return jsonify({"error": "Role not found"}), 404

@admin_bp.route('/save_instructions', methods=['POST'])
def save_instructions():
    role_name = request.form.get('role')
    instructions = request.form.get('instructions')
    role = Role.query.filter_by(name=role_name).first()
    if role:
        role.instructions = instructions
        db.session.commit()
        return jsonify({"status": "success"})
    return jsonify({"error": "Role not found"}), 404

@admin_bp.route('/admin', methods=['GET'])
def admin():
    messages = Message.query.all()
    return render_template('admin.html', messages=messages)
