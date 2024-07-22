from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
from config import Config
from models import db, migrate, User, Character, Message, RefereePrompt, CommentatorPrompt
import logging
from logging.handlers import RotatingFileHandler
import os
#---
from models import get_db_connection, create_tables
from core import BattleManager, ArenaManager, TournamentManager
#----

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db)

# Настройка логирования
if not app.debug:
    if not os.path.exists(Config.LOG_DIR):
        os.makedirs(Config.LOG_DIR)
    file_handler = RotatingFileHandler(Config.LOG_FILE, maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('AI Arena startup')

# @app.route('/')
# def index():
#     return render_template('index.html')
@app.route('/')
def index():
    top_players = [
        {"name": "JohnDoe", "wins": 10, "losses": 2},
        {"name": "JaneSmith", "wins": 8, "losses": 4},
        {"name": "RoboWarrior", "wins": 7, "losses": 5},
        {"name": "AIChamp", "wins": 6, "losses": 6},
    ]
    return render_template('index.html', top_players=top_players)

@app.route('/player')
def player():
    try:
        user_id = 1  # Здесь нужно определить ID текущего пользователя
        messages = Message.query.order_by(Message.timestamp.asc()).all()
        characters = Character.query.filter_by(user_id=user_id).all()
        selected_character_id = session.get('selected_character_id')
        selected_character = Character.query.get(selected_character_id) if selected_character_id else None
        return render_template('player.html', messages=messages, characters=characters, selected_character=selected_character)
    except Exception as e:
        return render_template('player.html', messages=[], characters=[], selected_character=None)

@app.route('/update_settings', methods=['POST'])
def update_settings():
    try:
        temperature = request.form['temperature']
        top_p = request.form['top_p']
        top_k = request.form['top_k']
        # Здесь вы можете сохранить эти значения в базу данных или использовать их для конфигурации
        flash('Settings updated successfully!', 'success')
    except Exception as e:
        flash('Error updating settings!', 'danger')
    return redirect(url_for('admin'))


@app.route('/admin')
def admin():
    try:
        messages = Message.query.order_by(Message.timestamp.asc()).all()
        referee_prompts = RefereePrompt.query.all()
        return render_template('admin.html', messages=messages, referee_prompts=referee_prompts)
    except Exception as e:
        return render_template('admin.html', messages=[], referee_prompts=[])

@app.route('/viewer')
def viewer():
    try:
        characters = Character.query.limit(2).all()
        messages = Message.query.order_by(Message.timestamp.asc()).all()
        return render_template('viewer.html', characters=characters, messages=messages)
    except Exception as e:
        app.logger.error('Error loading viewer: %s', e)
        return render_template('viewer.html', characters=[], messages=[])
    


@app.route('/create_character', methods=['POST'])
def create_character():
    try:
        name = request.form['name']
        description = request.form['description']
        user_id = 1  # Замените 1 на идентификатор текущего пользователя
        image_url = generate_character_image(description, user_id, name)
        health_points = calculate_initial_health(description)
        new_character = Character(name=name, description=description, image_url=image_url, health_points=health_points, user_id=user_id)
        db.session.add(new_character)
        db.session.commit()
        flash('Character created successfully!', 'success')
    except Exception as e:
        flash('Error creating character!', 'danger')
    return redirect(url_for('player'))

@app.route('/delete_character/<int:character_id>', methods=['POST'])
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
    return redirect(url_for('player'))

@app.route('/select_character/<int:character_id>', methods=['POST'])
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
    return redirect(url_for('player'))

@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        content = request.form['message']
        user_id = 1  # Здесь нужно определить ID текущего пользователя
        new_message = Message(user_id=user_id, content=content)
        db.session.add(new_message)
        db.session.commit()
        flash('Message sent!', 'success')
    except Exception as e:
        flash('Error sending message!', 'danger')
    return redirect(url_for('player'))

@app.route('/add_referee_prompt', methods=['POST'])
def add_referee_prompt():
    try:
        prompt_text = request.form['referee_prompt']
        new_prompt = RefereePrompt(prompt_text=prompt_text)
        db.session.add(new_prompt)
        db.session.commit()
        flash('Referee prompt added successfully!', 'success')
    except Exception as e:
        flash('Error adding referee prompt!', 'danger')
    return redirect(url_for('admin'))

@app.route('/select_referee_prompt', methods=['POST'])
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
    return redirect(url_for('admin'))

@app.route('/add_commentator_prompt', methods=['POST'])
def add_commentator_prompt():
    try:
        prompt_text = request.form['commentator_prompt']
        new_prompt = CommentatorPrompt(prompt_text=prompt_text)
        db.session.add(new_prompt)
        db.session.commit()
        flash('Commentator prompt added successfully!', 'success')
    except Exception as e:
        app.logger.error('Error adding commentator prompt: %s', e)
        flash('Error adding commentator prompt!', 'danger')
    return redirect(url_for('admin'))

@app.route('/select_commentator_prompt', methods=['POST'])
def select_commentator_prompt():
    prompt_id = request.form['existing_commentator_prompts']
    selected_prompt = CommentatorPrompt.query.get(prompt_id)
    if selected_prompt:
        flash(f'Selected commentator prompt: {selected_prompt.prompt_text}', 'success')
    else:
        flash('Error selecting commentator prompt!', 'danger')
    return redirect(url_for('admin'))
#---

create_tables()

battle_manager = BattleManager()
arena_manager = ArenaManager()
tournament_manager = TournamentManager()

@app.route('/organize_battle', methods=['POST'])
def organize_battle():
    data = request.json
    character1_id = data.get('character1_id')
    character2_id = data.get('character2_id')
    arena_id = data.get('arena_id')
    battle_manager.organize_battle(character1_id, character2_id, arena_id)
    return jsonify({'status': 'success'})

@app.route('/create_arena', methods=['POST'])
def create_arena():
    data = request.json
    description = data.get('description')
    parameters = data.get('parameters')
    arena_manager.create_arena(description, parameters)
    return jsonify({'status': 'success'})

@app.route('/create_tournament', methods=['POST'])
def create_tournament():
    data = request.json
    name = data.get('name')
    format = data.get('format')
    tournament_manager.create_tournament(name, format)
    return jsonify({'status': 'success'})
#---


def generate_character_image(description, user_id, character_name):
    image_filename = 'character_image.png'
    user_folder = os.path.join(app.root_path, 'static/images', f'user_{user_id}')
    character_folder = os.path.join(user_folder, character_name)

    if not os.path.exists(character_folder):
        os.makedirs(character_folder)

    image_path = os.path.join(character_folder, image_filename)
    with open(image_path, 'wb') as f:
        f.write(b'')
    return os.path.relpath(image_path, app.root_path + '/static')

def calculate_initial_health(description):
    return 1000


def generate_character_image(description, user_id, character_name):
    # Логика генерации изображения персонажа
    app.logger.info('Generating character image for description: %s', description)
    image_filename = 'character_image.png'  # Название файла изображения
    user_folder = os.path.join(app.root_path, 'static/images', f'user_{user_id}')
    character_folder = os.path.join(user_folder, character_name)

    if not os.path.exists(character_folder):
        os.makedirs(character_folder)

    image_path = os.path.join(character_folder, image_filename)

    # Здесь будет логика сохранения изображения на диск
    with open(image_path, 'wb') as f:
        f.write(b'')  # Сюда нужно поместить реальные данные изображения

    return os.path.relpath(image_path, app.root_path + '/static')

def calculate_initial_health(description):
    # Логика расчета начальных баллов
    app.logger.info('Calculating initial health for description: %s', description)
    return 1000

if __name__ == '__main__':
    app.run(debug=True)


#==========