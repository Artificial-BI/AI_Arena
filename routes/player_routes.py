import json
import re
import asyncio
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, current_app, g
from sqlalchemy import desc
from extensions import db
from models import Message, Character, Registrar, Player
from datetime import datetime
from gemini import GeminiAssistant
import logging
from utils import parse_character, save_to_json
from load_user import load_user
from open_ai import AIDesigner
import os

# --- player_routes.py ---
player_bp = Blueprint('player_bp', __name__)

@player_bp.before_request
def before_request():
    response = load_user()
    if response.status_code not in [200, 201]:
        return response
    
    user_data = response.get_json()
    g.user_id = user_data.get('user_id')
    g.cookie_id = user_data.get('cookie_id')

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper functions
def fetch_records(model, order_by_field=None):
    """Универсальная функция для получения записей из базы данных с фильтрацией по user_id."""
    try:
        query = model.query.filter_by(user_id=g.user_id)
        if order_by_field:
            query = query.order_by(order_by_field.asc())
        return query.all()
    except Exception as e:
        logger.error(f"Error fetching records from {model.__name__}: {e}")
        return []

def manage_selected_character_in_file(user_id, character_id=None, action="get"):
    """Управление сохранением и получением выбранного персонажа в/из файла."""
    try:
        file_path = 'selected_characters.json'
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
        else:
            data = {}

        if action == "set" and character_id is not None:
            data[str(user_id)] = character_id
            with open(file_path, 'w') as f:
                json.dump(data, f)
        return data.get(str(user_id))
    except Exception as e:
        logger.error(f"Error managing selected character in file: {e}")
        return None

def get_selected_character():
    """Получение выбранного персонажа из файла или базы данных."""
    selected_character_id = manage_selected_character_in_file(g.user_id)
    if selected_character_id:
        return Character.query.get(selected_character_id)
    return Character.query.filter_by(user_id=g.user_id).order_by(desc(Character.id)).first()

def get_or_create_player():
    """Получение или создание игрока в базе данных."""
    player = Player.query.filter_by(user_id=g.user_id).first()
    if not player:
        player_name = f"Player_{g.user_id}"
        player = Player(user_id=g.user_id, name=player_name)
        db.session.add(player)
        db.session.commit()
    return player

# Routes
@player_bp.route('/')
def player():
    logger.info("Fetching player data")

    selected_character = get_selected_character()
    messages = fetch_records(Message, order_by_field=Message.timestamp)
    characters = fetch_records(Character)
    last_character_id = selected_character.id if selected_character else None

    # Добавление значений Combat, Damage, Life в traits
    characters_data = []
    for character in characters:
        traits = json.loads(character.traits) if character.traits else {}
        traits.update({
            "Combat": character.combat,
            "Damage": character.damage,
            "Life": character.life
        })
        characters_data.append({
            "id": character.id,
            "name": character.name,
            "description": character.description,
            "traits": traits,
            "image_url": character.image_url
        })

    logger.info(f"Characters data: {characters_data}")  # Логируем данные для проверки

    return render_template('player.html', messages=messages, characters=characters, selected_character=selected_character, last_character_id=last_character_id)

@player_bp.route('/arena')
def arena():
    player = get_or_create_player()
    selected_character = player.selected_character
    if not selected_character:
        return render_template('error.html', error_message="Пожалуйста выберите персонажа или создайте с помощью ассистента")

    user_id = g.user_id
    arena_id = 1
    existing_registration = Registrar.query.filter_by(user_id=user_id, arena_id=arena_id).first()

    if existing_registration:
        if existing_registration.character_id != selected_character.id:
            existing_registration.character_id = selected_character.id
            db.session.commit()
            logger.info(f"Updated registration for user {user_id} with new character {selected_character.id} for arena {arena_id}")
    else:
        new_registration = Registrar(user_id=user_id, character_id=selected_character.id, arena_id=arena_id)
        db.session.add(new_registration)
        db.session.commit()
        logger.info(f"User {user_id} registered character {selected_character.id} for arena {arena_id}")

    return render_template('arena.html', selected_character=selected_character, enumerate=enumerate)

@player_bp.route('/select_character/<int:character_id>', methods=['POST'])
def select_character(character_id):
    try:
        logger.info(f"Selecting character ID: {character_id} for user: {g.user_id}")
        character = Character.query.get(character_id)
        if not character or character.user_id != g.user_id:
            return jsonify({"error": "Character not found or access denied"}), 404

        player = get_or_create_player()
        player.selected_character_id = character_id
        db.session.commit()

        manage_selected_character_in_file(g.user_id, character_id, action="set")

        selected_character = {
            "name": character.name,
            "description": character.description,
            "traits": json.loads(character.traits)
        }
        return jsonify(selected_character)
    except Exception as e:
        db.session.rollback()
        logger.error(f"An error occurred: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@player_bp.route('/register_for_arena', methods=['POST'])
def register_for_arena():
    try:
        data = request.get_json()
        character_id = data.get('character_id')
        if not character_id:
            return jsonify({"error": "Character ID is required"}), 400

        user_id = g.user_id
        arena_id = 1
        character = Character.query.get(character_id)
        if not character or character.user_id != user_id:
            return jsonify({"error": "Invalid character ID"}), 400

        existing_registration = Registrar.query.filter_by(user_id=user_id, arena_id=arena_id).first()
        if existing_registration:
            if existing_registration.character_id != character_id:
                existing_registration.character_id = character_id
                db.session.commit()
                return jsonify({"status": "updated"})
            return jsonify({"status": "already_registered"})
        else:
            new_registration = Registrar(user_id=user_id, character_id=character_id, arena_id=arena_id)
            db.session.add(new_registration)
            db.session.commit()
            return jsonify({"status": "registered"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error registering for arena: {e}")
        return jsonify({"error": str(e)}), 500

@player_bp.route('/send_message', methods=['POST'])
def send_message():
    try:
        content = request.form.get('message', '').strip()
        if not content:
            return jsonify({"error": "Invalid input: 'content' must not be empty."}), 400

        user_id = g.user_id
        assistant = GeminiAssistant("Character Generator")
        logger.info(f"Sending message to assistant: {content}")
        response = asyncio.run(assistant.send_message(content))
        logger.info(f"Received response from assistant: {response}")

        message = Message(content=content, user_id=user_id)
        db.session.add(message)
        db.session.commit()

        parsed_character = parse_character(response)
        if parsed_character["name"]:
            designer = AIDesigner()
            filename = re.sub(r'[\\/*?:"<>|]', "", parsed_character['name'].replace(" ", "_"))
            image_filename = f"{filename}.png"
            path_img_file = designer.create_image(parsed_character['description'], f"user_{user_id}", image_filename)
            parsed_character['image_url'] = path_img_file
           
            
            save_to_json(parsed_character)

            return jsonify({
                "status": "Message sent",
                "response": response,
                "character": parsed_character,
                "image_url": parsed_character['image_url']
            })

        return jsonify({"status": "Message sent", "response": response})
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return jsonify({"error": str(e)}), 500

@player_bp.route('/delete_character/<int:character_id>', methods=['POST'])
def delete_character(character_id):
    try:
        character = Character.query.get(character_id)
        if character and character.user_id == g.user_id:
            db.session.delete(character)
            db.session.commit()
            logger.info(f"Deleted character: {character_id}")
            return redirect(url_for('player_bp.player'))
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
            if ':' in item:
                key, value = item.split(':')
                try:
                    traits[key] = int(value)
                except ValueError:
                    traits[key] = 0  # Если значение не является числом, используем 0 по умолчанию

        traits_json = json.dumps(traits, ensure_ascii=False)
        filename = re.sub(r'[\\/*?:"<>|]', "", name.replace(" ", "_"))
        image_filename = f"{filename}.png"
        image_url = f"images/user_{g.user_id}/{image_filename}"

        new_character = Character(name=name, description=description, image_url=image_url, traits=traits_json, user_id=g.user_id)
        db.session.add(new_character)
        db.session.commit()

        logger.info(f"Created new character: {name} with image {image_url}")
        return redirect(url_for('player_bp.player'))
    except Exception as e:
        logger.error(f"Error creating character: {e}")
        return jsonify({"error": str(e)}), 500


@player_bp.route('/send_general_message', methods=['POST'])
def send_general_message():
    try:
        content = request.form.get('message', '').strip()
        if not content:
            return jsonify({"error": "Invalid input: 'content' must not be empty."}), 400

        user_id = g.user_id
        message = Message(content=content, user_id=user_id)
        db.session.add(message)
        db.session.commit()
        logger.info(f"Sent general message: {content}")
        return jsonify({"status": "General message sent"})
    except Exception as e:
        logger.error(f"Error sending general message: {e}")
        return jsonify({"error": str(e)}), 500
