from flask import Blueprint, render_template, session, request, flash, jsonify, redirect, url_for, current_app
from models import db, Message, Character, RefereePrompt, CommentatorPrompt, TopPlayer, Tournament
from managers import battle_manager, arena_manager, tournament_manager
import os
import json
from character_manager import CharacterManager

main_bp = Blueprint('main', __name__)

def init_character_manager():
    global character_manager
    with current_app.app_context():
        character_manager = CharacterManager()

@main_bp.before_app_request
def before_request():
    if 'character_manager' not in globals():
        init_character_manager()

@main_bp.route('/')
def index():
    top_players = TopPlayer.query.all()
    tournaments = Tournament.query.all()
    return render_template('index.html', top_players=top_players, tournaments=tournaments)

@main_bp.route('/player')
def player():
    try:
        user_id = session.get('user_id')
        messages = Message.query.order_by(Message.timestamp.asc()).all()
        characters = Character.query.filter_by(user_id=user_id).all()
        selected_character_id = session.get('selected_character_id')
        selected_character = Character.query.get(selected_character_id) if selected_character_id else None
        return render_template('player.html', messages=messages, characters=characters, selected_character=selected_character, general_messages=messages)
    except Exception as e:
        return render_template('player.html', messages=[], characters=[], selected_character=None, general_messages=[])

@main_bp.route('/create_character', methods=['POST'])
async def create_character():
    try:
        description = request.form['description']
        user_id = session.get('user_id')
        character_data = await character_manager.generate_character(description)
        
        new_character = Character(
            user_id=user_id,
            name=character_data['name'],
            description=description,
            image_url=character_data['image_url'],
            traits=json.dumps(character_data['traits'])
        )
        db.session.add(new_character)
        db.session.commit()
        
        # Отправка ответа в чат
        new_message = Message(user_id=user_id, content=json.dumps(character_data))
        db.session.add(new_message)
        db.session.commit()
        
        flash('Character created successfully!', 'success')
    except Exception as e:
        flash(f'Error creating character: {str(e)}', 'danger')
    return redirect(url_for('main.player'))

@main_bp.route('/select_character/<int:character_id>', methods=['POST'])
def select_character(character_id):
    try:
        character = Character.query.get(character_id)
        if character:
            session['selected_character_id'] = character_id
            flash('Character selected successfully!', 'success')
        else:
            flash('Character not found!', 'danger')
    except Exception as e:
        flash('Error selecting character!', 'danger')
    return redirect(url_for('main.player'))

@main_bp.route('/delete_character/<int:character_id>', methods=['POST'])
def delete_character(character_id):
    try:
        character = Character.query.get(character_id)
        if character:
            db.session.delete(character)
            db.session.commit()
            flash('Character deleted successfully!', 'success')
        else:
            flash('Character not found!', 'danger')
    except Exception as e:
        flash('Error deleting character!', 'danger')
    return redirect(url_for('main.player'))

@main_bp.route('/send_message', methods=['POST'])
async def send_message():
    try:
        content = request.form['message']
        user_id = session.get('user_id')
        
        # Генерация ответа нейросетью
        response = await character_manager.chat_with_assistant(content)
        
        new_message = Message(user_id=user_id, content=content)
        db.session.add(new_message)
        db.session.commit()
        
        response_message = Message(user_id=user_id, content=response)
        db.session.add(response_message)
        db.session.commit()
        
        flash('Message sent!', 'success')
    except Exception as e:
        flash(f'Error sending message: {str(e)}', 'danger')
    return redirect(url_for('main.player'))

@main_bp.route('/send_general_message', methods=['POST'])
def send_general_message():
    try:
        content = request.form['general-message']
        user_id = session.get('user_id')
        new_message = Message(user_id=user_id, content=content)
        db.session.add(new_message)
        db.session.commit()
        flash('General message sent!', 'success')
    except Exception as e:
        flash('Error sending general message!', 'danger')
    return redirect(url_for('main.player'))

@main_bp.route('/update_settings', methods=['POST'])
def update_settings():
    try:
        temperature = request.form['temperature']
        top_p = request.form['top_p']
        top_k = request.form['top_k']
        # Здесь вы можете сохранить эти значения в базу данных или использовать их для конфигурации
        flash('Settings updated successfully!', 'success')
    except Exception as e:
        flash('Error updating settings!', 'danger')
    return redirect(url_for('main.admin'))

@main_bp.route('/admin')
def admin():
    try:
        messages = Message.query.order_by(Message.timestamp.asc()).all()
        referee_prompts = RefereePrompt.query.all()
        return render_template('admin.html', messages=messages, referee_prompts=referee_prompts)
    except Exception as e:
        return render_template('admin.html', messages=[], referee_prompts=[])

@main_bp.route('/viewer')
def viewer():
    try:
        characters = Character.query.limit(2).all()
        messages = Message.query.order_by(Message.timestamp.asc()).all()
        return render_template('viewer.html', characters=characters, messages=messages)
    except Exception as e:
        return render_template('viewer.html', characters=[], messages=[])
