from flask import Blueprint, render_template, current_app, request, g, make_response
from models import Tournament, TopPlayer, User
from default import default_tournaments, default_top_players
import uuid
from extensions import db
import traceback

index_bp = Blueprint('index_bp', __name__)

@index_bp.before_request
def before_request():
    user_id = request.cookies.get('user_id')
    if not user_id:
        user_id = str(uuid.uuid4())
        new_user = User(cookie_id=user_id)
        db.session.add(new_user)
        db.session.commit()
        g.user = new_user
    else:
        g.user = User.query.filter_by(cookie_id=user_id).first()
        if not g.user:
            new_user = User(cookie_id=user_id)
            db.session.add(new_user)
            db.session.commit()
            g.user = new_user

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
        response.set_cookie('user_id', g.user.cookie_id, max_age=60*60*24*365)  # Cookie for one year
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
