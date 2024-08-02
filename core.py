from datetime import datetime
from models import db, Arena, Tournament, TournamentMatch, Fight, Role, Player, ArenaChatMessage, Score, Character, Registrar
from gemini import GeminiAssistant
import asyncio
from flask import current_app
import logging
from utils import parse_arena
import json

class CoreComon:
    def get_role_instructions(self, role_name):
        # Получение инструкций для роли из базы данных
        with current_app.app_context():
            role = Role.query.filter_by(name=role_name).first()
            logging.info(f"get role: {role}")
            if not role:
                raise ValueError(f"Role '{role_name}' not found in the database")
            return role.instructions

class ArenaManager:
    def __init__(self):
        self.assistant = None
        self.ccom = CoreComon()

    async def generate_arena(self, character_data):
        logging.info("--- Generating arena ---")
        if self.assistant == None:
            role_instructions = self.ccom.get_role_instructions('arena')
            self.assistant = GeminiAssistant(role_instructions, False)

        parameters = await self.assistant.send_message(f"Generate arena with the following character data: {character_data}")
        arena_description = "Generated Arena based on characters"

        logging.info(f"arena_parameters: {parameters}")

        parsed_parameters = parse_arena(parameters)

        new_arena = Arena(description=arena_description, parameters=json.dumps(parsed_parameters))
        db.session.add(new_arena)
        db.session.commit()

        logging.info(f"Arena generated with ID: {new_arena.id}")
        return new_arena


class BattleManager:
    def __init__(self):
        self.ccom = CoreComon()
        self.referee_assistant = None
        self.commentator_assistant = None
        self.arena_manager = ArenaManager()

    async def manage_battle_round(self, character_data, arena):
        logging.info("--- Managing battle round ---")

        # Сохранение ходов участников в чат арены
        for character in character_data:
            move_description = f"{character['name']} performs a strategic move based on current recommendations."
            logging.info(f"Move for {character['name']}: {move_description}")
            new_chat_message = ArenaChatMessage(content=move_description, sender='fighter', user_id=character['user_id'], arena_id=arena.id, read_status=0)
            db.session.add(new_chat_message)
        db.session.commit()

        # Ожидание получения ходов от всех участников
        await self.wait_for_moves(arena.id, len(character_data))

        # Получение непрочитанных сообщений
        unread_messages = ArenaChatMessage.query.filter_by(arena_id=arena.id, read_status=0).all()
        moves = [(msg.user_id, msg.content) for msg in unread_messages]

        # Пометка сообщений как прочитанных
        for msg in unread_messages:
            msg.read_status = 1
        db.session.commit()

        # 6. Запрос к ассистенту рефери
        referee_evaluation = await self.evaluate_moves(character_data, arena, moves)

        # 7. Запрос к ассистенту комментатору
        commentary = await self.generate_commentary(character_data, arena, moves, referee_evaluation)

        logging.info("--- Battle round completed ---")

    async def wait_for_moves(self, arena_id, num_participants):
        logging.info("Waiting for moves from all participants")
        while True:
            unread_count = ArenaChatMessage.query.filter_by(arena_id=arena_id, read_status=0).count()
            if unread_count >= num_participants:
                break
            await asyncio.sleep(1)
        logging.info("All moves received")

        # Оценка ходов рефери
        referee_evaluation = await self.evaluate_moves(character_data, arena, moves)

        # Генерация комментариев комментатора
        commentary = await self.generate_commentary(character_data, arena, moves, referee_evaluation)

        logging.info("--- Battle round completed ---")

    async def wait_for_moves(self, arena_id, num_participants):
        logging.info("Waiting for moves from all participants")
        while True:
            unread_count = ArenaChatMessage.query.filter_by(arena_id=arena_id, read_status=0).count()
            if unread_count >= num_participants:
                break
            await asyncio.sleep(1)
        logging.info("All moves received")

    async def evaluate_moves(self, character_data, arena, moves):
        logging.info("Evaluating moves by referee")
        if self.referee_assistant is None:
            self.referee_assistant = GeminiAssistant(self.ccom.get_role_instructions('referee'))
        evaluation_message = f"Evaluate the following moves in arena {arena.id}: {moves}"
        if not evaluation_message.strip():
            logging.error("Empty evaluation message, skipping evaluation")
            return "No evaluation provided"
        evaluation = await self.referee_assistant.send_message(evaluation_message)
        logging.info(f"Referee evaluation: {evaluation}")
    
        # Сохранение результатов судейства в чат арены
        evaluation_message = ArenaChatMessage(content=evaluation, sender='referee', user_id=None, arena_id=arena.id, read_status=0)
        db.session.add(evaluation_message)
        db.session.commit()
        
        return evaluation


    async def generate_commentary(self, character_data, arena, moves, evaluation):
        logging.info("Generating commentary")
        if self.commentator_assistant is None:
            self.commentator_assistant = GeminiAssistant(self.ccom.get_role_instructions('commentator'))
        commentary_message = f"Generate commentary for the following moves in arena {arena.id}: {moves} with evaluation {evaluation}"
        if not commentary_message.strip():
            logging.error("Empty commentary message, skipping commentary")
            return "No commentary provided"
        commentary = await self.commentator_assistant.send_message(commentary_message)
        logging.info(f"Commentary: {commentary}")
        
        # Сохранение комментариев в общий чат
        commentary_message = ArenaChatMessage(content=commentary, sender='commentator', user_id=None, arena_id=arena.id, read_status=0)
        db.session.add(commentary_message)
        db.session.commit()
        
        return commentary


    # Start the test battle process
    async def start_test_battle(self):
        logging.info("--- Starting test battle ---")
        try:
            # 2. Получение данных зарегистрированных персонажей
            character_data = await self.get_registered_character_data()

            # 3. Генерация параметров и описания арены на основании характеристик участников и внесение результатов в базу
            arena = await self.arena_manager.generate_arena(character_data)

            # 4. Старт цикла раундов
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
        self.ccom = CoreComon()
        self.tournament_assistant = None

    async def create_tournament(self, name, format):
        logging.info(f"Creating tournament with name: {name} and format: {format}")
        if self.tournament_assistant is None:
            self.tournament_assistant = GeminiAssistant(self.ccom.get_role_instructions('tournament'))

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
