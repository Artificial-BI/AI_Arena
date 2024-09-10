from flask import Blueprint, render_template, jsonify, request, g
from models import Character, User
#from chats_models import ReadStatus, ArenaChatMessage, TacticsChatMessage, GeneralChatMessage
import logging
import json
from extensions import db
from load_user import load_user

# --- viewer_routes.py ---
viewer_bp = Blueprint('viewer', __name__)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@viewer_bp.before_request
def before_request():
    response = load_user()
    if response.status_code != 200 and response.status_code != 201:
        return response
    
    # Извлекаем данные пользователя из ответа
    user_data = response.get_json()
    g.user_id = user_data.get('user_id')
    g.cookie_id = user_data.get('cookie_id')

@viewer_bp.route('/')
def viewer():
    characters = Character.query.order_by(Character.id.desc()).limit(2).all()
    return render_template('viewer.html', characters=characters)

@viewer_bp.route('/get_characters')
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
        logger.error(f"Error fetching characters: {e}")
        return jsonify({"error": "Internal server error"}), 500

@viewer_bp.route('/get_arena_chat')
def get_arena_chat():
    try:
        messages = "" #ArenaChatMessage.query.order_by(ArenaChatMessage.timestamp.asc()).all()
        chat_data = [{'content': msg.content, 'timestamp': msg.timestamp, 'sender': msg.sender, 'user_id': msg.user_id} for msg in messages]
        return jsonify(chat_data)
    except Exception as e:
        logger.error(f"Error fetching arena chat messages: {e}")
        return jsonify({"error": "Internal server error"}), 500

@viewer_bp.route('/get_general_chat')
def get_general_chat():
    try:
        messages = "" #GeneralChatMessage.query.order_by(GeneralChatMessage.timestamp.asc()).all()
        chat_data = [{'content': msg.content, 'timestamp': msg.timestamp, 'sender': msg.sender, 'user_id': msg.user_id} for msg in messages]
        return jsonify(chat_data)
    except Exception as e:
        logger.error(f"Error fetching general chat messages: {e}")
        return jsonify({"error": "Internal server error"}), 500

@viewer_bp.route('/send_arena_chat', methods=['POST'])
def send_arena_chat():
    try:
        data = request.get_json()
        content = data.get('content')
        sender = data.get('sender')
        user_id = g.user_id  # Используем текущий user_id

        if not content or not sender or not user_id:
            return jsonify({"error": "Invalid data"}), 400

        message = ""#ArenaChatMessage(content=content, sender=sender, user_id=user_id)
        db.session.add(message)
        db.session.commit()
        return jsonify({"status": "Message sent"}), 200
    except Exception as e:
        logger.error(f"Error saving arena chat message: {e}")
        return jsonify({"error": "Internal server error"}), 500

@viewer_bp.route('/send_general_chat', methods=['POST'])
def send_general_chat():
    try:
        data = request.get_json()
        content = data.get('content')
        sender = data.get('sender')
        user_id = g.user_id  # Используем текущий user_id

        if not content or not sender or not user_id:
            return jsonify({"error": "Invalid data"}), 400

        message = "" #GeneralChatMessage(content=content, sender=sender, user_id=user_id)
        db.session.add(message)
        db.session.commit()
        return jsonify({"status": "Message sent"}), 200
    except Exception as e:
        logger.error(f"Error saving general chat message: {e}")
        return jsonify({"error": "Internal server error"}), 500
