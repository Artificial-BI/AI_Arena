
# --- core.py ---

from datetime import datetime
from models import db, Arena, Tournament, TournamentMatch, Fight, Role, Player
from gemini import GeminiAssistant
from character_manager import CharacterManager
import asyncio
from flask import current_app

class BattleManager:
    def __init__(self):
        print('BattleManager')
        self.referee_assistant = None

    async def organize_battle(self, character1_id, character2_id, arena_id):
        # Инициализация ассистента при необходимости
        if self.referee_assistant is None:
            self.referee_assistant = GeminiAssistant(self.get_role_instructions('referee'))
        
        # Логика проведения боя
        result = await self.evaluate_battle(character1_id, character2_id)
        await self.save_battle(character1_id, character2_id, arena_id, result)

    async def evaluate_battle(self, character1_id, character2_id):
        # Логика оценки боя
        message = f"Evaluate the battle between character {character1_id} and character {character2_id}."
        result = await self.referee_assistant.send_message(message)
        return result

    async def save_battle(self, character1_id, character2_id, arena_id, result):
        with current_app.app_context():
            fight = Fight(
                character1_id=character1_id,
                character2_id=character2_id,
                arena_id=arena_id,
                result=result,
                fight_date=datetime.now()
            )
            db.session.add(fight)
            db.session.commit()

    def get_role_instructions(self, role_name):
        with current_app.app_context():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                raise ValueError(f"Role '{role_name}' not found in the database")
            return role.instructions

class ArenaManager:
    def __init__(self):
        print('ArenaManager')

    async def create_arena(self, description, parameters):
        with current_app.app_context():
            arena = Arena(description=description, parameters=parameters)
            db.session.add(arena)
            db.session.commit()

    async def configure_arena(self, arena_id, parameters):
        with current_app.app_context():
            arena = Arena.query.get(arena_id)
            if arena:
                arena.parameters = parameters
                db.session.commit()

    def get_role_instructions(self, role_name):
        with current_app.app_context():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                raise ValueError(f"Role '{role_name}' not found in the database")
            return role.instructions

class TournamentManager:
    def __init__(self):
        print('TournamentManager')

    async def create_tournament(self, name, format):
        with current_app.app_context():
            tournament = Tournament(
                name=name,
                format=format,
                start_date=datetime.now(),
                end_date=None,
                current_stage='initial'
            )
            db.session.add(tournament)
            db.session.commit()

    async def register_for_tournament(self, tournament_id, character_id):
        with current_app.app_context():
            match = TournamentMatch(
                tournament_id=tournament_id,
                character_id=character_id,
                status='scheduled'
            )
            db.session.add(match)
            db.session.commit()

    async def update_tournament(self, tournament_id, stage):
        with current_app.app_context():
            tournament = Tournament.query.get(tournament_id)
            if tournament:
                tournament.current_stage = stage
                db.session.commit()

    def get_role_instructions(self, role_name):
        with current_app.app_context():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                raise ValueError(f"Role '{role_name}' not found in the database")
            return role.instructions
