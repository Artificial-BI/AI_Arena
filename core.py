from datetime import datetime
from models import db, Arena, Tournament, TournamentMatch, Fight, Role, Player, ArenaChatMessage, Score, Character, Registrar
from gemini import GeminiAssistant
import asyncio
from flask import current_app
import logging

class ArenaManager:
    def __init__(self):
        self.assistant = None  # Initialize the assistant here

    async def generate_arena(self, character_data):
        logging.info("--- Generating arena ---")
        if self.assistant is None:
            self.assistant = GeminiAssistant(self.get_role_instructions('arena'))
        parameters = await self.assistant.send_message(f"Generate arena with the following character data: {character_data}")
        arena_description = "Generated Arena based on characters"

        # Save the arena to the database
        new_arena = Arena(description=arena_description, parameters=parameters)
        db.session.add(new_arena)
        db.session.commit()

        logging.info(f"Arena generated with ID: {new_arena.id}")
        return new_arena

    def generate_tactic_recommendations(self, character, arena, chat_history):
        logging.info(f"Generating tactic recommendations for character: {character.name}")
        # This is where you would call your assistant to generate recommendations
        recommendations = "Generated tactic recommendations based on character, arena, and chat history."
        return recommendations

    def get_role_instructions(self, role_name):
        with current_app.app_context():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                raise ValueError(f"Role '{role_name}' not found in the database")
            return role.instructions

class BattleManager:
    def __init__(self):
        self.referee_assistant = None
        self.commentator_assistant = None
        self.artist_assistant = None
        self.arena_manager = ArenaManager()

    async def manage_battle_round(self, character_data, arena):
        logging.info("--- Managing battle round ---")

        # Cycle through participants to get their moves
        moves = []
        for character in character_data:
            recommendations = self.arena_manager.generate_tactic_recommendations(character, arena, [])
            move_description = f"{character['name']} performs a strategic move based on recommendations: {recommendations}"
            logging.info(f"Move for {character['name']}: {move_description}")
            moves.append((character['id'], move_description))
            # Save move to the arena chat
            new_chat_message = ArenaChatMessage(content=move_description, sender='fighter', user_id=character['user_id'], arena_id=arena.id)
            db.session.add(new_chat_message)
        db.session.commit()

        # Evaluate moves by referee
        referee_evaluation = await self.evaluate_moves(character_data, arena, moves)

        # Generate comments by commentator
        commentary = await self.generate_commentary(character_data, arena, moves, referee_evaluation)

        # Generate images by artist
        battle_image = await self.generate_battle_image(character_data, arena, moves)

        logging.info("--- Battle round completed ---")

    async def evaluate_moves(self, character_data, arena, moves):
        logging.info("Evaluating moves by referee")
        if self.referee_assistant is None:
            self.referee_assistant = GeminiAssistant(self.get_role_instructions('referee'))
        evaluation_message = f"Evaluate the following moves in arena {arena.id}: {moves}"
        if not evaluation_message.strip():
            logging.error("Empty evaluation message, skipping evaluation")
            return "No evaluation provided"
        evaluation = await self.referee_assistant.send_message(evaluation_message)
        logging.info(f"Referee evaluation: {evaluation}")
        return evaluation

    async def generate_commentary(self, character_data, arena, moves, evaluation):
        logging.info("Generating commentary")
        if self.commentator_assistant is None:
            self.commentator_assistant = GeminiAssistant(self.get_role_instructions('commentator'))
        commentary_message = f"Generate commentary for the following moves in arena {arena.id}: {moves} with evaluation {evaluation}"
        if not commentary_message.strip():
            logging.error("Empty commentary message, skipping commentary")
            return "No commentary provided"
        commentary = await self.commentator_assistant.send_message(commentary_message)
        logging.info(f"Commentary: {commentary}")
        return commentary

    async def generate_battle_image(self, character_data, arena, moves):
        logging.info("Generating battle image")
        if self.artist_assistant is None:
            self.artist_assistant = GeminiAssistant(self.get_role_instructions('artist'))
        image_message = f"Generate an image for the following moves in arena {arena.id}: {moves}"
        if not image_message.strip():
            logging.error("Empty image message, skipping image generation")
            return "No image generated"
        image = await self.artist_assistant.send_message(image_message)
        logging.info(f"Generated battle image: {image}")
        return image

    async def start_test_battle(self):
        logging.info("--- Starting test battle ---")
        try:
            # Получение данных зарегистрированных персонажей
            character_data = await self.get_registered_character_data()

            # Генерация арены с использованием зарегистрированных персонажей
            arena = await self.arena_manager.generate_arena(character_data)

            # Цикл по двум кругам битвы
            for round_number in range(2):
                logging.info(f"--- Starting round {round_number + 1} ---")
                await self.manage_battle_round(character_data, arena)
            logging.info("Test battle completed")
        except Exception as e:
            logging.error(f"Error in test battle: {e}")

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
                        "traits": character.traits,
                        "user_id": registration.user_id
                    })
            return character_data

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
