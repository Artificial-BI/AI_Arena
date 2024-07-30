from flask import Blueprint, render_template, jsonify, request, g
from models import Character, ArenaChatMessage, GeneralChatMessage, TacticsChatMessage
import logging
import json
from extensions import db

arena_bp = Blueprint('arena', __name__)

@arena_bp.route('/')
def arena():
    characters = Character.query.order_by(Character.id.desc()).limit(2).all()
    return render_template('arena.html', characters=characters)

@arena_bp.route('/get_characters')
def get_characters():
    try:
        characters = Character.query.order_by(Character.id.desc()).limit(2).all()
        characters_data = []
        for character in characters:
            #logging.info(f"Character: {character.name}, Traits: {character.traits}")
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
       # logging.info(f"Characters data: {characters_data}")
        return jsonify(characters_data)
    except Exception as e:
        logging.error(f"Error fetching characters: {e}")
        return jsonify({"error": "Internal server error"}), 500

@arena_bp.route('/get_arena_chat')
def get_arena_chat():
    try:
        messages = ArenaChatMessage.query.order_by(ArenaChatMessage.timestamp.asc()).all()
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
        messages = GeneralChatMessage.query.order_by(GeneralChatMessage.timestamp.asc()).all()
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
        messages = TacticsChatMessage.query.order_by(TacticsChatMessage.timestamp.asc()).all()
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
