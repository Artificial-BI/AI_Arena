# from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response
# from models import db, User
# from werkzeug.security import generate_password_hash, check_password_hash
# import uuid

# auth_bp = Blueprint('auth', __name__)

# @auth_bp.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         name = request.form['name']
#         email = request.form['email']
#         username = request.form['username']
#         password = request.form['password']
        
#         if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
#             flash('A user with this username or email already exists.', 'danger')
#             return redirect(url_for('auth.register'))
        
#         hashed_password = generate_password_hash(password)
#         new_user = User(name=name, email=email, username=username, password=hashed_password)
#         db.session.add(new_user)
#         db.session.commit()

#         flash('Registration successful! You can now log in.', 'success')
#         return redirect(url_for('auth.login'))
#     return render_template('register.html')

# @auth_bp.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         user = User.query.filter_by(username=username).first()
#         if user and check_password_hash(user.password, password):
#             session['user_id'] = user.id
#             session['username'] = user.username
#             if not user.cookie_id:
#                 user.cookie_id = str(uuid.uuid4())
#                 db.session.commit()
#             response = make_response(redirect(url_for('main.index')))
#             response.set_cookie('user_id', user.cookie_id, max_age=60*60*24*365)  # Cookie for one year
#             flash('Login successful!', 'success')
#             return response
#         else:
#             flash('Invalid username or password.', 'danger')
#             return redirect(url_for('auth.login'))
#     return render_template('login.html')

# @auth_bp.route('/logout')
# def logout():
#     session.pop('user_id', None)
#     session.pop('username', None)
#     response = make_response(redirect(url_for('main.index')))
#     response.set_cookie('user_id', '', expires=0)  # Delete cookie
#     flash('You have been logged out.', 'success')
#     return response
