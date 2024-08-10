import traceback
from flask import g, request, make_response, current_app, jsonify, session
from models import db, User, Player
import uuid
import hashlib
from hashlib import sha256
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def uuid_to_int(uuid_str):
    # Generate a hash using SHA256
    hash_object = hashlib.sha256(uuid_str.encode())
    hash_code = hash_object.hexdigest()

    # Convert the hash to an integer
    hash_int = int(hash_code, 16)

    # Use modulo to ensure the integer fits within the SQLite Integer range
    max_int_value = 2**63 - 1  # Maximum value for SQLite INTEGER
    unique_int = hash_int % max_int_value

    return unique_int

def load_user():
    try:
        # Проверяем, существует ли пользовательский идентификатор в сессии
        user_id = session.get('user_id')

        if user_id:
            # Если user_id уже есть в сессии, проверяем, существует ли пользователь с таким id
            user = User.query.get(user_id)
            if user:
                #logger.info(f"User with ID {user_id} already exists.")
                g.user = user
                return make_response(jsonify({"status": "existing_user", "user_id": user.id, "cookie_id": user.cookie_id}), 200)
            else:
                logger.error(f"User with ID {user_id} not found in the database.")
                session.pop('user_id', None)  # Удаляем некорректный user_id из сессии

        # Если user_id нет в сессии или он некорректен, создаем нового пользователя
        cookie_id = request.cookies.get('user_cookie_id')
        if not cookie_id:
            cookie_id = str(uuid.uuid4())
            response = make_response()
            response.set_cookie('user_cookie_id', cookie_id)

        user_id = uuid_to_int(cookie_id)
        user = User(id=user_id, cookie_id=cookie_id)
        db.session.add(user)
        db.session.commit()

        # Сохраняем новый user_id в сессии
        session['user_id'] = user_id

        logger.info(f"Created new user with ID {user_id}.")
        g.user = user
        return make_response(jsonify({"status": "new_user", "user_id": user.id, "cookie_id": user.cookie_id}), 201)

    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in load_user: {e}")
        return make_response(jsonify({"error": "Internal server error"}), 500)
