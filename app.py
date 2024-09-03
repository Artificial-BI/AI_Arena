from flask import Flask, render_template, request, g
from config import Config
from logging_config import configure_logging
from initialization import init_extensions_and_db
from extensions import db
from models import PreRegistrar, Registrar, Player
import traceback
import asyncio
from core import BattleManager
from multiproc import StatusManager
from message_buffer import MessageManager, ZMQServer
from threading import Thread

# --- app.py ---

app = Flask(__name__)
app.config.from_object(Config)

if not app.debug:
    configure_logging(app)

init_extensions_and_db(app)

def clear_table():
    with app.app_context():
        try:
            db.session.query(PreRegistrar).delete()
            db.session.query(Registrar).delete()
            db.session.commit()
            app.logger.info("Очистка таблиц Registrar и PreRegistrar и статуса Player.")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Ошибка при очистке таблиц Registrar и PreRegistrar. Error: {e}")

# Подключение маршрутов
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

from webhook import webhook_bp
app.register_blueprint(webhook_bp)

app.jinja_env.globals.update(enumerate=enumerate)

clear_table()

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    error_trace = traceback.format_exc()
    app.logger.error(f'Server Error: {error}, route: {request.url}')
    return render_template('500.html', error=error, error_trace=error_trace), 500

# Функция для запуска игрового цикла
def start_game_loop():
    with app.app_context():
        battle_manager = BattleManager()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(battle_manager.start_game())

# Функция для запуска серверов ZeroMQ
def start_zmq_servers():
    status_manager = StatusManager()
    status_manager.start_server()
    conf = Config()
    
    server = ZMQServer()
    server.run()
    #message_manager = MessageManager()
    #message_manager.start_server()

if __name__ == "__main__":
    # Запуск серверов ZeroMQ в отдельном потоке
    zmq_thread = Thread(target=start_zmq_servers)
    zmq_thread.start()

    # Запуск игрового процесса в отдельном потоке
    game_thread = Thread(target=start_game_loop)
    game_thread.start()

    # Запуск сервера Flask
    app.run(debug=True, port=6511)

    # Ожидание завершения потоков (если нужно)
    zmq_thread.join()
    game_thread.join()
