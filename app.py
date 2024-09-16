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
from utils import count_runs, is_odd
from threading import Thread, Event
import logging
 
# --- app.py ---

app = Flask(__name__)
app.config.from_object(Config)

if not app.debug:
    configure_logging(app)

# Инициализация расширений и базы данных
init_extensions_and_db(app)

# Логгер приложения
logger = logging.getLogger(__name__)

def clear_table():
    """Очищаем таблицы PreRegistrar и Registrar"""
    with app.app_context():
        try:
            db.session.query(PreRegistrar).delete()
            db.session.query(Registrar).delete()
            db.session.commit()
            app.logger.info("Очистка таблиц Registrar и PreRegistrar.")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Ошибка при очистке таблиц Registrar и PreRegistrar: {e}")

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
app.register_blueprint(admin_bp,  url_prefix='/admin')
app.register_blueprint(arena_bp,  url_prefix='/arena')

from webhook import webhook_bp
app.register_blueprint(webhook_bp)

# Доступ к глобальным переменным Jinja
app.jinja_env.globals.update(enumerate=enumerate)

# Очистка таблиц при запуске приложения
clear_table()

# Обработчики ошибок
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
def start_game_loop(stop_event):
    """Запуск игрового цикла с использованием asyncio"""
    with app.app_context():
        
        battle_manager = BattleManager()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        #while not stop_event.is_set():
        loop.run_until_complete(battle_manager.start_game())


# Функция для запуска серверов ZeroMQ
def start_zmq_servers(stop_event):
    """Запуск серверов ZeroMQ для обработки сообщений"""
    #initialize_database()  # Инициализация базы данных перед запуском серверов

    status_manager = StatusManager()
    
    # Запускаем сервер для управления статусами (ZeroMQ)
    zmq_thread_status = Thread(target=status_manager.start_server)
    zmq_thread_status.start()
  
    # Создаем сервер сообщений
    #zmq_server = ZMQServer()
 
    # try:
    #     while not stop_event.is_set():
    #         zmq_server.run()  # Запуск ZeroMQ сервера для обработки сообщений
    # except Exception as e:
    #     logger.error(f"Ошибка в ZMQ-сервере: {e}")
    # finally:
    #     logger.info("ZeroMQ сервер завершён.")
    #     zmq_thread_status.join()

# Основная точка входа
if __name__ == "__main__":
    # Создаём событие для остановки потоков
    stop_event = Event()
    
    if is_odd(): # Если Debug = True
        # Запуск серверов ZeroMQ в отдельном потоке
        zmq_thread = Thread(target=start_zmq_servers, args=(stop_event,))
        zmq_thread.start()

        # Запуск игрового процесса в отдельном потоке
        game_thread = Thread(target=start_game_loop, args=(stop_event,))
        game_thread.start()

    try:
        # Запуск сервера Flask
        app.run(debug=True, port=6511)
    except KeyboardInterrupt:
        logger.info("Остановка приложения...")

    finally:
        # Устанавливаем флаг для завершения потоков
        stop_event.set()

        # Ожидание завершения потоков
        zmq_thread.join()
        game_thread.join()

        logger.info("Приложение завершено корректно.")
