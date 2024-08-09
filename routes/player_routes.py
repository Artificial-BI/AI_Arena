import json
import re
import asyncio
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, current_app, g
from sqlalchemy import desc
from extensions import db
from models import Message, Character, User, Registrar
from datetime import datetime
from gemini import GeminiAssistant
import logging
from utils import parse_character, save_to_json
from load_user import load_user
from open_ai import AIDesigner

# --- player_routes.py ---
player_bp = Blueprint('player_bp', __name__)

@player_bp.before_request
def before_request():
    response = load_user()
    if response:
        return response

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper functions
def fetch_messages():
    try:
        return Message.query.filter_by(user_id=g.user.id).order_by(Message.timestamp.asc()).all()
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        return []

def fetch_characters():
    try:
        return Character.query.filter_by(user_id=g.user.id).all()
    except Exception as e:
        logger.error(f"Error fetching characters: {e}")
        return []

def get_selected_character():
    try:
        return Character.query.filter_by(user_id=g.user.id).order_by(desc(Character.id)).first()
    except Exception as e:
        logger.error(f"Error fetching selected character: {e}")
        return None

def get_last_character_id():
    try:
        last_character = Character.query.filter_by(user_id=g.user.id).order_by(desc(Character.id)).first()
        return last_character.id if last_character else None
    except Exception as e:
        logger.error(f"Error fetching last character: {e}")
        return None

# Routes
@player_bp.route('/')
def player():
    logger.info("Fetching player data")
    messages = fetch_messages()
    characters = fetch_characters()
    selected_character = get_selected_character()
    last_character_id = get_last_character_id()

    return render_template('player.html', messages=messages, characters=characters, selected_character=selected_character, last_character_id=last_character_id)

@player_bp.route('/arena')
def arena():
    selected_character = get_selected_character()
    if not selected_character:
        return render_template('error.html', error_message="Пожалуйста выберите персонажа или создайте с помощью ассистента")
    
    user_id = g.user.id
    arena_id = 1  # Assuming a single arena for simplicity
    existing_registration = Registrar.query.filter_by(user_id=user_id, arena_id=arena_id).first()
    
    if existing_registration:
        if existing_registration.character_id != selected_character.id:
            existing_registration.character_id = selected_character.id
            db.session.commit()
            logging.info(f"Updated registration for user {user_id} with new character {selected_character.id} for arena {arena_id}")
    else:
        new_registration = Registrar(user_id=user_id, character_id=selected_character.id, arena_id=arena_id)
        db.session.add(new_registration)
        db.session.commit()
        logging.info(f"User {user_id} registered character {selected_character.id} for arena {arena_id}")

    return render_template('arena.html', selected_character=selected_character, enumerate=enumerate)

@player_bp.route('/select_character/<int:character_id>', methods=['POST'])
def select_character(character_id):
    character = Character.query.get(character_id)
    if character and character.user_id == g.user.id:
        selected_character = {
            "name": character.name,
            "description": character.description,
            "traits": json.loads(character.traits)
        }
        logger.info(f"Selected character: {selected_character}")
        return jsonify(selected_character)
    logger.error(f"Character not found or access denied: {character_id}")
    return jsonify({"error": "Character not found or access denied"}), 404



@player_bp.route('/send_message', methods=['POST'])
def send_message():
    try:
        content = request.form.get('message', '').strip()
        if not content:
            raise ValueError("Invalid input: 'content' argument must not be empty. Please provide a non-empty value.")

        user_id = g.user.id  # Используем ID текущего пользователя

        # Создаем ассистента
        assistant = GeminiAssistant("Character Generator")
        logger.info(f"Отправка сообщения ассистенту: {content}")
        response = asyncio.run(assistant.send_message(content))
        logger.info(f"Ответ от ассистента: {response}")

        # Сохраняем сообщение и ответ в базе данных
        message = Message(content=content, user_id=user_id)
        response_message = Message(content=response, user_id=user_id)
        db.session.add(message)
        db.session.commit()

        # Парсим ответ и возвращаем данные персонажа, если они присутствуют
        parsed_character = parse_character(response)
        if parsed_character["name"]:
            # Генерация изображения персонажа
            designer = AIDesigner()
            
            # Очистка имени файла от недопустимых символов
            filename = re.sub(r'[\\/*?:"<>|]', "", parsed_character['name'].replace(" ", "_"))
            
            image_filename = f"{filename}.png"
            path_img_file = designer.create_image(parsed_character['description'], f"user_{user_id}", image_filename)

            # Обновляем URL изображения в структуре персонажа
            parsed_character['image_url'] = f"images/user_{user_id}/{image_filename}"
            save_to_json(parsed_character)

            return jsonify({
                "status": "Message sent",
                "response": response,
                "character": parsed_character,
                "image_url": parsed_character['image_url']
            })

        return jsonify({"status": "Message sent", "response": response})
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        return jsonify({"error": str(e)}), 500


@player_bp.route('/delete_character/<int:character_id>', methods=['POST'])
def delete_character(character_id):
    try:
        character = Character.query.get(character_id)
        if character and character.user_id == g.user.id:
            db.session.delete(character)
            db.session.commit()
            logger.info(f"Deleted character: {character_id}")
            return redirect(url_for('player_bp.player'))
        else:
            return jsonify({"error": "Character not found or access denied"}), 404
    except Exception as e:
        logger.error(f"Error deleting character: {e}")
        return jsonify({"error": str(e)}), 500

@player_bp.route('/create_character', methods=['POST'])
def create_character():
    try:
        name = request.form['name']
        description = request.form['description']
        traits_string = request.form['extraInput']

        traits = {}
        for item in traits_string.split(', '):
            key, value = item.split(':')
            try:
                traits[key] = int(value)
            except ValueError:
                traits[key] = 0

        traits_json = json.dumps(traits, ensure_ascii=False)

        new_character = Character(name=name, description=description, image_url='images/default/character.png', traits=traits_json, user_id=g.user.id)
        db.session.add(new_character)
        db.session.commit()
        logger.info(f"Created new character: {name}")
        return redirect(url_for('player_bp.player'))
    except Exception as e:
        logger.error(f"Error creating character: {e}")
        return jsonify({"error": str(e)}), 500

@player_bp.route('/send_general_message', methods=['POST'])
def send_general_message():
    try:
        content = request.form.get('message', '').strip()
        if not content:
            raise ValueError("Invalid input: 'content' argument must not be empty. Please provide a non-empty value.")
            
        user_id = g.user.id  # Use the current user's ID
        message = Message(content=content, user_id=user_id)
        db.session.add(message)
        db.session.commit()
        logger.info(f"Sent general message: {content}")
        return jsonify({"status": "General message sent"})
    except Exception as e:
        logger.error(f"Error sending general message: {e}")
        return jsonify({"error": str(e)}), 500
    
@player_bp.route('/register_for_arena', methods=['POST'])
def register_for_arena():
    try:
        data = request.get_json()
        character_id = data.get('character_id')
        
        if not character_id:
            return jsonify({"error": "Character ID is required"}), 400
        
        user_id = g.user.id
        arena_id = 1  # Assuming a single arena for simplicity

        existing_registration = Registrar.query.filter_by(user_id=user_id, arena_id=arena_id).first()
        
        if existing_registration:
            if existing_registration.character_id != character_id:
                existing_registration.character_id = character_id
                db.session.commit()
                logging.info(f"Updated registration for user {user_id} with new character {character_id} for arena {arena_id}")
                return jsonify({"status": "updated"})
            else:
                logging.info(f"User {user_id} already registered with character {character_id} for arena {arena_id}")
                return jsonify({"status": "already_registered"})
        else:
            new_registration = Registrar(user_id=user_id, character_id=character_id, arena_id=arena_id)
            db.session.add(new_registration)
            db.session.commit()
            logging.info(f"User {user_id} registered character {character_id} for arena {arena_id}")
            return jsonify({"status": "registered"})
    except Exception as e:
        logging.error(f"Error registering for arena: {e}")
        return jsonify({"error": str(e)}), 500
