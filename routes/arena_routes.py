from flask import Blueprint, render_template, jsonify, request, g
from models import Character, ArenaChatMessage, GeneralChatMessage, TacticsChatMessage, User, Registrar, Arena
import logging
import json
from extensions import db
import uuid
from core import BattleManager
from gemini import GeminiAssistant  # Assuming GeminiAssistant is the assistant used for tactics and fighters

arena_bp = Blueprint('arena', __name__)
battle_manager = BattleManager()

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
    characters = Character.query.order_by(Character.id.desc()).limit(2).all()
    return render_template('arena.html', characters=characters, enumerate=enumerate)

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
    logging.info("Received request to start test battle")
    try:
        await battle_manager.start_test_battle()
        logging.info("Test battle started successfully")
        return jsonify({'status': 'Test battle started'}), 200
    except Exception as e:
        logging.error(f"Error starting test battle: {e}")
        return jsonify({"error": "Internal server error"}), 500
    
@arena_bp.route('/start_tactics', methods=['POST'])
async def start_tactics():
    logging.info("Received request to start tactics")
    try:
        user_id = g.user.id
        registrar = Registrar.query.filter_by(user_id=user_id).first()
        if not registrar:
            logging.error("User not registered for arena")
            return jsonify({"error": "User not registered for arena"}), 400

        character = Character.query.get(registrar.character_id)
        arena = Arena.query.get(registrar.arena_id)
        
        if not character or not arena:
            logging.error("Character or arena not found")
            return jsonify({"error": "Character or arena not found"}), 400

        # Получение непрочитанных сообщений
        unread_tactics_messages = TacticsChatMessage.query.filter_by(user_id=user_id, read_status=0).all()
        if not unread_tactics_messages:
            # Fetch character and arena details
            character = Character.query.get(registrar.character_id)
            arena = Arena.query.get(registrar.arena_id)

            # Construct the assistant prompt
            prompt = f"Arena Description: {arena.description}\n"
            prompt += f"Arena Parameters: {arena.parameters}\n\n"
            prompt += f"Character Name: {character.name}\n"
            prompt += f"Character Traits: {character.traits}\n\n"
            prompt += "Generate tactical advice for the next move."

            # Create assistant and get response
            assistant = GeminiAssistant("tactician")
            response = await assistant.send_message(prompt)

            # Save the tactics response to the tactics chat
            tactics_message = TacticsChatMessage(content=response, sender="tactician", user_id=user_id)
            db.session.add(tactics_message)
            db.session.commit()

            logging.info("Tactics generated successfully")
            return jsonify({"status": "Tactics generated", "response": response}), 200
        else:
            logging.info("Unread tactics messages present")
            return jsonify({"status": "Unread tactics messages present"}), 200
    except Exception as e:
        logging.error(f"Error generating tactics: {e}")
        return jsonify({"error": str(e)}), 500

