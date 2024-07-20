# --- app.py ---
from flask import Flask, render_template, redirect, url_for, request, flash
from config import Config
from models import db, migrate, User, Character, Message

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/player')
def player():
    return render_template('player.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/viewer')
def viewer():
    return render_template('viewer.html')

@app.route('/create_character', methods=['POST'])
def create_character():
    name = request.form['name']
    description = request.form['description']
    # Генерация изображения и начальных баллов
    image_url = generate_character_image(description)
    health_points = calculate_initial_health(description)
    new_character = Character(name=name, description=description, image_url=image_url, health_points=health_points)
    db.session.add(new_character)
    db.session.commit()
    flash('Character created successfully!', 'success')
    return redirect(url_for('player'))

@app.route('/send_message', methods=['POST'])
def send_message():
    content = request.form['message']
    # Здесь нужно добавить логику сохранения сообщения и отправки его другим пользователям
    flash('Message sent!', 'success')
    return redirect(url_for('player'))

@app.route('/update_settings', methods=['POST'])
def update_settings():
    temperature = request.form['temperature']
    top_p = request.form['top_p']
    top_k = request.form['top_k']
    # Здесь нужно добавить логику обновления настроек нейросетей
    flash('Settings updated!', 'success')
    return redirect(url_for('admin'))

@app.route('/set_game_mode', methods=['POST'])
def set_game_mode():
    game_mode = request.form['game_mode']
    # Логика для сохранения выбранного режима игры
    flash(f'Game mode set to {game_mode}!', 'success')
    return redirect(url_for('player'))

def generate_character_image(description):
    # Логика генерации изображения персонажа
    return "https://example.com/character_image.png"

def calculate_initial_health(description):
    # Логика расчета начальных баллов
    return 1000

if __name__ == '__main__':
    app.run(debug=True)
