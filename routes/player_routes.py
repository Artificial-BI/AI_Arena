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
#from core import BattleManager
import os

# --- player_routes.py ---
player_bp = Blueprint('player_bp', __name__)

@player_bp.before_request
def before_request():
    response = load_user()
    if response.status_code != 200 and response.status_code != 201:
        return response
    
    # Извлекаем данные пользователя из ответа
    user_data = response.get_json()
    g.user_id = user_data.get('user_id')
    g.cookie_id = user_data.get('cookie_id')


# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper functions
def fetch_messages():
    try:
        return Message.query.filter_by(user_id=g.user_id).order_by(Message.timestamp.asc()).all()
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        return []

def fetch_characters():
    try:
        return Character.query.filter_by(user_id=g.user_id).all()
    except Exception as e:
        logger.error(f"Error fetching characters: {e}")
        return []

def get_selected_character_from_file(user_id):
    try:
        with open('selected_characters.json', 'r') as f:
            data = json.load(f)
        return data.get(str(user_id))
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def set_selected_character_in_file(user_id, character_id):
    try:
        if os.path.exists('selected_characters.json'):
            with open('selected_characters.json', 'r') as f:
                data = json.load(f)
        else:
            data = {}

        data[str(user_id)] = character_id

        with open('selected_characters.json', 'w') as f:
            json.dump(data, f)
    except Exception as e:
        current_app.logger.error(f"Error saving selected character: {e}")

def get_selected_character():
    try:
        selected_character_id = get_selected_character_from_file(g.user_id)
        if selected_character_id:
            return Character.query.get(selected_character_id)
        else:
            return Character.query.filter_by(user_id=g.user_id).order_by(desc(Character.id)).first()
    except Exception as e:
        logger.error(f"Error fetching selected character: {e}")
        return None

def get_last_character_id():
    try:
        last_character = Character.query.filter_by(user_id=g.user_id).order_by(desc(Character.id)).first()
        return last_character.id if last_character else None
    except Exception as e:
        logger.error(f"Error fetching last character: {e}")
        return None

# Routes
@player_bp.route('/')
def player():
    logger.info("Fetching player data")
    
    # Загружаем выбранного персонажа из файла
    selected_character_id = get_selected_character_from_file(g.user_id)
    
    if selected_character_id:
        selected_character = Character.query.get(selected_character_id)
    else:
        selected_character = get_selected_character()

    messages = fetch_messages()
    characters = fetch_characters()
    last_character_id = selected_character.id if selected_character else get_last_character_id()

    return render_template('player.html', messages=messages, characters=characters, selected_character=selected_character, last_character_id=last_character_id)

@player_bp.route('/arena')
def arena():
    player = g.user.player  # Assuming that `g.user` has a relationship to `Player`
    selected_character = player.selected_character
    logging.info(f"+++++++ {selected_character} ++++++")
    if not selected_character:
        return render_template('error.html', error_message="Пожалуйста выберите персонажа или создайте с помощью ассистента")
    
    user_id = g.user_id
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
    try:
        logger.info(f"Selecting character ID: {character_id} for user: {g.user_id}")
        character = Character.query.get(character_id)
        if not character:
            logger.error(f"Character with ID {character_id} not found.")
            return jsonify({"error": "Character not found"}), 404

        if character.user_id != g.user_id:
            logger.error(f"Character ID {character_id} does not belong to user ID {g.user_id}.")
            return jsonify({"error": "Access denied"}), 403

        player = Player.query.filter_by(user_id=g.user_id).first()
        if not player:
            logger.error(f"Player not found for user ID {g.user_id}. Creating new player object.")
            player_name = f"Player_{g.user_id}"  # Присваиваем имя игрока
            player = Player(user_id=g.user_id, name=player_name)
            db.session.add(player)
            db.session.commit()

        logger.info(f"Updating player {player.id} to set selected_character_id to {character_id}")
        player.selected_character_id = character_id
        db.session.commit()

        set_selected_character_in_file(g.user_id, character_id)  # Сохраняем выбранного персонажа в файл

        # Логируем после коммита, чтобы убедиться, что изменение сохранено
        logger.info(f"After commit, player {player.id} has selected_character_id = {player.selected_character_id}")

        selected_character = {
            "name": character.name,
            "description": character.description,
            "traits": json.loads(character.traits)
        }
        return jsonify(selected_character)
    except Exception as e:
        db.session.rollback()  # Откатываем изменения в случае ошибки
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
        arena_id = 1  # Assuming a single arena for simplicity

        # Check if the character exists and belongs to the user
        character = Character.query.get(character_id)
        if not character or character.user_id != user_id:
            return jsonify({"error": "Invalid character ID"}), 400

        # Update or create registration
        existing_registration = Registrar.query.filter_by(user_id=user_id, arena_id=arena_id).first()

        if existing_registration:
            if existing_registration.character_id != character_id:
                existing_registration.character_id = character_id
                db.session.commit()  # Save changes
                logging.info(f"Updated registration for user {user_id} with new character {character_id} for arena {arena_id}")
                return jsonify({"status": "updated"})
            else:
                logging.info(f"User {user_id} already registered with character {character_id} for arena {arena_id}")
                return jsonify({"status": "already_registered"})
        else:
            new_registration = Registrar(user_id=user_id, character_id=character_id, arena_id=arena_id)
            db.session.add(new_registration)
            db.session.commit()  # Save changes
            logging.info(f"User {user_id} registered character {character_id} for arena {arena_id}")
            return jsonify({"status": "registered"})
    except Exception as e:
        db.session.rollback()  # Rollback transaction in case of error
        logging.error(f"Error registering for arena: {e}")
        return jsonify({"error": str(e)}), 500


@player_bp.route('/send_message', methods=['POST'])
def send_message():
    try:
        content = request.form.get('message', '').strip()
        if not content:
            raise ValueError("Invalid input: 'content' argument must not be empty. Please provide a non-empty value.")

        user_id = g.user_id  # Используем ID текущего пользователя

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
        if character and character.user_id == g.user_id:
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

        # Формирование пути к уже сгенерированному изображению
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
            raise ValueError("Invalid input: 'content' argument must not be empty. Please provide a non-empty value.")
            
        user_id = g.user_id  # Use the current user's ID
        message = Message(content=content, user_id=user_id)
        db.session.add(message)
        db.session.commit()
        logger.info(f"Sent general message: {content}")
        return jsonify({"status": "General message sent"})
    except Exception as e:
        logger.error(f"Error sending general message: {e}")
        return jsonify({"error": str(e)}), 500
