import traceback
from flask import g, request, make_response, current_app, jsonify, session
from models import db, User, Player
import uuid
import hashlib
from hashlib import sha256
import logging
from cookies import Cookies  # Импортируем класс Cookies

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def uuid_to_int(uuid_str):
    """
    Преобразует строковое представление UUID в целое число через SHA256,
    чтобы гарантировать уникальность, и делает результат совместимым с SQLite INTEGER.
    """
    hash_object = hashlib.sha256(uuid_str.encode())
    hash_code = hash_object.hexdigest()
    hash_int = int(hash_code, 16)
    max_int_value = 2**63 - 1
    unique_int = hash_int % max_int_value
    return unique_int

def load_user():
    cok = Cookies()
    try:
        user_id = session.get('user_id')

        if user_id:
            user = User.query.get(user_id)
            if user:
                g.user = user
                response = make_response(jsonify({
                    "status": "existing_user", 
                    "user_id": user.id,
                    "step_read": cok.get_cookie_for_user(user.id, 'step_read')
                }))
                
                # Увеличиваем значение step_read для этого пользователя
                response = cok.increment_cookie_for_user(response, user.id, 'step_read', max_age=86400)
                
                return response  # Возвращаем единый объект ответа

        # Если user_id нет в сессии, проверяем cookie
        cookie_id = cok.get_cookie('user_cookie_id')
        response = make_response()
        
        if not cookie_id:
            cookie_id = str(uuid.uuid4())
            response = cok.set_cookie(response, 'user_cookie_id', cookie_id)
        
        user_id = uuid_to_int(cookie_id)
        user = User(id=user_id, cookie_id=cookie_id)
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user_id
        g.user = user

        # Устанавливаем переменную step_read для пользователя на 24 часа
        response = cok.increment_cookie_for_user(response, user.id, 'step_read', max_age=86400)

        response_data = jsonify({
            "status": "new_user", 
            "user_id": user.id, 
            "step_read": cok.get_cookie_for_user(user.id, 'step_read')
        })
        return make_response(response_data)  # Возвращаем корректный объект ответа с данными

    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in load_user: {e}")
        return make_response(jsonify({"error": "Internal server error"}), 500)
