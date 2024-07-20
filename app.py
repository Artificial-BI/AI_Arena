# --- app.py ---
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from config import Config
from models import db, migrate, User, Character, Message
import logging
from logging.handlers import RotatingFileHandler
import os

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/player')
def player():
    try:
        messages = Message.query.order_by(Message.timestamp.asc()).all()
        character = Character.query.filter_by(user_id=1).first()  # Замените 1 на идентификатор текущего пользователя
        app.logger.info('Loaded player page with character: %s', character.name if character else 'No character found')
        return render_template('player.html', messages=messages, character=character)
    except Exception as e:
        app.logger.error('Error loading player page: %s', e)
        return render_template('player.html', messages=[], character=None)

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/viewer')
def viewer():
    return render_template('viewer.html')

@app.route('/create_character', methods=['POST'])
def create_character():
    try:
        name = request.form['name']
        description = request.form['description']
        user_id = 1  # Замените 1 на идентификатор текущего пользователя
        # Генерация изображения и начальных баллов
        image_url = generate_character_image(description, user_id, name)
        health_points = calculate_initial_health(description)
        new_character = Character(name=name, description=description, image_url=image_url, health_points=health_points, user_id=user_id)
        db.session.add(new_character)
        db.session.commit()
        app.logger.info('Created new character: %s with image URL: %s', name, image_url)
        flash('Character created successfully!', 'success')
    except Exception as e:
        app.logger.error('Error creating character: %s', e)
        flash('Error creating character!', 'danger')
    return redirect(url_for('player'))

@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        content = request.form['message']
        user_id = 1  # Здесь нужно определить ID текущего пользователя
        new_message = Message(user_id=user_id, content=content)
        db.session.add(new_message)
        db.session.commit()
        app.logger.info('Message sent by user %d: %s', user_id, content)
        flash('Message sent!', 'success')
    except Exception as e:
        app.logger.error('Error sending message: %s', e)
        flash('Error sending message!', 'danger')
    return redirect(url_for('player'))

@app.route('/get_messages', methods=['GET'])
def get_messages():
    try:
        messages = Message.query.order_by(Message.timestamp.asc()).all()
        app.logger.info('Fetched messages: %d messages', len(messages))
        return jsonify([{
            'user_id': message.user_id,
            'content': message.content,
            'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        } for message in messages])
    except Exception as e:
        app.logger.error('Error fetching messages: %s', e)
        return jsonify([])

def generate_character_image(description, user_id, character_name):
    # Логика генерации изображения персонажа
    app.logger.info('Generating character image for description: %s', description)
    image_filename = 'character_image.png'  # Название файла изображения
    user_folder = os.path.join(Config.IMAGE_UPLOADS, f'user_{user_id}')
    character_folder = os.path.join(user_folder, character_name)

    if not os.path.exists(character_folder):
        os.makedirs(character_folder)

    image_path = os.path.join(character_folder, image_filename)

    # Здесь будет логика сохранения изображения на диск
    with open(image_path, 'wb') as f:
        f.write(b'')  # Сюда нужно поместить реальные данные изображения

    return image_path

def calculate_initial_health(description):
    # Логика расчета начальных баллов
    app.logger.info('Calculating initial health for description: %s', description)
    return 1000

if __name__ == '__main__':
    app.run(debug=True)
