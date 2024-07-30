# index_routes.py

from flask import Blueprint, render_template
from models import Tournament, TopPlayer
from default import default_tournaments, default_top_players

index_bp = Blueprint('index_bp', __name__)

@index_bp.route('/')
def index():
    # Пытаемся получить данные из базы данных, если они существуют
    tournaments = Tournament.query.all() or default_tournaments
    top_players = TopPlayer.query.order_by(TopPlayer.weekly_wins.desc()).limit(10).all() or default_top_players

    # Преобразуем объекты из базы данных в словари, если они не пустые
    if tournaments and not isinstance(tournaments, list):
        tournaments = [tournament.to_dict() for tournament in tournaments]

    if top_players and not isinstance(top_players, list):
        top_players = [player.to_dict() for player in top_players]

    return render_template('index.html', tournaments=tournaments, top_players=top_players)
