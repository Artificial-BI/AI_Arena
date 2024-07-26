from flask import Blueprint, render_template
# from models import Tournament, Player

index_bp = Blueprint('index_bp', __name__)

@index_bp.route('/')
def index():
    # Комментируем запросы к базе данных
    # tournaments = Tournament.query.all()
    # top_players = Player.query.order_by(Player.score.desc()).limit(10).all()
    tournaments = []
    top_players = []
    return render_template('index.html', tournaments=tournaments, top_players=top_players)
