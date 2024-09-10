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
        #self.mm = MessageManager()

    async def start_waiting_for_players(self):
        count_sec = 0
        logger.info(" ---------- START WAITING PLAYERS -------------- ")
        while True:
            registered_players = Registrar.query.count()  # Это часть базы aiarena.db, ее оставляем
            if registered_players > 0:
                if registered_players >= self.config.PLAYER_COUNT:
                    break  # Достаточно игроков, выходим из ожидания
                self.sm.set_state('game', 'waiting', self.ccom.newTM())
                self.sm.set_state('timer', f'{count_sec}', self.ccom.newTM())
                count_sec += 1
            await asyncio.sleep(1)
                
        self.sm.set_state('timer', 'stop', self.ccom.newTM())

    async def generate_arena(self):
        self.sm.set_state('arena', 'start', self.ccom.newTM())
        if self.config.ARENA_MODE == 'random':
            self.sm.set_state('game', 'Arena random', self.ccom.newTM())
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
        start_count = count_runs(filename="run_count.txt")
        logger.info(f" ---------- NEW START GAME {start_count} -------------- ")
        
        # if start_count > 1:
        #     return
        
        self.sm.set_state('game', 'stop', self.ccom.newTM())
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

            # Очищаем предыдущие данные битвы через буфер сообщений
            await self.ccom.clear_chats()

            arena =  await self.ccom.get_arena()
            characters_data = await self.ccom.get_registered_character_data()

            message = "'message':'--- START GAME ---'\n"
            message = "'characters':\n"
            for character in characters_data:
                message += f"'User':'{character['user_id']}  "
                message += f"'Fighter':'{character['name']}'\n"

            logger.info(f"---* {message} *---")

            await self.ccom.message_to_Arena(message, "system", arena.id, self.config.SYS_ID, 'system')

            sum_fighters_moves_list = []
            for round_number in range(self.config.COUNT_ROUND):
                game_status = self.sm.get_state('game')
                if  game_status == 'stop':
                    logger.info(f"-----------   Game stop!:::::: {self.sm.get_state('error')}")
                    break
                if not self.battle_in_progress:
                    break
                self.sm.set_state('battle', f'Round {round_number + 1}', self.ccom.newTM())
                message = f"Round N: {round_number + 1}\n\n"
                logger.info(f"--- {message} ---")
                await self.ccom.message_to_Arena(message, "system", arena.id, self.config.SYS_ID, 'system')

                # Ждем шагов бойцов
                await asyncio.sleep(self.config.WAITING_STEPS)
                
                # Получаем ходы бойцов через буфер сообщений
                fighters_moves_list = await self.get_list_messages('fighter', arena)
                sum_fighters_moves_list.append(fighters_moves_list)
                await self.referee_evaluation_fighters(arena, characters_data, fighters_moves_list)
                
            if self.battle_in_progress:
                self.sm.set_state('battle', 'finished', self.ccom.newTM())
                self.sm.set_state('game', 'game over', self.ccom.newTM())
                logger.info("--- Battle finished ---")
                await self.ccom.message_to_Arena("--- Battle finished ---", "system", arena.id, self.config.SYS_ID, 'system')
                
                #await self.generate_commentary(characters_data, arena, sum_fighters_moves_list)
            else:
                logger.info("--- Battle stopped ---")
            
            

        except Exception as e:
            self.sm.set_state('game', 'stop', self.ccom.newTM())
            self.sm.set_state('battle', 'error', self.ccom.newTM())
            logger.error(f"Error in battle: {e}", exc_info=True)

    async def referee_evaluation_fighters(self, arena, characters_data, list_moves):

        prompt = f"Arena: {arena.to_str()}\n\n"
        prompt += f"Fighter character:\n"
        for character in characters_data:
            character_txt = self.ccom.character_toStr(character)
            prompt += f"{character_txt}\n\n"

        prompt += f"Fighter: {list_moves}\n\n"

        response = None
        try:
            assistant = Assistant("referee")
            response = await assistant.send_message(prompt,'auto')
        except Exception as e:
            logger.error(f"Error sending message sys: {e}")
            self.battle_in_progress = False
        
        if response:
            logger.info(f"--- fighters old step: {len(response)} ---")
            await self.ccom.message_to_Arena(response, "referee", arena.id, self.config.SYS_ID, 'system')


    async def generate_commentary(self, character_data, arena, list_moves):

        prompt = f"Arena: {arena.to_str()}\n\n"
        prompt += f"Fighter character:\n"
        for character in character_data:
            character_txt = self.ccom.character_toStr(character)
            prompt += f"{character_txt}\n\n"

        prompt += f"Fighters: {list_moves}\n\n"

        try:
            assistant = Assistant("commentator")
            response = await assistant.send_message(prompt,'auto')
        except Exception as e:
            logger.error(f"Error sending message sys: {e}")

        await self.ccom.message_to_GeneralChat(response, "commentator", self.config.SYS_ID)    

    async def get_list_messages(self, name, arena):
        
        unread_messages = await self.ccom.get_message_chatArena(name, arena.id, user_id=self.config.SYS_ID)
        list_moves = [(msg["user_id"], msg["content"]) for msg in unread_messages]

        return list_moves
