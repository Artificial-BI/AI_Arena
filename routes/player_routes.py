import json
import asyncio
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, g
from sqlalchemy import desc
from extensions import db
from models import Message, Character, Registrar, Player
from datetime import datetime
from gemini import GeminiAssistant
from utils import parse_character, generate_unixid
from load_user import load_user
from img_selector import IMGSelector
import logging
from config import Config
from default import default_current_character

conf = Config()
player_bp = Blueprint('player_bp', __name__)

@player_bp.before_request
def before_request():
    response = load_user()
    if response.status_code not in [200, 201]:
        return response
    user_data = response.get_json()
    g.user_id = user_data.get('user_id')
    g.cookie_id = user_data.get('cookie_id')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_records(model, order_by_field=None):
    try:
        query = model.query.filter_by(user_id=g.user_id)
        if order_by_field:
            query = query.order_by(order_by_field.asc())
        return query.all()
    except Exception as e:
        logger.error(f"Error fetching records from {model.__name__}: {e}")
        return []

def get_selected_character():
    """Получение выбранного персонажа из базы данных."""
    try:
        logger.info(f"Fetching selected character for user: {g.user_id}")
        
        # Получаем игрока по user_id
        player = Player.query.filter_by(user_id=g.user_id).first()
        
        if player and player.last_selected_character_id:
            # Если есть сохраненный выбранный персонаж, получаем его данные
            selected_character_id = player.last_selected_character_id
           # logger.info(f">> Selected character from Player table: {selected_character_id}")
        else:
            # Если нет сохраненного персонажа, получаем последнего из списка персонажей пользователя
            data_list = Character.query.filter_by(user_id=g.user_id).order_by(desc(Character.id)).first()
            if data_list:
                selected_character_id = data_list.character_id
              #  logger.info(f"Selected last character from database: {selected_character_id}")
            else:
                # Если у пользователя нет персонажей, выбираем дефолтный
                selected_character_id = default_current_character()
              #  logger.info(f"No characters found. Using default character: {selected_character_id}")
        
        # Получаем данные о выбранном персонаже
        if selected_character_id:
            character = Character.query.filter_by(character_id=selected_character_id, user_id=g.user_id).first()
            if character:
                selected_character = {
                    "character_id": character.character_id,  # Добавляем character_id
                    "name": character.name,
                    "description": character.description,
                    "Life": character.life,
                    "Combat": character.combat,
                    "Damage": character.damage,
                    "traits": json.loads(character.traits),
                    "image_url": character.image_url
                }
              #  logger.info(f"Character data loaded successfully: {selected_character}")
                return selected_character
            else:
                logger.error(f"Character with ID {selected_character_id} not found.")
                return None
    except Exception as e:
        logger.error(f"Error getting selected character: {e}")
        return None


@player_bp.route('/')
def player():
   # logger.info("Fetching player data")

    # Получаем выбранного персонажа
    selected_character_data = get_selected_character()

    # Загружаем все сообщения и всех персонажей пользователя
    messages = fetch_records(Message, order_by_field=Message.timestamp)
    characters_data = fetch_records(Character)

    # Логируем traits для каждого персонажа
    num = 0
    for character in characters_data:
       # logger.info(f"N: {num} Character: {character.character_id} | has traits: {character.traits}")
        num += 1
        
    if selected_character_data:
        last_character_id = selected_character_data.get("character_id")
        #last_character_id = selected_character_data.character_id
       # logger.info(f">>>>>> Current ID: {last_character_id} | {selected_character_data['traits']}")
    else:
        logger.info("No selected character found.")
        last_character_id = None

    # Логирование данных перед передачей в шаблон
   # logger.info(f"Selected Character Name: {selected_character_data.get('name')}")
   # logger.info(f"Selected Character Description: {selected_character_data.get('description')}")

    return render_template('player.html', 
                           messages=messages, 
                           characters=characters_data, 
                           last_character_id=last_character_id,
                           selected_character=selected_character_data)


@player_bp.route('/select_character/<int:character_num>', methods=['POST'])
def select_character(character_num):
   # logger.info(f"Selecting character: {character_num} for user: {g.user_id}")
    character = Character.query.get(character_num)
    if not character or character.user_id != g.user_id:
        return jsonify({"error": "Character not found or access denied"}), 404

    player = Player.query.filter_by(user_id=g.user_id).first()
    if player:
        player.last_selected_character_id = character.character_id
    else:
        player = Player(
            name=f"Player_{g.user_id}",
            user_id=g.user_id,
            last_selected_character_id=character.character_id
        )
        db.session.add(player)
    
    db.session.commit()

    selected_character = {
        "name": character.name,
        "description": character.description,
        "Life": character.life,
        "Combat": character.combat,
        "Damage": character.damage,
        "traits": json.loads(character.traits),
        "image_url": character.image_url
    }
    return jsonify(selected_character)

@player_bp.route('/create_character', methods=['POST'])
def create_character():
    try:
        character_data = conf.CURRENT_CHARACTER[g.user_id]
        name = request.form['name']
        description = request.form['description']
        character_id = character_data.get('character_id')
        new_character = Character(
            name=name,
            description=description,
            image_url=character_data.get('image_url'),
            traits=json.dumps(character_data.get('traits')),  # Преобразование в строку JSON
            user_id=g.user_id,
            character_id=character_id,
            life=100,
            combat=0,
            damage=0
        )
        db.session.add(new_character)
        db.session.commit()
        
        # Сохраняем ID выбранного персонажа в базу данных Player
        player = Player.query.filter_by(user_id=g.user_id).first()
        if player:
            player.last_selected_character_id = character_id
            db.session.commit()
       # logger.info(f"Created new character: {name} with image {character_data.get('image_url')}")

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

@player_bp.route('/delete_character/<int:character_id>', methods=['POST'])
def delete_character(character_id):
    try:
        character = Character.query.get(character_id)
        if character and character.user_id == g.user_id:
            db.session.delete(character)
            db.session.commit()
            logger.info(f"Deleted character: {character_id}")
            return jsonify({"status": "Character deleted", "character_id": character_id})
        else:
            return jsonify({"error": "Character not found or access denied"}), 404
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting character: {e}")
        return jsonify({"error": "Internal server error"}), 500


@player_bp.route('/send_message', methods=['POST'])
def send_message():
    content = request.form.get('message', '').strip()
    if not content:
        return jsonify({"error": "Invalid input: 'content' must not be empty."}), 400

    user_id = g.user_id
    assistant = GeminiAssistant("Character Generator")
   # logger.info(f"Sending message to assistant: {content}")
    response = asyncio.run(assistant.send_message(content))
   # logger.info(f"Received response from assistant: {response}")

    message = Message(content=content, user_id=user_id)
    db.session.add(message)
    db.session.commit()
    
    parsed_character = parse_character(response)
    if parsed_character["name"]:
        traits = {}
        for chkey in parsed_character:
            if chkey not in ['name', 'description', 'type']:
                traits[chkey] = parsed_character[chkey]
                
        parsed_character['traits'] = traits  # Вместо строки передаем объект
      #  logger.info(f"Traits dict: {traits}")
        
        designer = IMGSelector()
        character_id = generate_unixid()
        
        path_img_file = designer.selector(user_id, character_id, '', theme_img='character', _name=parsed_character['name'], _prompt=parsed_character['description'])
        
        parsed_character['image_url'] = path_img_file
        parsed_character['user_id'] = user_id
        parsed_character['character_id'] = character_id
        parsed_character['life'] = 100
        parsed_character['combat'] = 0
        parsed_character['damage'] = 0
        
        conf.CURRENT_CHARACTER[user_id] = parsed_character
       # logger.info(f"Image path: {path_img_file}")
        
        return jsonify({
            "status": "Message sent",
            "response": response,
            "character": parsed_character,
            "image_url": path_img_file
        })
    
    return jsonify({"status": "Message sent", "response": response})


@player_bp.route('/register_for_arena', methods=['POST'])
def register_for_arena():
    logger.info(f"----------register_for_arena------------")
    
    try:
        user_id = g.user_id

        # Получаем текущего выбранного персонажа для данного пользователя
        selected_character = Player.query.filter_by(user_id=user_id).first()
        if not selected_character or not selected_character.last_selected_character_id:
            return jsonify({"error": "No character selected"}), 400

        character_id = selected_character.last_selected_character_id

        # Проверяем, зарегистрирован ли уже персонаж для арены
        existing_registration = Registrar.query.filter_by(user_id=user_id, arena_id=1).first()
        if existing_registration:
            if existing_registration.character_id != character_id:
                existing_registration.character_id = character_id
                db.session.commit()
                return jsonify({"status": "updated"})
            return jsonify({"status": "already_registered"})
        else:
            # Добавляем новую регистрацию
            new_registration = Registrar(
                user_id=user_id, 
                character_id=character_id, 
                arena_id=1
            )
            db.session.add(new_registration)
            db.session.commit()
            return jsonify({"status": "registered"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error registering for arena: {e}")
        return jsonify({"error": "Internal server error"}), 500
