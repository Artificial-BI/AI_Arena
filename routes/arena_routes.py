# --- arena_routes.py ---
from flask import Blueprint, render_template, jsonify, request, g
from models import Character, ArenaChatMessage, GeneralChatMessage, TacticsChatMessage, User, Registrar, Arena
import logging
import json
from extensions import db
import uuid
from core import BattleManager
from tactics_manager import TacticsManager  # Импорт нового модуля тактик
from gemini import GeminiAssistant  # Assuming GeminiAssistant is the assistant used for tactics and fighters
import asyncio

arena_bp = Blueprint('arena', __name__)
battle_manager = BattleManager()
tactics_manager = TacticsManager()

@arena_bp.before_request
def before_request():
    user_id = request.cookies.get('user_id')
    if not user_id:
        user_id = str(uuid.uuid4())
        new_user = User(cookie_id=user_id)
        db.session.add(new_user)
        db.session.commit()
        g.user = new_user
    else:
        g.user = User.query.filter_by(cookie_id=user_id).first()
        if not g.user:
            new_user = User(cookie_id=user_id)
            db.session.add(new_user)
            db.session.commit()
            g.user = new_user

@arena_bp.route('/')
def arena():
    selected_character = Character.query.filter_by(user_id=g.user.id).order_by(Character.id.desc()).first()
    if not selected_character:
        return "Пожалуйста выберите персонажа или создайте с помощью ассистента"
    
    characters = Character.query.order_by(Character.id.desc()).limit(2).all()
    
    # Register the selected character for the arena
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

    return render_template('arena.html', characters=characters, selected_character=selected_character, enumerate=enumerate)

@arena_bp.route('/get_characters')
def get_characters():
    try:
        characters = Character.query.order_by(Character.id.desc()).limit(2).all()
        characters_data = []
        for character in characters:
            traits = json.loads(character.traits)
            characters_data.append({
                'name': character.name,
                'description': character.description,
                'image_url': character.image_url,
                'stats': {
                    'Health': traits.get('Health', 0),
                    'Intelligence': traits.get('Intelligence', 0),
                    'Strength': traits.get('Strength', 0),
                    'Magic': traits.get('Magic', 0),
                    'Attack': traits.get('Attack', 0),
                    'Defense': traits.get('Defense', 0),
                    'Speed': traits.get('Speed', 0),
                    'Agility': traits.get('Agility', 0),
                    'Endurance': traits.get('Endurance', 0),
                    'Luck': traits.get('Luck', 0),
                    'Charisma': traits.get('Charisma', 0)
                }
            })
        return jsonify(characters_data)
    except Exception as e:
        logging.error(f"Error fetching characters: {e}")
        return jsonify({"error": "Internal server error"}), 500

@arena_bp.route('/get_arena_chat')
def get_arena_chat():
    try:
        user_id = g.user.id
        messages = ArenaChatMessage.query.filter_by(user_id=user_id).order_by(ArenaChatMessage.timestamp.asc()).all()
        chat_data = [{'content': msg.content, 'timestamp': msg.timestamp, 'sender': msg.sender, 'user_id': msg.user_id} for msg in messages]
        return jsonify(chat_data)
    except Exception as e:
        logging.error(f"Error fetching arena chat messages: {e}")
        return jsonify({"error": "Internal server error"}), 500

@arena_bp.route('/send_arena_chat', methods=['POST'])
def send_arena_chat():
    try:
        data = request.get_json()
        content = data.get('content')
        sender = data.get('sender')
        user_id = data.get('user_id')
        if not content or not sender or not user_id:
            return jsonify({"error": "Invalid data"}), 400

        message = ArenaChatMessage(content=content, sender=sender, user_id=user_id)
        db.session.add(message)
        db.session.commit()
        return jsonify({"status": "Message sent"}), 200
    except Exception as e:
        logging.error(f"Error saving arena chat message: {e}")
        return jsonify({"error": "Internal server error"}), 500

@arena_bp.route('/get_general_chat')
def get_general_chat():
    try:
        user_id = g.user.id
        messages = GeneralChatMessage.query.filter_by(user_id=user_id).order_by(GeneralChatMessage.timestamp.asc()).all()
        chat_data = [{'content': msg.content, 'timestamp': msg.timestamp, 'sender': msg.sender, 'user_id': msg.user_id} for msg in messages]
        return jsonify(chat_data)
    except Exception as e:
        logging.error(f"Error fetching general chat messages: {e}")
        return jsonify({"error": "Internal server error"}), 500

@arena_bp.route('/send_general_chat', methods=['POST'])
def send_general_chat():
    try:
        data = request.get_json()
        content = data.get('content')
        sender = data.get('sender')
        user_id = data.get('user_id')
        if not content or not sender or not user_id:
            return jsonify({"error": "Invalid data"}), 400

        message = GeneralChatMessage(content=content, sender=sender, user_id=user_id)
        db.session.add(message)
        db.session.commit()
        return jsonify({"status": "Message sent"}), 200
    except Exception as e:
        logging.error(f"Error saving general chat message: {e}")
        return jsonify({"error": "Internal server error"}), 500

@arena_bp.route('/get_tactics_chat')
def get_tactics_chat():
    try:
        user_id = g.user.id
        messages = TacticsChatMessage.query.filter_by(user_id=user_id).order_by(TacticsChatMessage.timestamp.asc()).all()
        chat_data = [{'content': msg.content, 'timestamp': msg.timestamp, 'sender': msg.sender, 'user_id': msg.user_id} for msg in messages]
        return jsonify(chat_data)
    except Exception as e:
        logging.error(f"Error fetching tactics chat messages: {e}")
        return jsonify({"error": "Internal server error"}), 500

@arena_bp.route('/send_tactics_chat', methods=['POST'])
def send_tactics_chat():
    try:
        data = request.get_json()
        content = data.get('content')
        sender = data.get('sender')
        user_id = data.get('user_id')
        if not content or not sender or not user_id:
            return jsonify({"error": "Invalid data"}), 400

        message = TacticsChatMessage(content=content, sender=sender, user_id=user_id)
        db.session.add(message)
        db.session.commit()
        return jsonify({"status": "Message sent"}), 200
    except Exception as e:
        logging.error(f"Error saving tactics chat message: {e}")
        return jsonify({"error": "Internal server error"}), 500

@arena_bp.route('/start_test_battle', methods=['POST'])
async def start_test_battle():
    logging.info("Получен запрос на начало тестовой битвы")
    try:
        asyncio.create_task(tactics_manager.generate_tactics())
        await battle_manager.start_test_battle()
        logging.info("Тестовая битва успешно началась")
        return jsonify({'status': 'Тестовая битва началась'}), 200
    except Exception as e:
        logging.error(f"Ошибка при запуске тестовой битвы: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@arena_bp.route('/generate_fighter_move', methods=['POST'])
async def generate_fighter_move():
    logging.info("Получен запрос на создание хода бойца")
    try:
        user_id = g.user.id
        registrar = Registrar.query.filter_by(user_id=user_id).first()
        if not registrar:
            logging.error("Пользователь не зарегистрирован на арене")
            return jsonify({"error": "Пользователь не зарегистрирован на арене"}), 400

        character = Character.query.get(registrar.character_id)
        arena = Arena.query.get(registrar.arena_id)
        
        if not character or not arena:
            logging.error("Персонаж или арена не найдены")
            return jsonify({"error": "Персонаж или арена не найдены"}), 400

        # Получение последнего сообщения тактика
        tactics_message = TacticsChatMessage.query.filter_by(user_id=user_id).order_by(TacticsChatMessage.timestamp.desc()).first()
        tactics_content = tactics_message.content if tactics_message else ""

        # Получение последнего сообщения игрока
        player_message = GeneralChatMessage.query.filter_by(user_id=user_id).order_by(GeneralChatMessage.timestamp.desc()).first()
        player_content = player_message.content if player_message else ""

        # Конструирование запроса для ассистента бойца
        prompt = f"Атмосфера арены: {arena.description}\n"
        prompt += f"Параметры арены: {arena.parameters}\n\n"
        prompt += f"Имя персонажа: {character.name}\n"
        prompt += f"Характеристики персонажа: {character.traits}\n\n"
        prompt += f"Совет тактика: {tactics_content}\n"
        prompt += f"Ввод игрока: {player_content}\n\n"
        prompt += "Сгенерируйте следующий ход персонажа на основе вышеуказанной информации."

        # Создание ассистента и получение ответа
        assistant = GeminiAssistant("fighter")
        response = await assistant.send_message(prompt)

        if not response.strip():
            logging.error("Получен пустой ответ от ассистента")
            return jsonify({"error": "Получен пустой ответ от ассистента"}), 500

        # Сохранение хода бойца в чат арены
        fighter_move = ArenaChatMessage(content=response, sender="fighter", user_id=user_id, arena_id=arena.id)
        db.session.add(fighter_move)
        db.session.commit()

        logging.info("Ход бойца успешно создан")
        return jsonify({"status": "Ход бойца успешно создан", "response": response}), 200
    except Exception as e:
        logging.error(f"Ошибка при создании хода бойца: {e}")
        return jsonify({"error": str(e)}), 500
