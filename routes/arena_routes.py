import nest_asyncio
import asyncio
from flask import Blueprint, render_template, jsonify, request, g,  url_for
from models import Character, ArenaChatMessage, GeneralChatMessage, TacticsChatMessage, User, Registrar, Arena
import logging
import json
from extensions import db
from core import BattleManager
from load_user import load_user

# --- arena_routes.py ---
nest_asyncio.apply()

arena_bp = Blueprint('arena', __name__)
battle_manager = BattleManager()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@arena_bp.before_request
def before_request():
    response = load_user()
    if response.status_code != 200 and response.status_code != 201:
        return response
    
    # Извлекаем данные пользователя из ответа
    user_data = response.get_json()
    g.user_id = user_data.get('user_id')
    g.cookie_id = user_data.get('cookie_id')

@arena_bp.route('/')
def arena():
    selected_character = Character.query.filter_by(user_id=g.user_id).order_by(Character.id.desc()).first()
    if not selected_character:
        return "Пожалуйста выберите персонажа или создайте с помощью ассистента"

    user_id = g.user_id
    logger.info(f"Current user_id: {user_id}")
    arena_id = 1
    
    # Получение самой последней арены по дате создания
    arena = Arena.query.order_by(Arena.date_created.desc()).first()
    arena_image_url = arena.image_url if arena else None

    registrations = Registrar.query.all()
    characters = [Character.query.get(registration.character_id) for registration in registrations]
    
    return render_template('arena.html', characters=characters, selected_character=selected_character, arena_image_url=arena_image_url, enumerate=enumerate)


@arena_bp.route('/get_registered_characters')
def get_registered_characters():
    try:
        registrations = Registrar.query.all()
        characters = [
            {
                "user_id": registration.user_id,
                "name": Character.query.get(registration.character_id).name,
                "traits": json.loads(Character.query.get(registration.character_id).traits),
                "image_url": Character.query.get(registration.character_id).image_url,  # Используем URL из базы данных
                "description": Character.query.get(registration.character_id).description
            }
            for registration in registrations if Character.query.get(registration.character_id) is not None
        ]
        return jsonify(characters)
    except Exception as e:
        logger.error(f"Error fetching registered characters: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@arena_bp.route('/get_arena_chat')
def get_arena_chat():
    try:
        messages = ArenaChatMessage.query.order_by(ArenaChatMessage.timestamp.asc()).all()
        chat_data = [{'content': msg.content, 'timestamp': msg.timestamp, 'sender': msg.sender, 'user_id': msg.user_id} for msg in messages]
        return jsonify(chat_data)
    except Exception as e:
        logger.error(f"Error fetching arena chat messages: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@arena_bp.route('/get_general_chat')
def get_general_chat():
    try:
        messages = GeneralChatMessage.query.order_by(GeneralChatMessage.timestamp.asc()).all()
        chat_data = [{'content': msg.content, 'timestamp': msg.timestamp, 'sender': msg.sender, 'user_id': msg.user_id} for msg in messages]
        return jsonify(chat_data)
    except Exception as e:
        logger.error(f"Error fetching general chat messages: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@arena_bp.route('/get_tactics_chat')
def get_tactics_chat():
    try:
        messages = TacticsChatMessage.query.order_by(TacticsChatMessage.timestamp.asc()).all()
        chat_data = [{'content': msg.content, 'timestamp': msg.timestamp, 'sender': msg.sender, 'user_id': msg.user_id} for msg in messages]
        return jsonify(chat_data)
    except Exception as e:
        logger.error(f"Error fetching tactics chat messages: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@arena_bp.route('/check_registered_players', methods=['GET'])
def check_registered_players():
    try:
        battle_in_progress = battle_manager.battle_in_progress
        timer_in_progress = battle_manager.timer_in_progress
        remaining_time = battle_manager.get_remaining_time()
        registered_players = Registrar.query.count()
        
        return jsonify({
            'battle_in_progress': battle_in_progress,
            'timer_in_progress': timer_in_progress,
            'remaining_time': remaining_time,
            'registered_players': registered_players
        }), 200
    except Exception as e:
        logger.error(f"Ошибка при проверке количества зарегистрированных игроков: {e}", exc_info=True)
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@arena_bp.route('/start_timer', methods=['POST'])
def start_timer():
    if battle_manager.battle_in_progress or battle_manager.timer_in_progress:
        return jsonify({"error": "Битва уже идет или таймер уже запущен"}), 400
    
    battle_manager.start_timer(30)
    return jsonify({'status': 'Таймер запущен'}), 200

@arena_bp.route('/get_timer', methods=['GET'])
def get_timer():
    remaining_time = battle_manager.get_remaining_time()
    return jsonify({'remaining_time': remaining_time}), 200

@arena_bp.route('/start_battle', methods=['POST'])
def start_battle():
    logger.info("Запрос на старт битвы получен")
    try:
        # Вместо создания нового событийного цикла, используем текущий
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Если цикл уже запущен, просто создаем задачу
            asyncio.create_task(battle_manager.start_battle(g.user_id))
        else:
            # Если цикл не запущен, запускаем его
            loop.run_until_complete(battle_manager.start_battle(g.user_id))
        
        return jsonify({'status': 'Битва началась'}), 200
    except Exception as e:
        logger.error(f"Ошибка при запуске битвы: {e}", exc_info=True)
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500
    
@arena_bp.route('/get_arena_image_url/<int:arena_id>', methods=['GET'])
def get_arena_image_url(arena_id):
    try:
        arena = Arena.query.get(arena_id)
        if arena and arena.image_url:
            # Преобразование пути к изображению
            #image_url = arena.image_url.replace("\\", "/")
            image_url = arena.image_url if arena else None
            
            # Если путь уже включает 'static', избегаем его дублирования
            if image_url and image_url.startswith("static/"):
                image_url = image_url[len("static/"):]
            
            return jsonify({"image_url": image_url}), 200
        else:
            return jsonify({"error": "Arena image not found"}), 404
    except Exception as e:
        logger.error(f"Error fetching arena image URL: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@arena_bp.route('/get_latest_arena_image')
def get_latest_arena_image():
    arena = Arena.query.order_by(Arena.date_created.desc()).first()
    arena_image_url = arena.image_url if arena else None
    return jsonify({"arena_image_url": url_for('static', filename=arena_image_url)}) if arena_image_url else jsonify({"arena_image_url": None})
