from flask import Flask, jsonify, request
from config import Config
from models import db
from flask_migrate import Migrate
from auth import auth_bp
from routes import main_bp
from initialization import init_db
from logging_config import configure_logging
from managers import battle_manager, arena_manager, tournament_manager  # Импорт менеджеров

# Инициализация Flask приложения и конфигурация
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = '4349459044808681'

# Инициализация базы данных и миграций
db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    init_db()

# Настройка логирования
configure_logging(app)

# Регистрация Blueprint'ов
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)

# Асинхронный маршрут для проведения боя
@app.route('/organize_battle', methods=['POST'])
async def organize_battle():
    data = await request.get_json()
    character1_id = data.get('character1_id')
    character2_id = data.get('character2_id')
    arena_id = data.get('arena_id')
    
    result = await battle_manager.organize_battle(character1_id, character2_id, arena_id)
    
    return jsonify({'status': 'success', 'result': result})

if __name__ == '__main__':
    app.run(debug=True)
