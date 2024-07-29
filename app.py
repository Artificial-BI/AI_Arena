from flask import Flask, render_template
from config import Config
from logging_config import configure_logging
from initialization import init_extensions_and_db  # Импортируем объединенную функцию инициализации
from extensions import db
from load_user import initialize_user  # Импортируем наш новый декоратор

app = Flask(__name__)
app.config.from_object(Config)

# Инициализация расширений и базы данных
init_extensions_and_db(app)

# Импортируем и регистрируем блюпринты
from routes.index_routes import index_bp
from routes.common_routes import common_bp
from routes.player_routes import player_bp
from routes.viewer_routes import viewer_bp
from routes.admin_routes import admin_bp
from routes.arena_routes import arena_bp

app.register_blueprint(index_bp)
app.register_blueprint(common_bp, url_prefix='/common')
app.register_blueprint(player_bp, url_prefix='/player')
app.register_blueprint(viewer_bp, url_prefix='/viewer')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(arena_bp, url_prefix='/arena')

# Импортируем и регистрируем блюпринт для вебхуков
from webhook import webhook_bp
app.register_blueprint(webhook_bp)

# Конфигурируем логирование
configure_logging(app)

# Используем декоратор для всех маршрутов
@app.before_request
@initialize_user
def before_request():
    pass

# Определяем обработчики ошибок
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Основная точка входа
if __name__ == "__main__":
    app.run(debug=True, port=5000)
