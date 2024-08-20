import json
import re
import asyncio
import os
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, current_app, g
from sqlalchemy import desc
from extensions import db
from models import Message, Character, Registrar, Player
from datetime import datetime
from gemini import GeminiAssistant
from utils import parse_character, save_to_json, load_from_json, name_to_filename, win_to_unix_path, generate_unixid
from load_user import load_user
from img_selector import IMGSelector
import logging
from config import Config
from default import default_current_character

conf = Config()
# --- player_routes.py ---
player_bp = Blueprint('player_bp', __name__)

@player_bp.before_request
def before_request():
    # Загрузка данных пользователя перед выполнением запроса
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

def get_selected_character():
    """Получение выбранного персонажа из файла или базы данных."""
    try:
        logger.info(f"----- cur_char ------: {g.user_id} CONF {conf.CURRENT_CHARACTER}")
        
        # Проверяем, есть ли сохраненный выбранный персонаж
        if g.user_id in conf.CURRENT_CHARACTER and conf.CURRENT_CHARACTER[g.user_id]:
            cur_char = conf.CURRENT_CHARACTER[g.user_id]
            selected_character_id = cur_char['player_id']
            logger.info(f"Selected character from CURRENT_CHARACTER: {selected_character_id}")
        else:
            # Если нет сохраненного персонажа, получаем последнего из списка персонажей пользователя
            data_list = Character.query.filter_by(user_id=g.user_id).order_by(desc(Character.id)).first()
            if data_list:
                selected_character_id = data_list.id
                logger.info(f"Selected last character from database: {selected_character_id}")
            else:
                # Если у пользователя нет персонажей, выбираем дефолтный
                selected_character_id = default_current_character()
                logger.info(f"No characters found. Using default character: {selected_character_id}")
        
        # Получаем данные о выбранном персонаже
        if selected_character_id:
            data = Character.query.filter_by(id=selected_character_id, user_id=g.user_id).first()
            logger.info(f"character_ID: {selected_character_id} data: {data}")
            return data

    except KeyError:
        logger.info("No user data available. Using default character.")
        selected_character_id = default_current_character()
        return Character.query.filter_by(id=selected_character_id, user_id=g.user_id).first()

    return None

@player_bp.route('/')
def player():
    logger.info("Fetching player data")

    # Получаем выбранного персонажа
    selected_character = get_selected_character()

    # Загружаем все сообщения и всех персонажей пользователя
    messages = fetch_records(Message, order_by_field=Message.timestamp)
    characters_data = fetch_records(Character)

    # Логируем traits для каждого персонажа
    for character in characters_data:
        logger.info(f"Character {character.name} has traits: {character.traits}")

    # Если выбранный персонаж не найден, выбираем последнего персонажа в списке
    if not selected_character and characters_data:
        selected_character = characters_data[-1]
        logger.info(f"Selected last character in the list: {selected_character.name}")

    if selected_character:
        logger.info(f"-----START 3------ character {selected_character.id} | {selected_character}")
        last_character_id = selected_character.id
    else:
        logger.info("No characters available.")
        last_character_id = None

    return render_template('player.html', 
                           messages=messages, 
                           characters=characters_data, 
                           selected_character=selected_character, 
                           last_character_id=last_character_id)



@player_bp.route('/arena')
def arena():
    logger.info(f"-----START------ User {user_id} character {selected_character.id} ")
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

    logger.info(f"-----START 1------ User {user_id} character {selected_character.id} ")


    return render_template('arena.html', selected_character=selected_character, enumerate=enumerate)

#===============================
@player_bp.route('/select_character/<int:character_id>', methods=['POST'])
def select_character(character_id):
    logger.info(f"--------------- character_id: {character_id} | character = Character.query.get(character_id)")
    try:
        logger.info(f"Selecting --- character ID: {character_id} for user: {g.user_id}")
        character = Character.query.get(character_id)
        if not character or character.user_id != g.user_id:
            return jsonify({"error": "Character not found or access denied"}), 404

        #player = get_or_create_player()
        player.selected_character_id = character_id
        db.session.commit()
        logger.info(f"select_character --------- character_id: {character_id} | {character} | TR: {character.traits}")
        selected_character = {
            "name": character.name,
            "description": character.description,
            "Life":character.life,
            "Combat":character.combat,
            "Damage":character.damage,
            "traits": json.loads(character.traits),
            "image_url": character.image_url
        }
        conf.CURRENT_CHARACTER[g.user_id] = selected_character
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
        #logger.info(f"Raw JSON from assistant response: {response}")
        parsed_character = parse_character(response)
        
        if parsed_character["name"]:
            traits = {}
            for chkey in parsed_character:
                if chkey != 'name' and  chkey != 'description' and chkey != 'type':
                    traits[chkey] = parsed_character[chkey]
                    
            traits_json = json.dumps(traits, ensure_ascii=False)       
            logger.info(f"====== traits_json: =========== {traits_json}")
            
            parsed_character['traits'] = traits_json
            designer = IMGSelector()
            player_id = generate_unixid()
                                                                # create     character                           
            path_img_file = designer.selector(user_id, player_id, '', theme_img='character', _name=parsed_character['name'], _prompt=parsed_character['description'])
 
            parsed_character['image_url'] = path_img_file
            parsed_character['user_id'] = user_id
            parsed_character['player_id'] = player_id
            parsed_character['life'] = 100
            parsed_character['combat'] = 0
            parsed_character['damage'] = 0
            
            conf.CURRENT_CHARACTER[user_id] = parsed_character
            # Логируем путь к изображению для проверки
            logger.info(f"Image path: {path_img_file}")
            
            return jsonify({
                "status": "Message sent",
                "response": response,
                "character": parsed_character,
                "image_url": path_img_file
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
            return jsonify({"status": "Character deleted", "character_id": character_id})
        return jsonify({"error": "Character not found or access denied"}), 404
    except Exception as e:
        logger.error(f"Error deleting character: {e}")
        return jsonify({"error": str(e)}), 500


@player_bp.route('/create_character', methods=['POST'])
def create_character():
    try:
        character_data = conf.CURRENT_CHARACTER[g.user_id]
        name = request.form['name']
        description = request.form['description']
        
        new_character = Character(
            name=name,
            description=description,
            image_url=character_data.get('image_url'),
            traits=character_data.get('traits'),
            user_id=g.user_id,
            player_id=character_data.get('player_id'),
            life=100,
            combat=0,
            damage=0
        )
        db.session.add(new_character)
        db.session.commit()

        logger.info(f"Created new character: {name} with image {character_data.get('image_url')}")

        # Возвращаем данные нового персонажа
        return jsonify({
            "status": "Character created",
            "character": {
                "id": new_character.id,
                "name": new_character.name,
                "description": new_character.description,
                "traits": json.loads(new_character.traits),
                "image_url": new_character.image_url
            }
        })
    except Exception as e:
        logger.error(f"Error creating character: {e}")
        return jsonify({"error": "Internal server error"}), 500


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
