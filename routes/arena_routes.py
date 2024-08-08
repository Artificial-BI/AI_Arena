import nest_asyncio
import asyncio
from flask import Blueprint, render_template, jsonify, request, g
from models import Character, ArenaChatMessage, GeneralChatMessage, TacticsChatMessage, User, Registrar, PreRegistrar, Arena
import logging
import json
from extensions import db
from core import BattleManager
from tactics_manager import TacticsManager
from load_user import load_user

nest_asyncio.apply()

arena_bp = Blueprint('arena', __name__)
battle_manager = BattleManager()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@arena_bp.before_request
def before_request():
    response = load_user()
    if response:
        return response

@arena_bp.route('/')
def arena():
    selected_character = Character.query.filter_by(user_id=g.user.id).order_by(Character.id.desc()).first()
    if not selected_character:
        return "Пожалуйста выберите персонажа или создайте с помощью ассистента"
    
    user_id = g.user.id
    logger.info(f"Current user_id: {user_id}")
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

    registrations = Registrar.query.all()
    characters = [Character.query.get(registration.character_id) for registration in registrations]
    
    return render_template('arena.html', characters=characters, selected_character=selected_character, enumerate=enumerate)


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
        battle_in_progress = battle_manager.is_battle_in_progress()
        timer_in_progress = battle_manager.is_timer_in_progress()
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
    logger.info("Запрос на старт таймера получен")
    try:
        if battle_manager.is_battle_in_progress() or battle_manager.is_timer_in_progress():
            return jsonify({"error": "Битва уже идет или таймер уже запущен"}), 400

        battle_manager.start_timer(30)
        return jsonify({'status': 'Таймер запущен'}), 200
    except Exception as e:
        logger.error(f"Ошибка при запуске таймера: {e}", exc_info=True)
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@arena_bp.route('/start_battle', methods=['POST'])
async def start_battle():
    logger.info("Запрос на старт битвы получен")
    try:
        await battle_manager.start_battle()
        return jsonify({'status': 'Битва началась'}), 200
    except Exception as e:
        logger.error(f"Ошибка при запуске битвы: {e}", exc_info=True)
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500
