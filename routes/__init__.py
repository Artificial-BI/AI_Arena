# -- __init__.py --
from flask import Blueprint

common_bp = Blueprint('common', __name__)
index_bp = Blueprint('index', __name__)
player_bp = Blueprint('player', __name__)
viewer_bp = Blueprint('viewer', __name__)
admin_bp = Blueprint('admin', __name__)
arena_bp = Blueprint('arena', __name__)  # Добавляем новый блюпринт

# Импортируем маршруты, чтобы они зарегистрировались в приложении
from . import common_routes, index_routes, player_routes, viewer_routes, admin_routes, arena_routes  # Импортируем новый маршрут
