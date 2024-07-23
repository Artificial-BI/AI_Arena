from datetime import datetime
from models import db, Arena, Tournament, TournamentMatch, Fight, Role, Player
from gemini import GeminiAssistant
from character_manager import CharacterManager  # Импортируем CharacterManager
import asyncio

# class BattleManager:
#     def __init__(self, gemini_api_key):
#         self.referee_assistant = GeminiAssistant(gemini_api_key, self.get_role_instructions('referee'))

#     async def organize_battle(self, character1_id, character2_id, arena_id):
#         # Логика проведения боя
#         result = await self.evaluate_battle(character1_id, character2_id)
#         await self.save_battle(character1_id, character2_id, arena_id, result)

#     async def evaluate_battle(self, character1_id, character2_id):
#         # Логика оценки боя
#         # Здесь будет взаимодействие с нейросетью "рефери"
#         message = f"Evaluate the battle between character {character1_id} and character {character2_id}."
#         result = await self.referee_assistant.send_message(message)
#         return result

#     async def save_battle(self, character1_id, character2_id, arena_id, result):
#         fight = Fight(
#             character1_id=character1_id,
#             character2_id=character2_id,
#             arena_id=arena_id,
#             result=result,
#             fight_date=datetime.now()
#         )
#         db.session.add(fight)
#         db.session.commit()

#     def get_role_instructions(self, role_name):
#         role = Role.query.filter_by(name=role_name).first()
#         if not role:
#             raise ValueError(f"Role '{role_name}' not found in the database")
#         return role.instructions

# class ArenaManager:
#     def __init__(self, gemini_api_key):
#         self.arena_assistant = GeminiAssistant(gemini_api_key, self.get_role_instructions('arena'))

#     async def create_arena(self, description, parameters):
#         arena = Arena(description=description, parameters=parameters)
#         db.session.add(arena)
#         db.session.commit()

#     async def configure_arena(self, arena_id, parameters):
#         arena = Arena.query.get(arena_id)
#         if arena:
#             arena.parameters = parameters
#             db.session.commit()

#     def get_role_instructions(self, role_name):
#         role = Role.query.filter_by(name=role_name).first()
#         if not role:
#             raise ValueError(f"Role '{role_name}' not found in the database")
#         return role.instructions

# class TournamentManager:
#     def __init__(self, gemini_api_key):
#         self.tournament_assistant = GeminiAssistant(gemini_api_key, self.get_role_instructions('tournament'))

#     async def create_tournament(self, name, format):
#         tournament = Tournament(
#             name=name,
#             format=format,
#             start_date=datetime.now(),
#             end_date=None,
#             current_stage='initial'
#         )
#         db.session.add(tournament)
#         db.session.commit()

#     async def register_for_tournament(self, tournament_id, character_id):
#         match = TournamentMatch(
#             tournament_id=tournament_id,
#             character_id=character_id,
#             status='scheduled'
#         )
#         db.session.add(match)
#         db.session.commit()

#     async def update_tournament(self, tournament_id, stage):
#         tournament = Tournament.query.get(tournament_id)
#         if tournament:
#             tournament.current_stage = stage
#             db.session.commit()

#     def get_role_instructions(self, role_name):
#         role = Role.query.filter_by(name=role_name).first()
#         if not role:
#             raise ValueError(f"Role '{role_name}' not found in the database")
#         return role.instructions

# # Пример использования

# async def main():
#     gemini_api_key = 'YOUR_API_KEY'
#     battle_manager = BattleManager(gemini_api_key)
#     await battle_manager.organize_battle(1, 2, 3)

#     arena_manager = ArenaManager(gemini_api_key)
#     await arena_manager.create_arena("Test Arena", {"size": "large"})

#     tournament_manager = TournamentManager(gemini_api_key)
#     await tournament_manager.create_tournament("Championship", "single-elimination")
#     await tournament_manager.register_for_tournament(1, 1)
#     await tournament_manager.update_tournament(1, "quarterfinals")

#     character_manager = CharacterManager(gemini_api_key)
#     new_character = await character_manager.generate_character("A brave knight with unmatched swordsmanship.", "character_creation")
#     print(f"Generated character: {new_character.traits}")

# if __name__ == "__main__":
#     asyncio.run(main())
from flask import current_app

class BattleManager:
    def __init__(self, gemini_api_key):
        self.gemini_api_key = gemini_api_key

    async def organize_battle(self, character1_id, character2_id, arena_id):
        # Логика проведения боя
        result = await self.evaluate_battle(character1_id, character2_id)
        await self.save_battle(character1_id, character2_id, arena_id, result)

    async def evaluate_battle(self, character1_id, character2_id):
        # Логика оценки боя
        # Здесь будет взаимодействие с нейросетью "рефери"
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
    def __init__(self, gemini_api_key):
        self.gemini_api_key = gemini_api_key

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
    def __init__(self, gemini_api_key):
        self.gemini_api_key = gemini_api_key

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
