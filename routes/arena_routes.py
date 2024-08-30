import asyncio
from flask import Blueprint, render_template, jsonify, request, g, url_for, redirect, current_app
from models import Character, ArenaChatMessage, GeneralChatMessage, TacticsChatMessage, Registrar, Arena, PreRegistrar
import logging
import json
from extensions import db
from load_user import load_user
from multiproc import StatusManager

# --- arena_routes.py ---

arena_bp = Blueprint('arena', __name__)
logger = logging.getLogger(__name__)

# Инициализация StatusManager
status_manager = StatusManager()

# Проверка регистрации пользователя перед каждым запросом
@arena_bp.before_request
def before_request():
    response = load_user()
    if response.status_code not in [200, 201]:
        return response
    user_data = response.get_json()
    g.user_id = user_data.get('user_id')
    g.cookie_id = user_data.get('cookie_id')

# Основной маршрут для отображения арены
@arena_bp.route('/')
async def arena():
    registered_character = Registrar.query.filter_by(user_id=g.user_id).first()
    if not registered_character:
        return redirect(url_for('viewer.viewer'))

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
                'user_id': registration.user_id,
                'name': character.name,
                'traits': traits,
                'description': character.description,
                'image_url': character.image_url
            })

    arena = Arena.query.order_by(Arena.date_created.desc()).first()
    arena_image_url = arena.image_url if arena else None

    return render_template(
        'arena.html',
        characters=characters,
        arena_image_url=arena_image_url,
        enumerate=enumerate,
        show_start_game_popup=False
    )

@arena_bp.route('/get_registered_characters')
async def get_registered_characters():
    logger.info(f"------------ get_registered_characters ---------")
    try:
        characters = []
        registrations = Registrar.query.all()
        for registration in registrations:
            char = Character.query.filter_by(id=registration.character_id).first()
            if char:
                logger.info(f"char.name: {char.name}")
                traits = json.loads(char.traits) if char.traits else {}
                traits.update({
                    "Combat": char.combat,
                    "Damage": char.damage,
                    "Life": char.life
                })
                characters.append({
                    "user_id": registration.user_id,
                    "name": char.name,
                    "traits": traits,
                    "image_url": char.image_url,
                    "description": char.description
                })
        logger.info(f"Fetched characters: {characters}")
        
        return jsonify(characters)
    except Exception as e:
        logger.error(f"Error fetching registered characters: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@arena_bp.route('/get_arena_chat')
async def get_arena_chat():
    return await get_chat_messages(ArenaChatMessage, "arena chat")

@arena_bp.route('/get_general_chat')
async def get_general_chat():
    return await get_chat_messages(GeneralChatMessage, "general chat")

@arena_bp.route('/get_tactics_chat')
async def get_tactics_chat():
    return await get_chat_messages(TacticsChatMessage, "tactics chat")

async def get_chat_messages(message_model, chat_type):
    """Универсальная функция для получения сообщений чата."""
    try:
        messages = message_model.query.order_by(message_model.timestamp.asc()).all()
        chat_data = [{'content': msg.content, 'timestamp': msg.timestamp, 'sender': msg.sender, 'user_id': msg.user_id} for msg in messages]
        return jsonify(chat_data)
    except Exception as e:
        logger.error(f"Error fetching {chat_type} messages: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@arena_bp.route('/get_arena_image_url/<int:arena_id>', methods=['GET'])
async def get_arena_image_url(arena_id):
    try: 
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
async def get_latest_arena_image():
    arena = Arena.query.order_by(Arena.date_created.desc()).first()
    if arena and arena.image_url:
        image_url = arena.image_url.replace("\\", "/")
        return jsonify({"arena_image_url": url_for('static', filename=image_url)})
    return jsonify({"arena_image_url": None})

# Использование StatusManager в маршрутах
@arena_bp.route('/get_status', methods=['GET'])
async def get_status():
    try:
        game_status = status_manager.get_state('game')
        arena_status = status_manager.get_state('arena')
        battle_status = status_manager.get_state('battle')
        timer_status = status_manager.get_state('timer')
        
        logger.info(f"States A: {game_status} G: {arena_status} B: {battle_status} T: {timer_status}")
        
        registered_players = Registrar.query.count()

        return jsonify({
            'registered_players': registered_players,
            'battle_status': battle_status,
            'timer_status': timer_status,
            'game_status': game_status,
            'arena_status': arena_status
        }), 200

    except Exception as e:
        logger.error(f"Error fetching statuses: {e}")
        return jsonify({"error": "Internal server error"}), 500


@arena_bp.route('/start_async_tasks', methods=['POST'])
async def start_async_tasks():
    # Ваш код для запуска задач
    return jsonify({'status': 'Tasks started'}), 200
