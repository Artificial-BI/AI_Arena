import json
import re
import asyncio
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, current_app, g
from sqlalchemy import desc
from extensions import db
from models import Message, Character
from datetime import datetime
from gemini import GeminiAssistant
import logging
from utils import parse_character, save_to_json

player_bp = Blueprint('player_bp', __name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Вспомогательные функции
def fetch_messages():
    try:
        return Message.query.all()
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        return []

def fetch_characters():
    try:
        return Character.query.all()
    except Exception as e:
        logger.error(f"Error fetching characters: {e}")
        return []

def get_selected_character():
    try:
        return Character.query.order_by(desc(Character.id)).first()
    except Exception as e:
        logger.error(f"Error fetching selected character: {e}")
        return None

def get_last_character_id():
    try:
        last_character = Character.query.order_by(desc(Character.id)).first()
        return last_character.id if last_character else None
    except Exception as e:
        logger.error(f"Error fetching last character: {e}")
        return None

# Маршруты
@player_bp.route('/')
def player():
    logger.info("Fetching player data")
    messages = fetch_messages()
    characters = fetch_characters()
    selected_character = get_selected_character()
    last_character_id = get_last_character_id()

    return render_template('player.html', messages=messages, characters=characters, selected_character=selected_character, last_character_id=last_character_id)

@player_bp.route('/arena')
def arena():
    return render_template('arena.html')

@player_bp.route('/select_character/<int:character_id>', methods=['POST'])
def select_character(character_id):
    character = Character.query.get(character_id)
    if character:
        selected_character = {
            "name": character.name,
            "description": character.description,
            "traits": json.loads(character.traits)
        }
        logger.info(f"Selected character: {selected_character}")
        return jsonify(selected_character)
    logger.error(f"Character not found: {character_id}")
    return jsonify({"error": "Character not found"}), 404

@player_bp.route('/send_message', methods=['POST'])
def send_message():
    try:
        content = request.form.get('message', '').strip()

        if not content:
            raise ValueError("Invalid input: 'content' argument must not be empty. Please provide a non-empty value.")

        user_id = g.user.id  # Используем идентификатор текущего пользователя

        # Создаем ассистента при каждом вызове
        assistant = GeminiAssistant("character_generator")
        # Используем asyncio.run для выполнения асинхронной функции
        logger.info(f"Sending message to assistant: {content}")
        response = asyncio.run(assistant.send_message(content))
        logger.info(f"Received response from assistant: {response}")

        # Сохраняем сообщение и ответ в базе данных
        message = Message(content=content, user_id=user_id)
        response_message = Message(content=response, user_id=0)
        db.session.add(message)
        db.session.add(response_message)
        db.session.commit()

        # Парсим ответ и возвращаем данные персонажа, если они есть
        parsed_character = parse_character(response)
        if parsed_character["name"]:
            save_to_json(parsed_character)
            return jsonify({"status": "Message sent", "response": response, "character": parsed_character})
        
        return jsonify({"status": "Message sent", "response": response})
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return jsonify({"error": str(e)}), 500
    
@player_bp.route('/delete_character/<int:character_id>', methods=['POST'])
def delete_character(character_id):
    try:
        character = Character.query.get(character_id)
        db.session.delete(character)
        db.session.commit()
        logger.info(f"Deleted character: {character_id}")
        return redirect(url_for('player_bp.player'))
    except Exception as e:
        logger.error(f"Error deleting character: {e}")
        return jsonify({"error": str(e)}), 500

@player_bp.route('/create_character', methods=['POST'])
def create_character():
    try:
        name = request.form['name']
        description = request.form['description']
        traits_string = request.form['extraInput']
        
        # Преобразуем строку характеристик в словарь
        traits = {}
        for item in traits_string.split(', '):
            key, value = item.split(':')
            try:
                traits[key] = int(value)
            except ValueError:
                traits[key] = 0  # или любое другое значение по умолчанию для невалидных данных
        
        # Преобразуем словарь в JSON строку с кодировкой Unicode
        traits_json = json.dumps(traits, ensure_ascii=False)
        
        new_character = Character(name=name, description=description, image_url='images/default/character.png', traits=traits_json)
        db.session.add(new_character)
        db.session.commit()
        logger.info(f"Created new character: {name}")
        return redirect(url_for('player_bp.player'))
    except Exception as e:
        logger.error(f"Error creating character: {e}")
        return jsonify({"error": str(e)}), 500

@player_bp.route('/send_general_message', methods=['POST'])
def send_general_message():
    try:
        content = request.form.get('message', '').strip()
        if not content:
            raise ValueError("Invalid input: 'content' argument must not be empty. Please provide a non-empty value.")
            
        user_id = g.user.id  # Используем идентификатор текущего пользователя
        message = Message(content=content, user_id=user_id)
        db.session.add(message)
        db.session.commit()
        logger.info(f"Sent general message: {content}")
        return jsonify({"status": "General message sent"})
    except Exception as e:
        logger.error(f"Error sending general message: {e}")
        return jsonify({"error": str(e)}), 500
