import traceback
from flask import g, request, make_response, Flask, current_app, render_template
from functools import wraps
from models import db, User
import uuid

app = Flask(__name__)

def initialize_user(f):
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
                g.user = new_user
                response = f(*args, **kwargs)
                if response is None:
                    current_app.logger.error("The view function did not return a valid response after generating new user.")
                    raise TypeError("The view function did not return a valid response.")
                response = make_response(response)
                response.set_cookie('user_id', user_id, max_age=60*60*24*365)  # Cookie for one year
                current_app.logger.info(f"Set cookie and returning response: {response}")
                return response

            g.user = User.query.filter_by(cookie_id=user_id).first()
            current_app.logger.info(f"User from database: {g.user}")
            if not g.user:
                new_user = User(cookie_id=user_id)
                db.session.add(new_user)
                db.session.commit()
                g.user = new_user

            response = f(*args, **kwargs)
            current_app.logger.info(f"Response from view function: {response}")
            if response is None:
                current_app.logger.error("The view function did not return a valid response.")
                raise TypeError("The view function did not return a valid response.")
            response = make_response(response)
            current_app.logger.info(f"Returning the decorated response: {response}")
            return response
        except Exception as e:
            current_app.logger.error(f"Error in decorated_function: {e}")
            current_app.logger.error(f"Stack trace: {traceback.format_exc()}")
            return render_template('500.html', error=str(e), error_trace=traceback.format_exc()), 500

    return decorated_function

# Включение логирования
if not app.debug:
    from logging_config import configure_logging
    configure_logging(app)

app.logger.info("Logging is configured.")
