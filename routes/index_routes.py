# index_routes.py

from flask import Blueprint, render_template, current_app
from models import Tournament, TopPlayer
from default import default_tournaments, default_top_players

index_bp = Blueprint('index_bp', __name__)

@index_bp.route('/')
def index():
    current_app.logger.info("-------------------- Entered the index view. ------------------------")
    # Пытаемся получить данные из базы данных, если они существуют
    tournaments = Tournament.query.all() or default_tournaments
    top_players = TopPlayer.query.order_by(TopPlayer.weekly_wins.desc()).limit(10).all() or default_top_players
    #current_app.logger.info(f" ---- 1 -----   in Rendered the index tournaments: {tournaments} | {top_players}")
    # Преобразуем объекты из базы данных в словари, если они не пустые
    if tournaments and not isinstance(tournaments, list):
        tournaments = [tournament.to_dict() for tournament in tournaments]

    if top_players and not isinstance(top_players, list):
        top_players = [player.to_dict() for player in top_players]

    # # Отладочный вывод данных
    # current_app.logger.info(f"Tournaments: {tournaments}")
    # current_app.logger.info(f"Top Players: {top_players}")

    # Возвращаем рендеринг шаблона с данными
    #current_app.logger.info(f"in Rendered the index tournaments: {tournaments} | {top_players}")
    response = render_template('index.html', tournaments=tournaments, top_players=top_players)
    #current_app.logger.info(f"out Rendered the index response: {response}")
    return response
