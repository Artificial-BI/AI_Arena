# --- models.py ---

from datetime import datetime
from extensions import db  # Import an instance of SQLAlchemy from extensions.py

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    role = db.Column(db.String(64))  # 'player', 'admin', 'viewer'
    characters = db.relationship('Character', backref='owner', lazy='dynamic')
    messages = db.relationship('Message', backref='author', lazy='dynamic')
    name = db.Column(db.String(64))  # Add the name field
    email = db.Column(db.String(120), unique=True)  # Adding an email field
    password = db.Column(db.String(128))  # Add the password field
    cookie_id = db.Column(db.String(36), unique=True, nullable=True)  # Field for cookie_id

    def __repr__(self):
        return f'<User {self.username}>'

class Character(db.Model):
    __tablename__ = 'character'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=True)  # Adding a foreign key
    name = db.Column(db.String(64))
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(256))
    traits = db.Column(db.Text, nullable=False)  # List of features in JSON format

    def __repr__(self):
        return f'<Character {self.name}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return f'<Message {self.content[:15]}>'
class ArenaChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    sender = db.Column(db.String(64), nullable=False)  # 'player1', 'player2', 'referee'
    arena_id = db.Column(db.Integer, db.ForeignKey('arena.id'), nullable=True)  # Add this line

    def __repr__(self):
        return f'<ArenaChatMessage {self.content[:15]}>'


class GeneralChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    sender = db.Column(db.String(64), nullable=False)  # 'player', 'viewer', 'referee'

    def __repr__(self):
        return f'<GeneralChatMessage {self.content[:15]}>'

class TacticsChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    sender = db.Column(db.String(64), nullable=False)  # 'player', 'viewer', 'referee'

    def __repr__(self):
        return f'<TacticsChatMessage {self.content[:15]}>'

class RefereePrompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt_text = db.Column(db.Text)

class CommentatorPrompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt_text = db.Column(db.Text, nullable=False)

class Fight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer)  # Fixed typo here
    arena_id = db.Column(db.Integer)
    result = db.Column(db.String(64))
    fight_date = db.Column(db.DateTime, default=datetime.utcnow)

class Arena(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(256))
    parameters = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)  # Add this line

class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    format = db.Column(db.String(64))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime, nullable=True)
    current_stage = db.Column(db.String(64))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'format': self.format,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'current_stage': self.current_stage
        }

class TopPlayer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    wins = db.Column(db.Integer, nullable=False)
    losses = db.Column(db.Integer, nullable=False)
    character_name = db.Column(db.String(64), nullable=False)
    weekly_wins = db.Column(db.Integer, nullable=False)
    weekly_losses = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'wins': self.wins,
            'losses': self.losses,
            'character_name': self.character_name,
            'weekly_wins': self.weekly_wins,
            'weekly_losses': self.weekly_losses
        }

class TournamentMatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'))
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'))
    status = db.Column(db.String(64))

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    instructions = db.Column(db.Text, nullable=False)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    characters = db.relationship('Character', backref='player', lazy=True)

    def __repr__(self):
        return f'<Player {self.name}>'
