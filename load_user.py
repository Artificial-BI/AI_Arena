from flask import g, request, jsonify, make_response, Flask
from functools import wraps
from models import db, User
import uuid

app = Flask(__name__)

def initialize_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.cookies.get('user_id')
        if not user_id:
            user_id = str(uuid.uuid4())
            new_user = User(cookie_id=user_id)
            db.session.add(new_user)
            db.session.commit()
            response = make_response(f(*args, **kwargs))
            response.set_cookie('user_id', user_id, max_age=60*60*24*365)
            return response

        g.user = User.query.filter_by(cookie_id=user_id).first()
        if not g.user:
            new_user = User(cookie_id=user_id)
            db.session.add(new_user)
            db.session.commit()
            g.user = new_user
        
        response = make_response(f(*args, **kwargs))
        return response

    return decorated_function

# @app.route('/')
# @initialize_user
# def index():
#     return jsonify({'message': 'Hello, your user ID is set.', 'user_id': g.user.cookie_id})

# if __name__ == '__main__':
#     app.run(debug=True)
