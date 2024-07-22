from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import sqlite3
from datetime import datetime

db = SQLAlchemy()
migrate = Migrate()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    role = db.Column(db.String(64))  # 'player', 'admin', 'viewer'
    characters = db.relationship('Character', backref='owner', lazy='dynamic')
    messages = db.relationship('Message', backref='author', lazy='dynamic')

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

# Подключение к базе данных
def get_db_connection():
    conn = sqlite3.connect('ai_arena.db')
    conn.row_factory = sqlite3.Row
    return conn

# Пример моделей данных
def create_tables():
    connection = get_db_connection()
    with connection as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY,
                name TEXT,
                attributes TEXT,
                player_id INTEGER,
                created_date TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                password TEXT,
                registered_date TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS fights (
                id INTEGER PRIMARY KEY,
                character1_id INTEGER,
                character2_id INTEGER,
                arena_id INTEGER,
                result TEXT,
                fight_date TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS arenas (
                id INTEGER PRIMARY KEY,
                description TEXT,
                parameters TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tournaments (
                id INTEGER PRIMARY KEY,
                name TEXT,
                format TEXT,
                start_date TEXT,
                end_date TEXT,
                current_stage TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tournament_matches (
                id INTEGER PRIMARY KEY,
                tournament_id INTEGER,
                character_id INTEGER,
                status TEXT,
                match_date TEXT
            )
        ''')

create_tables()
    
    
    
