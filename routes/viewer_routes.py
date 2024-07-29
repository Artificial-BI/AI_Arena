from flask import Blueprint, render_template, jsonify, request
from models import Character, ArenaChatMessage  # Учитываем, что models находится в корне проекта
import logging
import json
from extensions import db

viewer_bp = Blueprint('viewer', __name__)

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
            logging.info(f"Character: {character.name}, Traits: {character.traits}")
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
        logging.info(f"Characters data: {characters_data}")
        return jsonify(characters_data)
    except Exception as e:
        logging.error(f"Error fetching characters: {e}")
        return jsonify({"error": "Internal server error"}), 500

@viewer_bp.route('/get_arena_chat')
def get_arena_chat():
    try:
        messages = ArenaChatMessage.query.order_by(ArenaChatMessage.timestamp.asc()).all()
        chat_data = [{'content': msg.content, 'timestamp': msg.timestamp, 'sender': msg.sender} for msg in messages]
        return jsonify(chat_data)
    except Exception as e:
        logging.error(f"Error fetching arena chat messages: {e}")
        return jsonify({"error": "Internal server error"}), 500

@viewer_bp.route('/send_arena_chat', methods=['POST'])
def send_arena_chat():
    try:
        data = request.get_json()
        content = data.get('content')
        sender = data.get('sender')
        if not content or not sender:
            return jsonify({"error": "Invalid data"}), 400

        message = ArenaChatMessage(content=content, sender=sender)
        db.session.add(message)
        db.session.commit()
        return jsonify({"status": "Message sent"}), 200
    except Exception as e:
        logging.error(f"Error saving arena chat message: {e}")
        return jsonify({"error": "Internal server error"}), 500
