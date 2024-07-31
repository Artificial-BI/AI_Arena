from datetime import datetime
from models import db, Arena, Tournament, TournamentMatch, Fight, Role, Player, ArenaChatMessage, Character
from gemini import GeminiAssistant
from character_manager import CharacterManager
import asyncio
from flask import current_app

class BattleManager:
    def __init__(self):
        self.referee_assistant = None

    async def organize_battle(self, character_ids, arena_id):
        if self.referee_assistant is None:
            self.referee_assistant = GeminiAssistant(self.get_role_instructions('referee'))

        results = []
        for character_id in character_ids:
            result = await self.evaluate_battle(character_id, arena_id)
            results.append(result)

        await self.save_battle(character_ids, arena_id, results)

    async def evaluate_battle(self, character_id, arena_id):
        message = f"Evaluate the battle for character {character_id} in arena {arena_id}."
        result = await self.referee_assistant.send_message(message)
        return result

    async def save_battle(self, character_ids, arena_id, results):
        with current_app.app_context():
            for character_id, result in zip(character_ids, results):
                fight = Fight(
                    character_id=character_id,
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

    async def start_test_battle(self):
        # Создание заглушек для арены и персонажей
        arena_id = await self.create_test_arena()
        character_ids = await self.create_test_characters()

        # Организация тестового боя
        await self.organize_battle(character_ids, arena_id)

    async def create_test_arena(self):
        # Создание заглушки для арены
        description = "Test Arena"
        parameters = '{"obstacles": "low", "weather": "clear"}'
        with current_app.app_context():
            arena = Arena(description=description, parameters=parameters)
            db.session.add(arena)
            db.session.commit()
        return arena.id

    async def create_test_characters(self):
        # Создание заглушек для персонажей
        with current_app.app_context():
            character1 = Character(
                user_id=1,  # Предположим, что у нас есть пользователь с ID 1
                name="Test Character 1",
                description="A brave warrior",
                image_url="images/default/player1.png",
                traits='{"strength": 10, "speed": 8, "intelligence": 6}'
            )
            character2 = Character(
                user_id=2,  # Предположим, что у нас есть пользователь с ID 2
                name="Test Character 2",
                description="A cunning mage",
                image_url="images/default/player2.png",
                traits='{"strength": 5, "speed": 7, "intelligence": 10}'
            )
            db.session.add(character1)
            db.session.add(character2)
            db.session.commit()
        return [character1.id, character2.id]

class ArenaManager:
    def __init__(self):
        self.arena_assistant = None

    async def create_arena(self, description, parameters):
        if self.arena_assistant is None:
            self.arena_assistant = GeminiAssistant(self.get_role_instructions('arena'))

        arena_description = await self.arena_assistant.send_message(f"Create an arena with these parameters: {parameters}")
        with current_app.app_context():
            arena = Arena(description=description, parameters=arena_description)
            db.session.add(arena)
            db.session.commit()
        return arena.id

    def get_role_instructions(self, role_name):
        with current_app.app_context():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                raise ValueError(f"Role '{role_name}' not found in the database")
            return role.instructions

class TournamentManager:
    def __init__(self):
        self.tournament_assistant = None

    async def create_tournament(self, name, format):
        if self.tournament_assistant is None:
            self.tournament_assistant = GeminiAssistant(self.get_role_instructions('tournament'))

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
