import asyncio
import logging
import random
from flask import current_app
from models import Arena, Character, Registrar, db
from assistant import Assistant
from config import Config
from core_common import CoreCommon
from arena_manager import ArenaManager
from multiproc import StatusManager
from utils import count_runs
#from message_buffer import MessageManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BattleManager:
    def __init__(self, loop=None):
        self.glob_step = 0
        self.ccom = CoreCommon()
        self.referee_assistant = None
        self.commentator_assistant = None
        self.arena_manager = ArenaManager()
        self.battle_count = 0
        self.round_count = 0
        self.battle_in_progress = False
        self.loop = loop
        self.config = Config()
        self.sm = StatusManager()
    
    def clear_registrar(self):
        self.sm.set_state('characters', False, self.ccom.newTM())
        db.session.query(Registrar).delete()
        db.session.commit()

    def clear_state(self):
        self.sm.set_state('characters', None, self.ccom.newTM())
        self.sm.set_state('arena', None, self.ccom.newTM())
        self.sm.set_state('timer', None, self.ccom.newTM())
        self.sm.set_state('battle', None, self.ccom.newTM())
    
    def clear_chats(self):
        pass
        
    async def waiting(self, set_count):
        count = 0
        res = False
        while True: 
            if count >= set_count:
                res = True
                break
            self.sm.set_state('timer', f'{count}', self.ccom.newTM())
            count+=1    
            await asyncio.sleep(1) 
        self.sm.set_state('timer', 'stop', self.ccom.newTM())
        return res    
        
    async def start_waiting_for_players(self):
        count_sec = 0
        res = False
        logger.info(f" ---------- START WAITING PLAYERS {self.glob_step}-------------- ")
        while True:
            registered_players = Registrar.query.count()  # Это часть базы aiarena.db, ее оставляем
            if registered_players > 0:
                if registered_players >= self.config.PLAYER_COUNT:
                    self.sm.set_state('characters', True, self.ccom.newTM())
                    res = True
                    break  # Достаточно игроков, выходим из ожидания
                self.sm.set_state('timer', f'{count_sec}', self.ccom.newTM())
                count_sec += 1
            await asyncio.sleep(1)
                
        self.sm.set_state('timer', 'stop', self.ccom.newTM())
        return res

    async def generate_arena(self):
        self.sm.set_state('arena', 'start', self.ccom.newTM())
        if self.config.ARENA_MODE == 'random':
            logger.info(" ---------- ARENA RANDOM -------------- ") 
            self.sm.set_state('arena', 'random', self.ccom.newTM())
            arena_cnt = Arena.query.count()  # Работа с таблицами aiarena.db, это оставляем
            if arena_cnt > 0:
                random_offset = random.randint(0, arena_cnt - 1)
                arena = Arena.query.offset(random_offset).first()
            else:
                arena = await self.arena_manager.generate_arena()
                db.session.add(arena)
                db.session.commit()
        else:
            self.sm.set_state('arena', 'generated', self.ccom.newTM())
            logger.info(" ---------- ARENA GENERATE -------------- ")
            arena = await self.arena_manager.generate_arena()
            db.session.add(arena)
            db.session.commit()

    async def start_game(self):
        start_count = count_runs(filename="core_count.txt")
        self.clear_state()
        logger.info(f" ---------- NEW START GAME {start_count} -------------- ")
        self.game_is_on = True
        #set_waiting = 20
        self.sm.set_state('game', 'start', self.ccom.newTM())
        while self.game_is_on:
            game_state = self.sm.get_state('game')
            if game_state == 'stop' or game_state == 'error':
                self.game_is_on = False
 
            start_battle = await self.waiting(self.config.NEW_BATTLE_WAIT)
            if start_battle:
                self.clear_state()
                self.clear_chats()
                players_waiting = await self.start_waiting_for_players()
                if players_waiting:
                    await self.generate_arena()
                    await self.start_battle()

    async def start_battle(self):
        logger.info(f"--- Battle {self.battle_count + 1} started ---")
        try:
            self.battle_in_progress = True
            self.battle_count += 1
            self.sm.set_state('battle', 'start', self.ccom.newTM())
            # Очищаем предыдущие данные битвы через буфер сообщений
            await self.ccom.clear_chats()

            arena =  await self.ccom.get_arena()
            characters_data = await self.ccom.get_registered_character_data()

            message = "--- START BATTLE ---\n"
            message = "characters:\n"
            for character in characters_data:
                message += f"User: {character['user_id']}  "
                message += f"Fighter: {character['name']}\n"

            logger.info(f"{message}")

            await self.ccom.message_to_Arena(message, "system", arena.id, self.config.SYS_ID, 'system')

            sum_fighters_moves_list = []
            for round_number in range(self.config.COUNT_ROUND): #к-во раундов битвы
                
                battle_state = self.sm.get_state('battle')
                if  battle_state == 'stop' or battle_state == 'error':
                    logger.info(f"-----------  Battle stop!:::::: {self.sm.get_state('error')}")
                    break
                
                self.sm.set_state('battle', f'Round {round_number + 1}', self.ccom.newTM())
                message = f"Round N: {round_number + 1}\n\n"
                logger.info(f"--- {message} ---")
                await self.ccom.message_to_Arena(message, "system", arena.id, self.config.SYS_ID, 'system')

                for fighterSteps in range(10):
                    # Ждем шагов бойцов
                    await asyncio.sleep(self.config.WAITING_STEPS)
                    # Получаем ходы бойцов через буфер сообщений
                    unread_messages = await self.ccom.get_message_chatArena('fighter', None, user_id=None, mark_user_id=543654)
                    fighters_moves_list = [(msg["user_id"], msg["content"]) for msg in unread_messages]
                    
                    logger.info(f"Get fighter step: {fighterSteps} count: {len(fighters_moves_list)} ")
                    
                    if len(fighters_moves_list) > 1:
                        break    
                
                
                # рефери дает оценку
                sum_fighters_moves_list.append(fighters_moves_list)
                grade =  await self.referee_evaluation_fighters(arena, characters_data, fighters_moves_list)
                await self.ccom.message_to_Arena(grade, "referee", arena.id, self.config.SYS_ID, 'system')

                logger.info(f"referee grade count: {len(grade)} ")

                # комментарии раунда
                comment = await self.generate_commentary(characters_data, arena, sum_fighters_moves_list)
                await self.ccom.message_to_GeneralChat(comment, "commentator", self.config.SYS_ID)  
                
                logger.info(f"commentary count: {len(comment)} ")

            # завершение битвы 
            self.sm.set_state('battle', 'finish', self.ccom.newTM())
            await self.ccom.message_to_Arena("--- Battle finished ---", "system", arena.id, self.config.SYS_ID, 'system')
            self.clear_registrar()
            await asyncio.sleep(10)
            logger.info(f"--- Battle finished. user registrar: ({Registrar.query.count()}) ---")

        except Exception as e:
            self.sm.set_state('game', 'error', self.ccom.newTM())
            self.sm.set_state('battle', 'error', self.ccom.newTM())
            logger.error(f"Error in battle: {e}", exc_info=True)

    async def referee_evaluation_fighters(self, arena, characters_data, list_moves):

        prompt = f"Arena: {arena.to_str()}\n\n"
        prompt += f"Fighter character:\n"
        for character in characters_data:
            character_txt = self.ccom.character_toStr(character)
            prompt += f"{character_txt}\n\n"

        prompt += f"Fighter: {list_moves}\n\n"

        try:
            assistant = Assistant("referee")
            response = await assistant.send_message(prompt,'auto')
            return response
        except Exception as e:
            logger.error(f"Error sending message sys: {e}")
            self.sm.set_state('battle', 'error', self.ccom.newTM())
            self.sm.set_state('error', f'core referee: {e}', self.ccom.newTM())
        return None


    async def generate_commentary(self, character_data, arena, list_moves):

        prompt = f"Arena: {arena.to_str()}\n\n"
        prompt += f"Fighter character:\n"
        for character in character_data:
            character_txt = self.ccom.character_toStr(character)
            prompt += f"{character_txt}\n\n"

        prompt += f"Fighters: {list_moves}\n\n"

        try:
            assistant = Assistant("commentator")
            response = await assistant.send_message(prompt,'gemini')
            return response
        except Exception as e:
            logger.error(f"Error sending message sys: {e}")
            self.sm.set_state('battle', 'error', self.ccom.newTM())
            self.sm.set_state('error', f'core commentator: {e}', self.ccom.newTM())
        return None    
            
          

