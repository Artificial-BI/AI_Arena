# --- load_user.py ---
import traceback
from flask import g, request, make_response, current_app, render_template
from models import db, User
import uuid
from hashlib import sha256

def uuid_to_int(uuid_str):
    # Хэшируем строку UUID
    hash_value = sha256(uuid_str.encode()).hexdigest()
    # Обрезаем хэш до 8 символов для уменьшения размера числа
    truncated_hash = hash_value[:8]
    # Преобразуем обрезанный хэш в целое число
    return int(truncated_hash, 16)


def load_user():
    try:
        user_id = request.cookies.get('user_id')
        #current_app.logger.info(f"User ID from cookies: {user_id}")
        if not user_id:
            user_id = str(uuid.uuid4())
            #current_app.logger.info(f"Generated new User ID: {user_id}")
            new_user = User(cookie_id=user_id, id=uuid_to_int(user_id))
            db.session.add(new_user)
            db.session.commit()
            g.user = new_user
            response = make_response()
            response.set_cookie('user_id', user_id, max_age=60*60*24*365)  # Cookie for one year
            current_app.logger.info(f"Set cookie and returning response: {response}")
            return response

        g.user = User.query.filter_by(cookie_id=user_id).first()
        #current_app.logger.info(f"User from database: {g.user}")
        if not g.user:
            new_user = User(cookie_id=user_id, id=uuid_to_int(user_id))
            db.session.add(new_user)
            db.session.commit()
            g.user = new_user
    except Exception as e:
        current_app.logger.error(f"Error in load_user: {e}")
        current_app.logger.error(f"Stack trace: {traceback.format_exc()}")
        return render_template('500.html', error=str(e), error_trace=traceback.format_exc()), 500
