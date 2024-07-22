from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

db = SQLAlchemy()
migrate = Migrate()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    role = db.Column(db.String(64))  # 'player', 'admin', 'viewer'
    characters = db.relationship('Character', backref='owner', lazy='dynamic')
    messages = db.relationship('Message', backref='author', lazy='dynamic')
    name = db.Column(db.String(64))  # Добавляем поле name
    email = db.Column(db.String(120), unique=True)  # Добавляем поле email
    password = db.Column(db.String(128))  # Добавляем поле password

    def __repr__(self):
        return f'<User {self.username}>'

class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(64))
    description = db.Column(db.Text)
    image_url = db.Column(db.String(256))
    health_points = db.Column(db.Integer)
    is_alive = db.Column(db.Boolean, default=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

class RefereePrompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt_text = db.Column(db.Text)
    
class CommentatorPrompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt_text = db.Column(db.Text, nullable=False)


class Fight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character1_id = db.Column(db.Integer)
    character2_id = db.Column(db.Integer)
    arena_id = db.Column(db.Integer)
    result = db.Column(db.String(64))
    fight_date = db.Column(db.DateTime, default=datetime.utcnow)

class Arena(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(256))
    parameters = db.Column(db.Text)

class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    format = db.Column(db.String(64))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime, nullable=True)
    current_stage = db.Column(db.String(64))

class TournamentMatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'))
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'))
    status = db.Column(db.String(64))
