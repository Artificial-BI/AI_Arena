#=============================================================================================

import sys
import asyncio
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import tornado.platform.asyncio
from flask import Flask, render_template, request, g
from config import Config
from logging_config import configure_logging 
from initialization import init_extensions_and_db
from extensions import db
from models import PreRegistrar, Registrar, Player
import traceback
from core import BattleManager
from status_manager import StatusManager
from message_server import startMessagesServer
from utils import count_runs, is_odd, set_glob_var, get_glob_var
from threading import Thread, Event
import logging

app = Flask(__name__)
app.config.from_object(Config)

if not app.debug:
    configure_logging(app)

# Инициализация расширений и базы данных
init_extensions_and_db(app)

logger = logging.getLogger(__name__)

def one_start():
    res = is_odd()

    return res

def clear_table():
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
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(arena_bp, url_prefix='/arena')

from webhook import webhook_bp
app.register_blueprint(webhook_bp)

app.jinja_env.globals.update(enumerate=enumerate)

# Очистка таблиц при запуске приложения
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

# ===============================================      
async def start_game_loop(stop_event):
    with app.app_context():
        battle_manager = BattleManager()
        await battle_manager.start_game(stop_event)
        
def start_game_server(stop_event): 
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tornado.platform.asyncio.AsyncIOMainLoop().install()
    game_thread = Thread(target=loop.run_until_complete, args=(start_game_loop(stop_event),))
    game_thread.start()
    return game_thread

def start_messages_loop(stop_event):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(startMessagesServer(stop_event))
    except OSError as e:
        logger.error(f"Ошибка при запуске MessageServer: {e}")
    finally:
        loop.close()

def start_messages_server(stop_event):
    messages_thread = Thread(target=start_messages_loop, args=(stop_event,))
    messages_thread.start()
    return messages_thread

def run_flask_app(app, stop_event, base_port=6511):
    port = base_port
    while not stop_event.is_set():
        try:
            app.run(debug=True, port=port)
        except OSError as e:
            if "Address already in use" in str(e):
                logger.warning(f"Порт {port} занят. Flak уже запущен.")
            else:
                logger.error(f"Ошибка при запуске Flask: {e}")

if __name__ == "__main__":
    stop_event = Event()
    
    print('START:',get_glob_var('flask'))
    
    messages_thread = start_messages_server(stop_event)
    
    if not get_glob_var('flask'):
        set_glob_var('flask', True)
        game_thread = start_game_server(stop_event)    
    try:
        run_flask_app(app, stop_event)
    except KeyboardInterrupt:
        logger.info("Остановка приложения...")
    finally:
        set_glob_var('flask', False)
        stop_event.set()
        print(f"Приложение завершено корректно, status: {get_glob_var('flask')}")
        
