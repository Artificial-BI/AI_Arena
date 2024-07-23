from flask import Blueprint, render_template, session, request, flash, jsonify, redirect, url_for
from models import db, Message, Character, RefereePrompt, CommentatorPrompt
from managers import battle_manager, arena_manager, tournament_manager
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    top_players = [
        {"name": "JohnDoe", "wins": 10, "losses": 2, "character_name": "Warrior John", "weekly_wins": 5, "weekly_losses": 1},
        {"name": "JaneSmith", "wins": 8, "losses": 4, "character_name": "Mage Jane", "weekly_wins": 4, "weekly_losses": 2},
        {"name": "RoboWarrior", "wins": 7, "losses": 5, "character_name": "Robot Robo", "weekly_wins": 3, "weekly_losses": 3},
        {"name": "AIChamp", "wins": 6, "losses": 6, "character_name": "Champion AI", "weekly_wins": 2, "weekly_losses": 4},
        {"name": "Player5", "wins": 5, "losses": 5, "character_name": "Character 5", "weekly_wins": 1, "weekly_losses": 5},
        {"name": "Player6", "wins": 4, "losses": 6, "character_name": "Character 6", "weekly_wins": 0, "weekly_losses": 6},
        {"name": "Player7", "wins": 3, "losses": 7, "character_name": "Character 7", "weekly_wins": 6, "weekly_losses": 0},
        {"name": "Player8", "wins": 2, "losses": 8, "character_name": "Character 8", "weekly_wins": 5, "weekly_losses": 1},
        {"name": "Player9", "wins": 1, "losses": 9, "character_name": "Character 9", "weekly_wins": 4, "weekly_losses": 2},
        {"name": "Player10", "wins": 0, "losses": 10, "character_name": "Character 10", "weekly_wins": 3, "weekly_losses": 3},
    ]
    tournaments = [
        {"id": 1, "name": "Summer Cup", "format": "круговой", "start_date": "2024-06-01", "end_date": "2024-06-30", "current_stage": "финал"},
        {"id": 2, "name": "Winter Cup", "format": "плей-офф", "start_date": "2024-12-01", "end_date": "2024-12-31", "current_stage": "полуфинал"},
    ]
    return render_template('index.html', top_players=top_players, tournaments=tournaments)

@main_bp.route('/player')
def player():
    try:
        user_id = session.get('user_id')
        messages = Message.query.order_by(Message.timestamp.asc()).all()
        characters = Character.query.filter_by(user_id=user_id).all()
        selected_character_id = session.get('selected_character_id')
        selected_character = Character.query.get(selected_character_id) if selected_character_id else None
        return render_template('player.html', messages=messages, characters=characters, selected_character=selected_character)
    except Exception as e:
        return render_template('player.html', messages=[], characters=[], selected_character=None)

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
        
@main_bp.route('/create_character', methods=['POST'])
def create_character():
    try:
        name = request.form['name']
        description = request.form['description']
        user_id = session.get('user_id')
        image_url = generate_character_image(description, user_id, name)
        health_points = calculate_initial_health(description)
        new_character = Character(name=name, description=description, image_url=image_url, health_points=health_points, user_id=user_id)
        db.session.add(new_character)
        db.session.commit()
        flash('Character created successfully!', 'success')
    except Exception as e:
        flash('Error creating character!', 'danger')
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

@main_bp.route('/send_message', methods=['POST'])
def send_message():
    try:
        content = request.form['message']
        user_id = session.get('user_id')
        new_message = Message(user_id=user_id, content=content)
        db.session.add(new_message)
        db.session.commit()
        flash('Message sent!', 'success')
    except Exception as e:
        flash('Error sending message!', 'danger')
    return redirect(url_for('main.player'))

@main_bp.route('/add_referee_prompt', methods=['POST'])
def add_referee_prompt():
    try:
        prompt_text = request.form['referee_prompt']
        new_prompt = RefereePrompt(prompt_text=prompt_text)
        db.session.add(new_prompt)
        db.session.commit()
        flash('Referee prompt added successfully!', 'success')
    except Exception as e:
        flash('Error adding referee prompt!', 'danger')
    return redirect(url_for('main.admin'))

@main_bp.route('/select_referee_prompt', methods=['POST'])
def select_referee_prompt():
    try:
        prompt_id = request.form['existing_prompts']
        selected_prompt = RefereePrompt.query.get(prompt_id)
        if selected_prompt:
            session['selected_referee_prompt'] = selected_prompt.prompt_text
            flash('Referee prompt selected successfully!', 'success')
        else:
            flash('Referee prompt not found!', 'danger')
    except Exception as e:
        flash('Error selecting referee prompt!', 'danger')
    return redirect(url_for('main.admin'))

@main_bp.route('/add_commentator_prompt', methods=['POST'])
def add_commentator_prompt():
    try:
        prompt_text = request.form['commentator_prompt']
        new_prompt = CommentatorPrompt(prompt_text=prompt_text)
        db.session.add(new_prompt)
        db.session.commit()
        flash('Commentator prompt added successfully!', 'success')
    except Exception as e:
        flash('Error adding commentator prompt!', 'danger')
    return redirect(url_for('main.admin'))

@main_bp.route('/select_commentator_prompt', methods=['POST'])
def select_commentator_prompt():
    prompt_id = request.form['existing_commentator_prompts']
    selected_prompt = CommentatorPrompt.query.get(prompt_id)
    if selected_prompt:
        flash(f'Selected commentator prompt: {selected_prompt.prompt_text}', 'success')
    else:
        flash('Error selecting commentator prompt!', 'danger')
    return redirect(url_for('main.admin'))

@main_bp.route('/organize_battle', methods=['POST'])
def organize_battle():
    data = request.json
    character1_id = data.get('character1_id')
    character2_id = data.get('character2_id')
    arena_id = data.get('arena_id')
    battle_manager.organize_battle(character1_id, character2_id, arena_id)
    return jsonify({'status': 'success'})

@main_bp.route('/create_arena', methods=['POST'])
def create_arena():
    data = request.json
    description = data.get('description')
    parameters = data.get('parameters')
    arena_manager.create_arena(description, parameters)
    return jsonify({'status': 'success'})

@main_bp.route('/create_tournament', methods=['POST'])
def create_tournament():
    data = request.json
    name = data.get('name')
    format = data.get('format')
    tournament_manager.create_tournament(name, format)
    return jsonify({'status': 'success'})

# Функции для генерации изображений и расчета здоровья персонажей
def generate_character_image(description, user_id, character_name):
    image_filename = 'character_image.png'  # Название файла изображения
    user_folder = os.path.join('static/images', f'user_{user_id}')
    character_folder = os.path.join(user_folder, character_name)

    if not os.path.exists(character_folder):
        os.makedirs(character_folder)

    image_path = os.path.join(character_folder, image_filename)

    # Здесь будет логика сохранения изображения на диск
    with open(image_path, 'wb') as f:
        f.write(b'')  # Сюда нужно поместить реальные данные изображения

    return os.path.relpath(image_path, 'static')

def calculate_initial_health(description):
    return 1000
