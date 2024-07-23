from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    username = request.form['username']
    password = generate_password_hash(request.form['password'])

    new_user = User(name=name, email=email, username=username, password=password)
    db.session.add(new_user)
    db.session.commit()

    flash('Регистрация прошла успешно! Теперь вы можете войти в систему.', 'success')
    return redirect(url_for('main.index'))

@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        session['username'] = user.username
        flash('Вход в систему выполнен успешно!', 'success')
        return redirect(url_for('main.index'))
    else:
        flash('Неверный логин или пароль.', 'danger')
        return redirect(url_for('main.index'))

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Вы вышли из системы.', 'success')
    return redirect(url_for('main.index'))
