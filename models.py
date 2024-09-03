
# --- models.py ---

from datetime import datetime
from extensions import db  # Import an instance of SQLAlchemy from extensions.py

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    role = db.Column(db.String(64))
    characters = db.relationship('Character', backref='owner', lazy='dynamic')
    messages = db.relationship('Message', backref='author', lazy='dynamic')
    name = db.Column(db.String(64))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(128))
    cookie_id = db.Column(db.String(36), unique=True, nullable=True)
    
    # Связь с Player (удаляем player_id, поскольку Player уже связан с User через user_id)
    player = db.relationship('Player', backref='user', uselist=False)

    def __repr__(self):
        return f'<User {self.username}>'

from sqlalchemy.orm import relationship

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Сохранение ссылок и данных
    last_selected_character_id = db.Column(db.Integer, nullable=True)
    temp_character_traits = db.Column(db.Text, nullable=True)
    current_status = db.Column(db.String(50), nullable=True)
    arena_id = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f'<Player {self.name}>'



class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    traits = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Переименованное поле
    character_id = db.Column(db.Integer, nullable=True)  # Больше не связано с таблицей Player
    
    combat = db.Column(db.Integer, default=0)
    damage = db.Column(db.Integer, default=0)
    life = db.Column(db.Integer, default=100)

    def to_str(self):
        return (f"ID: {self.id}, "
                f"name: {self.name}, "
                f"Description: {self.description}, "
                f"traits: {self.traits}, "
                f"user_id: {self.user_id}, "
                f"character_id: {self.character_id}, "
                f"combat: {self.combat}, "
                f"damage: {self.damage}, "
                f"life: {self.life}")

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
    name = db.Column(db.String(64), nullable=False)  # 'fighter name'
    arena_id = db.Column(db.Integer, db.ForeignKey('arena.id'), nullable=True)
    read_status = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<ArenaChatMessage {self.content[:15]}>'

class AssistantReadStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), nullable=False)  # Идентификатор user
    message_id = db.Column(db.Integer, db.ForeignKey('arena_chat_message.id'))
    read_status = db.Column(db.Boolean, default=False)  # Статус прочтения: False - не прочитано, True - прочитано
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

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
    read_status = db.Column(db.Integer, default=0)

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
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    arena_id = db.Column(db.Integer, db.ForeignKey('arena.id'), nullable=False)
    result = db.Column(db.String(64))
    fight_date = db.Column(db.DateTime, default=datetime.utcnow)

# models.py
class Arena(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(256))
    parameters = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    image_url = db.Column(db.String(255), nullable=True)  # Добавляем поле для хранения URL изображения арены
    def to_str(self):
        return (f"Arena ID: {self.id}, "
                f"Description: {self.description}, "
                f"Parameters: {self.parameters}, "
                f"Date Created: {self.date_created.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"Image URL: {self.image_url if self.image_url else 'No Image'}")

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

class PreRegistrar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    arena_id = db.Column(db.Integer, db.ForeignKey('arena.id'), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='pre_registrations')
    character = db.relationship('Character', backref='pre_registrations')
    arena = db.relationship('Arena', backref='pre_registrations')

    def __repr__(self):
        return f'<PreRegistrar User ID: {self.user_id}, Character ID: {self.character_id}, Arena ID: {self.arena_id}>'

class Statuses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    state = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    time_state = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<name: {self.name}, state: {self.state}, description: {self.description} , time_state: {self.time_state}>'

class Registrar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    arena_id = db.Column(db.Integer, db.ForeignKey('arena.id'), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='registrations')
    character = db.relationship('Character', backref='registrations')
    arena = db.relationship('Arena', backref='registrations')

    def __repr__(self):
        return f'<Registrar User ID: {self.user_id}, Character ID: {self.character_id}, Arena ID: {self.arena_id}>'

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    arena_id = db.Column(db.Integer, db.ForeignKey('arena.id'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Score Arena ID: {self.arena_id}, Character ID: {self.character_id}, Score: {self.score}>'
