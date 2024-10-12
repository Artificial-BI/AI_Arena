import asyncio
import logging
import random
from flask import current_app
from models import Arena, Character, PreRegistrar, Registrar, db
from assistant import Assistant
from config import Config
from core_common import CoreCommon
from arena_manager import ArenaManager
from status_manager import StatusManager
from utils import count_runs
from messaging_manager import MessageManager
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
        #self.battle_in_progress = False
        self.loop = loop
        self.config = Config()
        self.sm = StatusManager()
        self.mm = MessageManager()
        self.game_status = ''
        self.error_status = ''
        self.battle_status = ''
        # 'tactic_chat', 'arena_chat', 'general_chat'

    async def clear_registrar(self):
        await self.sm.set_status('characters', False)
        db.session.query(Registrar).delete()
        db.session.commit()

    async def clear_state(self):
        await self.sm.set_status('characters', False)
        await self.sm.set_status('arena', 0)
        await self.sm.set_status('timer', 0)
        await self.sm.set_status('battle', 'none')
        await self.sm.set_status('battle_process', False)
    
    async def clear_chats(self):
        print('clear_chats !!!')

    async def game_callback(self, response):
        self.game_status = self.sm.stat_extraction(response)
        print('STAT GAME:',self.game_status)
        
    async def error_callback(self, response):
        self.error_status = self.sm.stat_extraction(response)
        print('STAT ERROR:',self.error_status)

    async def battle_callback(self, response):
        self.battle_status = self.sm.stat_extraction(response)
        print('STAT BATTLE:',self.battle_status)
    
    # async def create_subscribe(self):
    #     await self.mm.message_subscribes()
        
    #     subscribe_stat = {'game':self.game_callback,
    #                       'error':self.error_callback,
    #                       'battle':self.battle_callback}
        
    #     await self.sm.subscribe_statuses(subscribe_stat)
    
    
    def preReg_to_Reg(self):
        if PreRegistrar.query.count() > 0:
            pre_reg_users = PreRegistrar.query.filter_by(arena_id=1).all()
            for pre_reg_user in pre_reg_users:
                reg = Registrar(
                    user_id=pre_reg_user.user_id,
                    character_id=pre_reg_user.character_id,
                    arena_id=pre_reg_user.arena_id,
                    registration_date=pre_reg_user.registration_date
                )
                db.session.add(reg)
            db.session.commit()
            db.session.query(PreRegistrar).delete()
            db.session.commit()
            print("Пользователи успешно перенесены и таблица PreRegistrar очищена.")
        else:
            print("Нет пользователей для переноса.")
        
    async def waiting(self, set_count):
        count = 0
        res = False
        while True: 
            if count >= set_count:
                res = True
                break
            await self.sm.set_status('timer', f'{count}')
            count+=1    
            await asyncio.sleep(1) 
        await self.sm.set_status('timer', 'stop')
        return res    
        
    async def start_waiting_for_players(self, stop_event):
        count_sec = 0
        res = False
        logger.info(f" ---------- START WAITING PLAYERS {self.glob_step}-------------- ")
        waiting_cicle = True
        while waiting_cicle:
            if stop_event.is_set():
                waiting_cicle = False
            registered_players = Registrar.query.count() 
            if registered_players > 0:
                if registered_players >= self.config.PLAYER_COUNT:
                    await self.sm.set_status('characters', True)
                    res = True
                    waiting_cicle = False  # Достаточно игроков, выходим из ожидания
                await self.sm.set_status('timer', f'{count_sec}')
                #logger.info(f'timer: {count_sec}')
                logger.info(f"timer: {await self.sm.get_status('timer')}")
                count_sec += 1
            await asyncio.sleep(1)
                
        await self.sm.set_status('timer', 'stop')
        return res

    async def generate_arena(self):
        
        if self.config.ARENA_MODE == 'random':
            logger.info(" ---------- ARENA RANDOM -------------- ") 
            #await self.sm.set_status('arena', 'random')
            arena_cnt = Arena.query.count()  # Работа с таблицами aiarena.db, это оставляем
            if arena_cnt > 0:
                random_offset = random.randint(0, arena_cnt - 1)
                arena = Arena.query.offset(random_offset).first()
            else:
                arena = await self.arena_manager.generate_arena()
                db.session.add(arena)
                db.session.commit()
        else:
            #await self.sm.set_status('arena', 'generated')
            logger.info(" ---------- ARENA GENERATE -------------- ")
            arena = await self.arena_manager.generate_arena()
            db.session.add(arena)
            db.session.commit()
        await self.sm.set_status('arena', arena)    

    async def start_game(self, stop_event):
        start_count = count_runs(filename="core_count.txt")
        logger.info(f" ---------- NEW START GAME {start_count} {stop_event.is_set()} -------------- ")
                
        await self.sm.create_status_channels()
        await self.sm.init_statuses()
        await self.mm.create_message_channels()

        game_cicle = 0

        await self.sm.set_status('game', 'start')
        stats = await self.sm.get_all_statuses()
      
        for st in stats:
            logger.info(f"{st['name']}= {st['status']}")
    
        while not stop_event.is_set():
            if self.game_status == 'stop' or self.game_status == 'error':
                self.stop_event.set()
            logger.info(f'--- NEW GAME CICLE {game_cicle} ---')
            start_battle = await self.waiting(self.config.NEW_BATTLE_WAIT)
            if start_battle:
                await self.clear_state()
                # переносим зарегистрированных пользователей из предварительной регистрации в зарегистрированных
                self.preReg_to_Reg() 
                players_waiting = await self.start_waiting_for_players(stop_event)
                if players_waiting:
                    await self.generate_arena()
                    #await self.start_battle()
            game_cicle+=1    



     
# 'tactic_chat', 'arena_chat', 'general_chat'
    async def start_battle(self):
        
        #_arena = await self.sm.get_status('arena')
        
        # logger.info(f'START ARENA: {type(_arena)}, {_arena}')
        # logger.info(f'ARENA: {_arena.id}, {_arena.image_url}')
        
        logger.info(f"--- Battle {self.battle_count + 1} started ---")
        try:
            self.battle_count += 1
            await self.sm.set_status('battle', 'start')
            await self.sm.set_status('battle_process', True)
            # Очищаем предыдущие данные битвы через буфер сообщений
            await self.clear_chats()

            #arena =  await self.ccom.get_arena()
            arena = await self.sm.get_status('arena')
            characters_data = await self.ccom.get_registered_character_data()

            message = "--- START BATTLE ---\n"
            message = "characters:\n"
            fnum=0
            for character in characters_data:
                message += f"User: {character['user_id']}  "
                message += f"Fighter {fnum}: {character['name']}\n"
                fnum +=1     
            logger.info(f"{message}")

            await self.mm.message_to_Arena(message, "system", arena.id, self.config.SYS_ID, 'system')
            
            sum_fighters_moves_list = []
            for round_number in range(self.config.COUNT_ROUND): #к-во раундов битвы
                if  self.battle_status == 'stop' or self.battle_status == 'error':
                    logger.info(f"-----------  Battle stop!:::::: {self.error_status}")
                    break
                
                await self.sm.set_status('battle', f'Round {round_number + 1}')
                message = f"Round N: {round_number + 1}\n\n"
                logger.info(f"--- {message} ---")
                await self.mm.message_to_Arena(message, "system", arena.id, self.config.SYS_ID, 'system')

                for fighterSteps in range(10):
                    # Ждем шагов бойцов
                    await asyncio.sleep(self.config.WAITING_STEPS)
                    # Получаем ходы бойцов через буфер сообщений
                    unread_messages = await self.mm.get_all_message_chatArena('fighter', arena.id, None)
                    fighters_moves_list = unread_messages #[(msg["user_id"], msg["message"]) for msg in unread_messages]
                    
                    logger.info(f"Get fighter step: {fighterSteps} count: {len(fighters_moves_list)} ")
                    
                    if len(fighters_moves_list) > 1:
                        break    
                
                
                # рефери дает оценку
                sum_fighters_moves_list.append(fighters_moves_list)
                grade =  await self.referee_evaluation_fighters(arena, characters_data, fighters_moves_list)
                await self.mm.message_to_Arena(grade, "referee", arena.id, self.config.SYS_ID, 'system')

                logger.info(f"referee grade count: {len(grade)} ")

                # комментарии раунда
                comment = await self.generate_commentary(characters_data, arena, sum_fighters_moves_list)
                await self.mm.message_to_GeneralChat(comment, "commentator", self.config.SYS_ID)  
                
                logger.info(f"commentary count: {len(comment)} ")

            # завершение битвы 
            await self.sm.set_status('battle', 'finish')
            await self.mm.message_to_Arena("--- Battle finished ---", "system", arena.id, self.config.SYS_ID, 'system')
            await self.sm.set_status('battle_process', False)
            # очищаем таблицу регистрации
            await self.clear_registrar() 
            await asyncio.sleep(10)
            logger.info(f"--- Battle finished. user registrar: ({Registrar.query.count()}) ---")

        except Exception as e:
            await self.sm.set_status('battle_process', False)
            await self.sm.set_status('game', 'error')
            await self.sm.set_status('battle', 'error')
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
            await self.sm.set_status('battle', 'error')
            await self.sm.set_status('error', f'core referee: {e}')
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
            await self.sm.set_status('battle', 'error')
            await self.sm.set_status('error', f'core commentator: {e}')
        return None    
            
          

