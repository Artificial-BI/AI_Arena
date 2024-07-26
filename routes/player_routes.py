# routes/player_routes.py
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from extensions import db
from models import Message, Character, User
from datetime import datetime

player_bp = Blueprint('player_bp', __name__)

# Вспомогательные функции
def fetch_messages():
    try:
        return Message.query.all()
    except Exception as e:
        return []

def fetch_characters():
    try:
        return Character.query.all()
    except Exception as e:
        return []

def get_selected_character():
    try:
        return Character.query.first()  # Замените на вашу логику выбора персонажа
    except Exception as e:
        return None

def fetch_general_messages():
    try:
        return Message.query.filter_by(general=True).all()
    except Exception as e:
        return []

# Пример преобразования строки в datetime
def convert_to_datetime(timestamp_str):
    return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

# Маршруты
@player_bp.route('/')
def player():
    messages = fetch_messages()
    characters = fetch_characters()
    selected_character = get_selected_character()
    general_messages = fetch_general_messages()

    return render_template('player.html', messages=messages, characters=characters, selected_character=selected_character, general_messages=general_messages)

@player_bp.route('/select_character/<int:character_id>', methods=['POST'])
def select_character(character_id):
    character = Character.query.get(character_id)
    if character:
        selected_character = {
            "name": character.name,
            "description": character.description
        }
        return jsonify(selected_character)
    return jsonify({"error": "Character not found"}), 404

@player_bp.route('/delete_character/<int:character_id>', methods=['POST'])
def delete_character(character_id):
    try:
        character = Character.query.get(character_id)
        db.session.delete(character)
        db.session.commit()
        return redirect(url_for('player_bp.player'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@player_bp.route('/create_character', methods=['POST'])
def create_character():
    try:
        name = request.form['name']
        description = request.form['description']
        new_character = Character(name=name, description=description, image_url='images/default/character.png', traits='{}')
        db.session.add(new_character)
        db.session.commit()
        return redirect(url_for('player_bp.player'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@player_bp.route('/send_message', methods=['POST'])
def send_message():
    try:
        content = request.form['message']
        user_id = 1  # Замените на идентификатор текущего пользователя
        message = Message(content=content, user_id=user_id)
        db.session.add(message)
        db.session.commit()
        return jsonify({"status": "Message sent"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@player_bp.route('/send_general_message', methods=['POST'])
def send_general_message():
    try:
        content = request.form['message']
        user_id = 1  # Замените на идентификатор текущего пользователя
        message = Message(content=content, user_id=user_id, general=True)
        db.session.add(message)
        db.session.commit()
        return jsonify({"status": "General message sent"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
