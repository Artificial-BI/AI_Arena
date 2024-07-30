import traceback
from flask import g, request, make_response, Flask #, current_app
from functools import wraps
from models import db, User
import uuid

app = Flask(__name__)


# Заглушка для декоратора
def initialize_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Здесь можно логировать вызовы для отладки
        #current_app.logger.info(f"initialize_user called for {f.__name__}")
        return f(*args, **kwargs)
    return decorated_function



def _initialize_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user_id = request.cookies.get('user_id')
            current_app.logger.info(f"User ID from cookies: {user_id}")
            if not user_id:
                user_id = str(uuid.uuid4())
                current_app.logger.info(f"Generated new User ID: {user_id}")
                new_user = User(cookie_id=user_id)
                db.session.add(new_user)
                db.session.commit()
                current_app.logger.info(f'Args: {args}, Kwargs: {kwargs}')
                response = make_response(f(*args, **kwargs))
                response.set_cookie('user_id', user_id, max_age=60*60*24*365)
                current_app.logger.info(f"Set cookie and returning response: {response}")
                return response

            g.user = User.query.filter_by(cookie_id=user_id).first()
            current_app.logger.info(f"User from database: {g.user}")
            if not g.user:
                new_user = User(cookie_id=user_id)
                db.session.add(new_user)
                db.session.commit()
                g.user = new_user

            current_app.logger.info(f'Args: {args}, Kwargs: {kwargs}')
            response = make_response(f(*args, **kwargs))
            current_app.logger.info(f"Returning the decorated response: {response}")
            return response
        except Exception as e:
            current_app.logger.error(f"Error in decorated_function: {e}")
            current_app.logger.error(f"Stack trace: {traceback.format_exc()}")
            raise

    return decorated_function

# Включение логирования
if not app.debug:
    import logging
    logging.basicConfig(level=logging.INFO)
    file_handler = logging.FileHandler('error.log')
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)

app.logger.info("Logging is configured.")
