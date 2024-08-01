from datetime import datetime
from models import db, Arena, Tournament, TournamentMatch, Fight, Role, Player, ArenaChatMessage, Score, Character, Registrar
from gemini import GeminiAssistant
import asyncio
from flask import current_app
import logging

class ArenaManager:
    def __init__(self):
        self.assistant = None  # Initialize the assistant here

    async def generate_arena(self):
        logging.info("Generating arena")
        # Fetch character data from the database
        registered_characters = Registrar.query.all()
        characters = []
        for registration in registered_characters:
            character = Character.query.get(registration.character_id)
            if character:
                characters.append({
                    'name': character.name,
                    'description': character.description,
                    'traits': character.traits,
                })

        # Generate arena based on character data
        arena_description = "Generated Arena based on characters"
        arena_parameters = {
            'difficulty': 'high',
            'environment': 'lava',
        }

        # Save the arena to the database
        new_arena = Arena(description=arena_description, parameters=str(arena_parameters))
        db.session.add(new_arena)
        db.session.commit()

        logging.info(f"Arena generated with ID: {new_arena.id}")
        return new_arena

    def generate_tactic_recommendations(self, character, arena, chat_history):
        logging.info(f"Generating tactic recommendations for character: {character.name}")
        # This is where you would call your assistant to generate recommendations
        recommendations = "Generated tactic recommendations based on character, arena, and chat history."
        return recommendations

    async def create_arena_with_registered_characters(self, character_data):
        logging.info("Creating arena with registered characters")
        # Создание арены с использованием данных зарегистрированных персонажей
        description = "Arena for battle"
        parameters = await self.generate_arena_parameters(character_data)
        with current_app.app_context():
            arena = Arena(description=description, parameters=parameters)
            db.session.add(arena)
            db.session.commit()
        logging.info(f"Arena created with ID: {arena.id}")
        return arena.id

    async def generate_arena_parameters(self, character_data):
        if self.assistant is None:
            self.assistant = GeminiAssistant(self.get_role_instructions('arena'))
        parameters = await self.assistant.send_message(f"Generate arena with the following character data: {character_data}")
        return parameters

    def get_role_instructions(self, role_name):
        with current_app.app_context():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                raise ValueError(f"Role '{role_name}' not found in the database")
            return role.instructions

class BattleManager:
    def __init__(self):
        self.referee_assistant = None
        self.arena_manager = ArenaManager()

    async def manage_battle(self):
        try:
            logging.info("Managing battle")
            # Получение данных зарегистрированных персонажей
            character_data = await self.get_registered_character_data()

            # Генерация арены с использованием зарегистрированных персонажей
            arena_id = await self.arena_manager.create_arena_with_registered_characters(character_data)

            # Получение ID зарегистрированных персонажей
            character_ids = [char['id'] for char in character_data]

            if not character_ids:
                raise ValueError("No characters registered for the battle.")

            # Организация боя
            await self.organize_battle(character_ids, arena_id)

        except Exception as e:
            current_app.logger.error(f"Error managing battle: {e}")

    async def organize_battle(self, character_ids, arena_id):
        logging.info("Organizing battle")
        if self.referee_assistant is None:
            self.referee_assistant = GeminiAssistant(self.get_role_instructions('referee'))

        results = []
        for character_id in character_ids:
            result = await self.evaluate_battle(character_id, arena_id)
            results.append(result)

        await self.save_battle(character_ids, arena_id, results)

    async def evaluate_battle(self, character_id, arena_id):
        logging.info(f"Evaluating battle for character ID: {character_id} in arena ID: {arena_id}")
        message = f"Evaluate the battle for character {character_id} in arena {arena_id}."
        result = await self.referee_assistant.send_message(message)
        return result

    async def save_battle(self, character_ids, arena_id, results):
        logging.info("Saving battle results")
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

    async def get_registered_character_data(self):
        logging.info("Fetching registered character data")
        with current_app.app_context():
            registrations = Registrar.query.all()
            character_data = []
            for registration in registrations:
                character = Character.query.get(registration.character_id)
                if character:
                    character_data.append({
                        "id": character.id,
                        "name": character.name,
                        "description": character.description,
                        "traits": character.traits
                    })
            return character_data

    async def start_test_battle(self):
        logging.info("Starting test battle")
        # Step 1: Generate Arena
        arena = await self.arena_manager.generate_arena()

        # Step 2: Fetch Characters registered for this arena
        registered_characters = Registrar.query.filter_by(arena_id=arena.id).all()
        characters = [Character.query.get(reg.character_id) for reg in registered_characters]

        # Step 3: Simulate battle for 2 rounds
        for round_number in range(2):
            logging.info(f"Starting round {round_number + 1}")
            for character in characters:
                # Fetch arena chat history
                chat_history = ArenaChatMessage.query.filter_by(arena_id=arena.id).all()

                # Generate recommendations from Tactics Manager
                recommendations = self.arena_manager.generate_tactic_recommendations(character, arena, chat_history)

                # Generate moves based on recommendations
                move_description = f"{character.name} performs a strategic move based on recommendations."
                logging.info(f"{character.name} move: {move_description}")

                # Save move to the arena chat
                new_chat_message = ArenaChatMessage(content=move_description, sender='fighter', user_id=character.user_id, arena_id=arena.id)
                db.session.add(new_chat_message)

            db.session.commit()
        logging.info("Test battle completed")

class TournamentManager:
    def __init__(self):
        self.tournament_assistant = None

    async def create_tournament(self, name, format):
        logging.info(f"Creating tournament with name: {name} and format: {format}")
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
        logging.info(f"Registering character ID: {character_id} for tournament ID: {tournament_id}")
        with current_app.app_context():
            match = TournamentMatch(
                tournament_id=tournament_id,
                character_id=character_id,
                status='scheduled'
            )
            db.session.add(match)
            db.session.commit()

    async def update_tournament(self, tournament_id, stage):
        logging.info(f"Updating tournament ID: {tournament_id} to stage: {stage}")
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
