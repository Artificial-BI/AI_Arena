from flask import Blueprint, render_template, session, request, flash, jsonify, redirect, url_for, current_app
from models import db, Message, Character, RefereePrompt, CommentatorPrompt, TopPlayer, Tournament
from managers import battle_manager, arena_manager, tournament_manager
import json

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    current_app.logger.info('Index route accessed')
    top_players = TopPlayer.query.all()
    tournaments = Tournament.query.all()
    return render_template('index.html', top_players=top_players, tournaments=tournaments)

@main_bp.route('/player')
def player():
    current_app.logger.info('Player route accessed')
    try:
        user_id = session.get('user_id')
        messages = Message.query.order_by(Message.timestamp.asc()).all()
        characters = Character.query.filter((Character.user_id == user_id) | (Character.user_id == None)).all()
        selected_character_id = session.get('selected_character_id')
        selected_character = Character.query.get(selected_character_id) if selected_character_id else None

        return render_template('player.html', messages=messages, characters=characters, selected_character=selected_character, general_messages=messages)
    except Exception as e:
        current_app.logger.error(f'Error in player route: {str(e)}')
        return render_template('player.html', messages=[], characters=[], selected_character=None, general_messages=[])

@main_bp.route('/create_character', methods=['POST'])
async def create_character():
    current_app.logger.info('Create character route accessed')
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
        
        new_message = Message(user_id=user_id, content=json.dumps(character_data))
        db.session.add(new_message)
        db.session.commit()
        
        flash('Character created successfully!', 'success')
    except Exception as e:
        current_app.logger.error(f'Error creating character: {str(e)}')
        flash(f'Error creating character: {str(e)}', 'danger')
    return redirect(url_for('main.player'))

@main_bp.route('/select_character/<int:character_id>', methods=['POST'])
def select_character(character_id):
    current_app.logger.info(f'Select character route accessed for character_id: {character_id}')
    try:
        character = Character.query.get(character_id)
        if character:
            session['selected_character_id'] = character_id
            flash('Character selected successfully!', 'success')
        else:
            flash('Character not found!', 'danger')
    except Exception as e:
        current_app.logger.error(f'Error selecting character: {str(e)}')
        flash('Error selecting character!', 'danger')
    return redirect(url_for('main.player'))

@main_bp.route('/delete_character/<int:character_id>', methods=['POST'])
def delete_character(character_id):
    current_app.logger.info(f'Delete character route accessed for character_id: {character_id}')
    try:
        character = Character.query.get(character_id)
        if character:
            db.session.delete(character)
            db.session.commit()
            flash('Character deleted successfully!', 'success')
        else:
            flash('Character not found!', 'danger')
    except Exception as e:
        current_app.logger.error(f'Error deleting character: {str(e)}')
        flash('Error deleting character!', 'danger')
    return redirect(url_for('main.player'))

@main_bp.route('/get_characters', methods=['GET'])
def get_characters():
    current_app.logger.info('Get characters route accessed')
    try:
        characters = Character.query.all()
        characters_data = [{
            'id': character.id,
            'name': character.name,
            'description': character.description,
            'image_url': character.image_url,
            'traits': json.loads(character.traits)
        } for character in characters]
        
        current_app.logger.info(f'Characters fetched: {len(characters_data)}')
        return jsonify(characters_data)
    except Exception as e:
        current_app.logger.error(f'Error fetching characters: {str(e)}')
        return jsonify([]), 500

@main_bp.route('/get_battle_updates', methods=['GET'])
def get_battle_updates():
    current_app.logger.info('Get battle updates route accessed')
    try:
        updates = Message.query.order_by(Message.timestamp.desc()).limit(10).all()
        updates_data = [{
            'content': update.content,
            'timestamp': update.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        } for update in updates]
        
        current_app.logger.info(f'Battle updates fetched: {len(updates_data)}')
        return jsonify(updates_data)
    except Exception as e:
        current_app.logger.error(f'Error fetching battle updates: {str(e)}')
        return jsonify([]), 500

@main_bp.route('/get_battle_images', methods=['GET'])
def get_battle_images():
    current_app.logger.info('Get battle images route accessed')
    try:
        # Dummy data for images, replace with real image fetching logic
        images_data = [
            {'url': 'battle1.png'},
            {'url': 'battle2.png'},
            {'url': 'battle3.png'}
        ]
        
        current_app.logger.info(f'Battle images fetched: {len(images_data)}')
        return jsonify(images_data)
    except Exception as e:
        current_app.logger.error(f'Error fetching battle images: {str(e)}')
        return jsonify([]), 500

@main_bp.route('/get_messages', methods=['GET'])
def get_messages():
    current_app.logger.info('Get messages route accessed')
    try:
        messages = Message.query.order_by(Message.timestamp.desc()).all()
        messages_data = [{
            'content': message.content,
            'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': message.user_id
        } for message in messages]
        
        current_app.logger.info(f'Messages fetched: {len(messages_data)}')
        return jsonify(messages_data)
    except Exception as e:
        current_app.logger.error(f'Error fetching messages: {str(e)}')
        return jsonify([]), 500

@main_bp.route('/send_message', methods=['POST'])
def send_message():
    current_app.logger.info('Send message route accessed')
    try:
        user_id = session.get('user_id')
        content = request.form['message']
        new_message = Message(user_id=user_id, content=content)
        db.session.add(new_message)
        db.session.commit()
        
        current_app.logger.info('Message sent successfully')
        return jsonify({'status': 'success'})
    except Exception as e:
        current_app.logger.error(f'Error sending message: {str(e)}')
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get_characters')
def get_characters():
    try:
        characters = fetch_characters_from_db()  # Ваша функция для получения данных персонажей
        app.logger.info(f"Characters fetched: {characters}")
        return jsonify(characters)
    except Exception as e:
        app.logger.error(f"Error fetching characters: {e}")
        return jsonify({"error": str(e)}), 500
