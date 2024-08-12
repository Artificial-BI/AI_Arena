import nest_asyncio
import asyncio
from flask import Blueprint, render_template, jsonify, request, g, url_for
from models import Character, ArenaChatMessage, GeneralChatMessage, TacticsChatMessage, Registrar, Arena
import logging
import json
from extensions import db
from core import BattleManager
from load_user import load_user
import os
from config import Config

# Применение nest_asyncio для поддержки запуска asyncio в текущем событии
nest_asyncio.apply()

config = Config()
# Путь к JSON-файлу
VISIT_TRACKING_FILE = config.VISIT_TRACKING_FILE
# Создание blueprint и battle manager
arena_bp = Blueprint('arena', __name__)
battle_manager = BattleManager()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@arena_bp.before_request
def before_request():
    """Обработка запросов перед их выполнением: проверка пользователя."""
    response = load_user()
    if response.status_code not in [200, 201]:
        return response
    
    user_data = response.get_json()
    g.user_id = user_data.get('user_id')
    g.cookie_id = user_data.get('cookie_id')

@arena_bp.route('/')
def arena():
    """Основной маршрут для отображения арены."""

    # Проверка существования JSON-файла
    if not os.path.exists(VISIT_TRACKING_FILE):
        with open(VISIT_TRACKING_FILE, 'w') as file:
            json.dump({"current_game": {}}, file)

    # Чтение данных из JSON-файла
    with open(VISIT_TRACKING_FILE, 'r') as file:
        visit_data = json.load(file)

    user_id_str = str(g.user_id)
    show_start_game_popup = False

    # Проверка состояния текущей игры для пользователя
    if visit_data["current_game"].get(user_id_str, True):
        show_start_game_popup = True
        visit_data["current_game"][user_id_str] = False
        with open(VISIT_TRACKING_FILE, 'w') as file:
            json.dump(visit_data, file)

    selected_character = Character.query.filter_by(user_id=g.user_id).order_by(Character.id.desc()).first()
    if not selected_character:
        return "Пожалуйста выберите персонажа или создайте с помощью ассистента"

    logger.info(f"Current user_id: {g.user_id}")

    arena = Arena.query.order_by(Arena.date_created.desc()).first()
    arena_image_url = arena.image_url if arena else None
    registrations = Registrar.query.all()

    characters = []
    for registration in registrations:
        character = Character.query.get(registration.character_id)
        if character:
            traits = json.loads(character.traits) if character.traits else {}
            traits['Combat'] = character.combat
            traits['Damage'] = character.damage
            traits['Life'] = character.life
            
            characters.append({
                'name': character.name,
                'traits': traits,
                'description': character.description,
                'image_url': character.image_url
            })

        return render_template(
            'arena.html', 
            characters=characters, 
            selected_character=selected_character, 
            arena_image_url=arena_image_url, 
            enumerate=enumerate,
            show_start_game_popup=show_start_game_popup
        )

def reset_game_state():
    """Сброс состояния игры для всех пользователей."""
    if os.path.exists(VISIT_TRACKING_FILE):
        with open(VISIT_TRACKING_FILE, 'r+') as file:
            visit_data = json.load(file)
            for user_id in visit_data["current_game"]:
                visit_data["current_game"][user_id] = True
            file.seek(0)
            json.dump(visit_data, file)
            file.truncate()

    return render_template(
        'arena.html', 
        characters=characters, 
        selected_character=selected_character, 
        arena_image_url=arena_image_url, 
        enumerate=enumerate,
        show_start_game_popup=show_start_game_popup
    )

@arena_bp.route('/get_registered_characters')
def get_registered_characters():
    """Получение списка зарегистрированных персонажей."""
    try:
        characters = [
            {
                "user_id": registration.user_id,
                "name": char.name,
                "traits": json.loads(char.traits),
                "image_url": char.image_url,
                "description": char.description
            }
            for registration in Registrar.query.all()
            if (char := Character.query.get(registration.character_id)) is not None
        ]
        return jsonify(characters)
    except Exception as e:
        logger.error(f"Error fetching registered characters: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@arena_bp.route('/get_arena_chat')
def get_arena_chat():
    """Получение сообщений чата арены."""
    return get_chat_messages(ArenaChatMessage, "arena chat")

@arena_bp.route('/get_general_chat')
def get_general_chat():
    """Получение сообщений общего чата."""
    return get_chat_messages(GeneralChatMessage, "general chat")

@arena_bp.route('/get_tactics_chat')
def get_tactics_chat():
    """Получение сообщений тактического чата."""
    return get_chat_messages(TacticsChatMessage, "tactics chat")

def get_chat_messages(message_model, chat_type):
    """Универсальная функция для получения сообщений чата."""
    try:
        messages = message_model.query.order_by(message_model.timestamp.asc()).all()
        chat_data = [{'content': msg.content, 'timestamp': msg.timestamp, 'sender': msg.sender, 'user_id': msg.user_id} for msg in messages]
        return jsonify(chat_data)
    except Exception as e:
        logger.error(f"Error fetching {chat_type} messages: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@arena_bp.route('/check_registered_players', methods=['GET'])
def check_registered_players():
    """Проверка количества зарегистрированных игроков и состояния битвы."""
    try:
        return jsonify({
            'battle_in_progress': battle_manager.battle_in_progress,
            'timer_in_progress': battle_manager.timer_in_progress,
            'remaining_time': battle_manager.get_remaining_time(),
            'registered_players': Registrar.query.count()
        }), 200
    except Exception as e:
        logger.error(f"Ошибка при проверке количества зарегистрированных игроков: {e}", exc_info=True)
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@arena_bp.route('/start_timer', methods=['POST'])
def start_timer():
    """Запуск таймера битвы."""
    if battle_manager.battle_in_progress or battle_manager.timer_in_progress:
        return jsonify({"error": "Битва уже идет или таймер уже запущен"}), 400
    
    battle_manager.start_timer(30)
    return jsonify({'status': 'Таймер запущен'}), 200

@arena_bp.route('/get_timer', methods=['GET'])
def get_timer():
    """Получение оставшегося времени таймера."""
    remaining_time = battle_manager.get_remaining_time()
    return jsonify({'remaining_time': remaining_time}), 200

@arena_bp.route('/start_battle', methods=['POST'])
def start_battle():
    """Запуск битвы."""
    logger.info("Запрос на старт битвы получен")
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(battle_manager.start_battle(g.user_id))
        else:
            loop.run_until_complete(battle_manager.start_battle(g.user_id))
        
        return jsonify({'status': 'Битва началась'}), 200
    except Exception as e:
        logger.error(f"Ошибка при запуске битвы: {e}", exc_info=True)
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@arena_bp.route('/get_arena_image_url/<int:arena_id>', methods=['GET'])
def get_arena_image_url(arena_id):
    """Получение URL изображения арены."""
    try:
        # Вызов всплывающего сообщения о начале генерации арены
       # show_notification("Генерация изображения арены...")

        arena = Arena.query.get(arena_id)
        if arena and arena.image_url:
            image_url = arena.image_url.replace("\\", "/")
            return jsonify({"image_url": image_url}), 200
        else:
            return jsonify({"error": "Arena image not found"}), 404
    except Exception as e:
        logger.error(f"Error fetching arena image URL: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@arena_bp.route('/get_latest_arena_image')
def get_latest_arena_image():
    """Получение изображения последней созданной арены."""
    arena = Arena.query.order_by(Arena.date_created.desc()).first()
    if arena and arena.image_url:
        image_url = arena.image_url.replace("\\", "/")
        return jsonify({"arena_image_url": url_for('static', filename=image_url)})
    return jsonify({"arena_image_url": None})
