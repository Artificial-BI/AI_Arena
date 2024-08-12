from flask import Blueprint, render_template, current_app, request, g, make_response
from models import Tournament, TopPlayer, User
from default import default_tournaments, default_top_players
from extensions import db
import traceback
import logging
from load_user import load_user

# --- index_routes.py ---
index_bp = Blueprint('index_bp', __name__)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@index_bp.before_request
def before_request():
    # Получаем ответ от load_user
    response = load_user()
    
    # Проверяем статус ответа
    if response.status_code != 200 and response.status_code != 201:
        return response  # Если статус не 200 или 201, возвращаем ответ как есть
    
    # Извлекаем данные пользователя из JSON ответа
    user_data = response.get_json()
    g.user_id = user_data.get('user_id')
    g.cookie_id = user_data.get('cookie_id')

@index_bp.route('/')
def index():
    current_app.logger.info("Entered the index view.")
    try:
        tournaments = Tournament.query.all() or default_tournaments
        top_players = TopPlayer.query.order_by(TopPlayer.weekly_wins.desc()).limit(10).all() or default_top_players

        if tournaments and not isinstance(tournaments, list):
            tournaments = [tournament.to_dict() for tournament in tournaments]

        if top_players and not isinstance(top_players, list):
            top_players = [player.to_dict() for player in top_players]

        response = make_response(render_template('index.html', tournaments=tournaments, top_players=top_players))
        # response.set_cookie('user_id', g.cookie_id, max_age=60*60*24*365)  # Cookie for one year
        return response
    except Exception as e:
        current_app.logger.error(f"Error in index view: {e}")
        current_app.logger.error(f"Stack trace: {traceback.format_exc()}")
        return render_template('500.html', error=str(e), error_trace=traceback.format_exc()), 500

@index_bp.route('/about')
def about():
    return render_template('about.html')

@index_bp.route('/contact')
def contact():
    return render_template('contact.html')
