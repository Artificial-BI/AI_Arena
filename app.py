from flask import Flask
from config import Config
from models import db
from flask_migrate import Migrate

# Импорт маршрутов и инициализации
from auth import auth_bp
from routes import main_bp
from initialization import init_db
from logging_config import configure_logging
from managers import battle_manager, arena_manager, tournament_manager

migrate = Migrate()
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = '4349459044808681'

# Инициализация базы данных
db.init_app(app)
migrate.init_app(app, db)
with app.app_context():
    init_db()

# Настройка логирования
configure_logging(app)

# Регистрация Blueprint'ов
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)

if __name__ == '__main__':
    app.run(debug=True)
