import asyncio
import logging

from flask import current_app
from models import (Arena, ArenaChatMessage, Character, GeneralChatMessage, Registrar, TacticsChatMessage, db)
from gemini import GeminiAssistant

from tactics_manager import FighterManager, TacticsManager
from utils import parse_referee
import random
from config import Config
from core_common import CoreCommon
from arena_manager import ArenaManager
from multiproc import StatusManager
from message_buffer import MessageManager
# --- core.py ---

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BattleManager:
    def __init__(self, loop=None):

        self.ccom = CoreCommon()
        self.referee_assistant = None
        self.commentator_assistant = None
        self.arena_manager = ArenaManager()
        self.battle_count = 0
        self.round_count = 0
        self.timer_in_progress = False
        self.battle_in_progress = False
        self.timer_start_time = None
        self.countdown_duration = 30
        self.moves_count = {}
        self.loop = loop
        self.count_round = 3
        self.count_steps = 4 
        self.user_expectation = 2
        self.config = Config()
        self.sm = StatusManager()
        #self.mm = MessageManager()
        

    async def start_waiting_for_players(self):
        count_sec = 0
        logger.info(" ---------- START WAITING PLAYERS -------------- ")
        while True:
            registered_players = Registrar.query.count()
            if registered_players >= self.config.PLAYER_COUNT:
                break  # Достаточно игроков, выходим из ожидания
            self.sm.set_state('game', 'waiting', self.ccom.newTM())
            self.sm.set_state('timer', f'{count_sec}', self.ccom.newTM())
            await asyncio.sleep(1)
            count_sec += 1
        self.sm.set_state('timer', 'stop', self.ccom.newTM())

    async def generate_arena(self):
        self.sm.set_state('arena', 'start', self.ccom.newTM())
        if self.config.ARENA_MODE == 'random':
            self.sm.set_state('game', 'Arena random', self.ccom.newTM())
            logger.info(" ---------- ARENA RANDOM -------------- ") 
            self.sm.set_state('arena', 'random', self.ccom.newTM())
            arena_cnt = Arena.query.count()
            if arena_cnt > 0:
                random_offset = random.randint(0, arena_cnt - 1)
                arena = Arena.query.offset(random_offset).first()
            else:
                arena = await self.arena_manager.generate_arena()
                db.session.add(arena)
                db.session.commit()
        else:
            self.sm.set_state('arena', 'generated', self.ccom.newTM())
            _start = self.ccom.newTM()
            self.sm.set_state('timer', f'{0}', self.ccom.newTM())
            logger.info(" ---------- ARENA GENERATE -------------- ")
            arena = await self.arena_manager.generate_arena()
            _end = self.ccom.newTM()
            self.sm.set_state('timer', f'{_end-_start}', self.ccom.newTM())
            db.session.add(arena)
            db.session.commit()

    async def start_game(self):
        await self.start_waiting_for_players()
        self.sm.set_state('game', 'players ok', self.ccom.newTM())
        await self.generate_arena()
        self.sm.set_state('game', 'arena ok', self.ccom.newTM())
       
        await self.start_battle()

    async def start_battle(self):
        logger.info(f"--- Battle {self.battle_count + 1} started ---")
        self.sm.set_state('game', 'battle', self.ccom.newTM())
        self.sm.set_state('battle', 'start', self.ccom.newTM())
        try:
            self.battle_in_progress = True
            self.battle_count += 1
            await self._clear_previous_battle()
            arena = self.ccom.get_arena()
            #cur_arena_txt = self.ccom.convert_dict_toStr(arena)
            characters_data = await self.ccom.get_registered_character_data()

            logger.info("-------------- STARTING MAIN BATTLE CYCLE ---------------")
            message = '--- START GAME ---\n\n'
            for character in characters_data:
                message += f'User: {character["user_id"]}\n\n'
                message += f'Fighter: {character["name"]}\n\n'

            self.ccom.message_to_Arena(message, "system", arena.id, self.config.SYS_ID, 'system')
            
            for round_number in range(self.config.COUNT_ROUND):
                if not self.battle_in_progress:
                    break
                logger.info(f"Round {round_number + 1} started")
                self.sm.set_state('battle', f'Round {round_number + 1}', self.ccom.newTM())
                message = f"Round N: {round_number + 1}\n\n"
                self.ccom.message_to_Arena(message, "system", arena.id, self.config.SYS_ID, 'system')
                
                #reg_character_list = self.ccom.get_registered_character_data()  # получение списка зарегистрированных персонажей

                await asyncio.sleep(self.config.WAITING_STEPS)
                
                fighters_moves_list = self.ccom.get_message_chatArena(sender='fighter',arena_id=arena.id)
                
                res = await self.referee_evaluation_fighters(arena, characters_data, fighters_moves_list)
                self.ccom.message_to_Arena(res, "referee", arena.id, self.config.SYS_ID, 'system')

            logger.info("Battle finished")
            self.sm.set_state('battle', 'finished', self.ccom.newTM())
            self.sm.set_state('game', 'over', self.ccom.newTM())

            self.ccom.message_to_Arena("--- Battle finished ---", "system", arena.id, self.config.SYS_ID, 'system')

        except Exception as e:
            self.sm.set_state('game', 'stop', self.ccom.newTM())
            self.sm.set_state('battle', 'error', self.ccom.newTM())
            logger.error(f"Error in battle: {e}", exc_info=True)

    async def referee_evaluation_fighters(self, arena, characters_data, fighters_moves_list):
        self.round_count += 1

        prompt = f"Arena: {arena.to_str}\n\n"
        for character in characters_data:
            character_txt = self.ccom.convert_dict_toStr(character)
            prompt += f"Fighter: {character_txt}\n\n"
            
        for fighter_step in fighters_moves_list:  
            fighter_step_txt = self.ccom.convert_dict_toStr(fighter_step)
            prompt += f"fighter step: {fighter_step_txt}\n\n"
        
        response = None
        try:
            assistant = GeminiAssistant("referee")
            response = await assistant.send_message(prompt)
        except Exception as e:
            logger.error(f"Error sending message sys: {e}")
        
        return response
        
        
        
        
        


        #await self.evaluate_and_comment_round(character_data, arena)
        
        
        
        
    async def _clear_previous_battle(self):
        with current_app.app_context():
            ArenaChatMessage.query.delete()
            TacticsChatMessage.query.delete()
            db.session.commit()


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
                self.ccom.message_to_Arena(f"--- Referee: {parsed_grade['name']} | Combat: {parsed_grade['combat']} | Damage: {parsed_grade['damage']} ---", _sender='referee', _name='referee', _arena_id=arena.id)
                # Update character combat and damage
                self.update_character_combat_and_damage(parsed_grade)
        self.ccom.message_to_Arena(evaluation, _sender='referee', _name='referee', _arena_id=arena.id)
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

    async def generate_commentary(self, character_data, arena, moves, referee_evaluation):
        logger.info("Generating commentary for the round")
        commentary = f"Referee evaluated the round as follows: {referee_evaluation}\n"
        commentary += "Fighters made the following moves:\n"
        for user_id, move in moves:
            character = next((char for char in character_data if char['user_id'] == user_id), None)
            if character:
                commentary += f"{character['name']}: {move}\n"
                
        self.assistant = GeminiAssistant('arena')       
  
        return commentary

   