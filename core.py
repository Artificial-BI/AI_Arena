import asyncio
import logging
import json
import re
import time
from datetime import datetime
from flask import current_app
from models import (Arena, ArenaChatMessage, Character, GeneralChatMessage, PreRegistrar, Registrar, Role, TacticsChatMessage, db)
from gemini import GeminiAssistant
from open_ai import AIDesigner
from tactics_manager import Fighter, TacticsManager
from utils import parse_arena, parse_referee

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoreCommon:
    def get_role_instructions(self, role_name):
        with current_app.app_context():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                raise ValueError(f"Role '{role_name}' not found in the database")
            logger.info(f"Instructions received for role: {role}")
            return role.instructions

class ArenaManager:
    def __init__(self, loop=None):
        self.assistant = None
        self.ccom = CoreCommon()
        self.loop = loop or asyncio.get_event_loop()

    def _initialize_assistant(self):
        if self.assistant is None:
            self.assistant = GeminiAssistant('arena')

    def message_to_Arena(self, _message):
        set_message = ArenaChatMessage(content=_message, sender='system', user_id=None, read_status=0)
        db.session.add(set_message)
        db.session.commit()

    async def generate_arena(self, character_data):
        logger.info("Generating arena")
        self._initialize_assistant()

        parameters = await self.assistant.send_message(
            f"Generate arena with the following character data: {character_data}"
        )

        if not parameters.strip():
            logger.error("Received empty parameters from assistant")
            raise ValueError("Invalid parameters: 'parameters' must not be empty. Please provide a non-null value.")

        arena_description = parameters
        parsed_parameters = parse_arena(parameters)

        new_arena = Arena(description=arena_description, parameters=json.dumps(parsed_parameters))
        db.session.add(new_arena)
        db.session.commit()

        designer = AIDesigner()
        filename = re.sub(r'[\\/*?:"<>|]', "", f"arena_{new_arena.id}")
        image_filename = f"{filename}.png"
        image_url = designer.create_image(arena_description, "arena", image_filename)

        new_arena.image_url = image_url
        db.session.commit()

        self.message_to_Arena(f"Arena description: {arena_description}\nParameters: {parsed_parameters}")

        logger.info(f"Arena generated with ID: {new_arena.id} and image {image_url}")
        return new_arena

class BattleManager:
    def __init__(self, loop=None):
        self.ccom = CoreCommon()
        self.referee_assistant = None
        self.commentator_assistant = None
        self.arena_manager = ArenaManager(loop=loop)
        self.battle_count = 0
        self.round_count = 0
        self.fighter = Fighter(loop=loop)
        self.tactics_manager = TacticsManager(fighter_instance=self.fighter, loop=loop)
        self.timer_in_progress = False
        self.battle_in_progress = False
        self.timer_start_time = None
        self.countdown_duration = 30
        self.moves_count = {}
        self.loop = loop or asyncio.get_event_loop()

    def message_to_Arena(self, _message):
        set_message = ArenaChatMessage(content=_message, sender='system', user_id=None, read_status=0)
        db.session.add(set_message)
        db.session.commit()

    async def start_battle(self, user_id):
        logger.info(f"--- Battle {self.battle_count + 1} started ---")
        try:
            self.battle_in_progress = True
            self.battle_count += 1
            await self._clear_previous_battle()

            content = f"--- Battle № {self.battle_count} ---"
            self.message_to_Arena(content)

            character_data = await self.get_registered_character_data()
            arena = await self.arena_manager.generate_arena(character_data)

            for character in character_data:
                self.tactics_manager.add_fighter(character['user_id'])
                self.fighter.add_fighter(character['user_id'])

            logger.info("-------------- STARTING MAIN BATTLE CYCLE ---------------")
            max_rounds = 2  # Set the maximum number of rounds in the battle
            for round_number in range(max_rounds):
                if not self.battle_in_progress:
                    break
                logger.info(f"Round {round_number + 1} started")
                self.message_to_Arena(f"Round N: {round_number + 1}")
                await self.manage_battle_round(character_data, arena, max_moves=3)

            self.message_to_Arena("--- Battle stop ---")
            logger.info("Battle finished")
        except Exception as e:
            logger.error(f"Error in battle: {e}", exc_info=True)
            raise
        finally:
            self.battle_in_progress = False
            self.stop_timer()
            self.tactics_manager.stop()
            self.fighter.stop()
            await self.handle_post_battle_registration()


    async def manage_battle_round(self, character_data, arena, max_moves):
        self.round_count += 1
        for char in character_data:
            logger.info("Processing actions for the fighter ")
            await self.tactics_manager.generate_tactics_and_moves(char['user_id'], max_moves, arena)
            logger.info("Fighter actions completed")

        logger.info("All fighters have finished their moves, starting evaluation and commentary generation.")
        await self.evaluate_and_comment_round(character_data, arena)
        logger.info("Round completed, checking for battle end.")

    def start_timer(self, duration):
        self.countdown_duration = duration
        self.timer_start_time = time.time()
        self.timer_in_progress = True
        logger.info(f"Timer started for {duration} seconds")

    def get_remaining_time(self):
        if not self.timer_in_progress:
            return 0
        elapsed_time = time.time() - self.timer_start_time
        remaining_time = self.countdown_duration - elapsed_time
        if remaining_time <= 0:
            self.timer_in_progress = False
            return 0
        return remaining_time

    def stop_timer(self):
        self.timer_in_progress = False
        self.timer_start_time = None
        logger.info("Timer stopped")

    async def _clear_previous_battle(self):
        with current_app.app_context():
            ArenaChatMessage.query.delete()
            TacticsChatMessage.query.delete()
            db.session.commit()

    async def get_registered_character_data(self):
        logger.info("Fetching registered character data")
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

    async def evaluate_and_comment_round(self, character_data, arena):
        # Evaluate fighters' moves
        unread_messages = ArenaChatMessage.query.filter_by(arena_id=arena.id, read_status=0, sender='fighter').all()
        moves = [(msg.user_id, msg.content) for msg in unread_messages]
        for msg in unread_messages:
            msg.read_status = 1
        db.session.commit()

        referee_evaluation = await self.evaluate_moves(character_data, arena, moves)
        logger.info(f"Referee evaluation completed: {referee_evaluation}")

        commentary = await self.generate_commentary(character_data, arena, moves, referee_evaluation)
        logger.info("Commentary completed: ")

        general_chat_message = GeneralChatMessage(content=commentary, sender='commentator', user_id=None)
        db.session.add(general_chat_message)
        db.session.commit()

    async def wait_for_moves(self, arena_id, num_participants):
        logger.info("Waiting for moves from participants")
        while True:
            unread_count = ArenaChatMessage.query.filter_by(arena_id=arena_id, read_status=0, sender='fighter').count()
            logger.info(f">>>>> {unread_count} >= {num_participants}")
            if unread_count >= num_participants:
                break
            await asyncio.sleep(1)
        logger.info("All moves received")

    async def evaluate_moves(self, character_data, arena, moves):
        logger.info("Evaluating moves by referee")
        if self.referee_assistant is None:
            self.referee_assistant = GeminiAssistant('referee')
        evaluation_message = f"Evaluate the following moves in arena {arena.id}: {moves}"
        if not evaluation_message.strip():
            logger.error("Empty message for evaluation, skipping evaluation")
            return "Evaluation not provided"
        evaluation = await self.referee_assistant.send_message(evaluation_message)

        # Parse referee message
        parsed_grades = parse_referee(evaluation)
        
        for parsed_grade in parsed_grades:
            if parsed_grade["name"]:
                logger.info(f"Referee evaluation: {parsed_grade['name']} | Combat: {parsed_grade['combat']} | Damage: {parsed_grade['damage']}")
                self.message_to_Arena(f"--- Referee: {parsed_grade['name']} | Combat: {parsed_grade['combat']} | Damage: {parsed_grade['damage']} ---")
                # Update character combat and damage
                self.update_character_combat_and_damage(parsed_grade)

        evaluation_message = ArenaChatMessage(
            content=evaluation, sender='referee', user_id=None, arena_id=arena.id, read_status=0
        )
        db.session.add(evaluation_message)
        db.session.commit()

        return evaluation

    def update_character_combat_and_damage(self, parsed_grade):
        """Updates character Combat, Damage, and Life based on referee evaluation."""
        with current_app.app_context():
            character = Character.query.filter_by(name=parsed_grade['name']).first()
            logger.info(f"character: {character}")
            if character:
                character.combat = parsed_grade['combat'] if parsed_grade['combat'] is not None else character.combat
                character.damage = parsed_grade['damage'] if parsed_grade['damage'] is not None else character.damage
                
                # Reduce character life by the amount of damage
                if parsed_grade['damage'] is not None:
                    character.life = max(0, character.life - parsed_grade['damage'])
                
                logger.info(f"life: {character.life}, combat: {character.combat}, damage: {character.damage}")
                
                db.session.commit()

                logger.info(f"Character {character.name} updated: Combat: {character.combat}, Damage: {character.damage}, Life: {character.life}")

                # Check if the character's life has dropped to zero, removing them from the arena
                if character.life <= 0:
                    self.remove_character_from_arena(character)

    def update_character_health(self, evaluation):
        """Updates characters' health based on referee evaluation."""
        with current_app.app_context():
            for line in evaluation.splitlines():
                if "Character ID:" in line:
                    parts = line.split()
                    for part in parts:
                        if part.isdigit():
                            character_id = int(part)
                            break
                elif "Points:" in line:
                    points = int(line.split()[-1])
                    character = Character.query.get(character_id)
                    if character:
                        traits = json.loads(character.traits)
                        # Update health or other attribute
                        traits['health'] = max(0, traits.get('health', 100) - points)
                        character.traits = json.dumps(traits)
                        db.session.commit()

    async def generate_commentary(self, character_data, arena, moves, referee_evaluation):
        logger.info("Generating commentary for the round")
        commentary = f"Referee evaluated the round as follows: {referee_evaluation}\n"
        commentary += "Fighters made the following moves:\n"
        for user_id, move in moves:
            character = next((char for char in character_data if char['user_id'] == user_id), None)
            if character:
                commentary += f"{character['name']}: {move}\n"
        return commentary

    async def handle_post_battle_registration(self):
        with current_app.app_context():
            Registrar.query.delete()
            db.session.commit()

            pre_registrations = PreRegistrar.query.all()
            for pre_reg in pre_registrations:
                new_registration = Registrar(
                    user_id=pre_reg.user_id,
                    character_id=pre_reg.character_id,
                    arena_id=pre_reg.arena_id
                )
                db.session.add(new_registration)
            db.session.commit()

            PreRegistrar.query.delete()
            db.session.commit()

            logger.info("Registration table updated with data from pre-registration")
