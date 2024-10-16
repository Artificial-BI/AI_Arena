
# --- player_manager.py ---
import logging
import asyncio
from flask import current_app
from models import Character, Registrar, PreRegistrar, Arena 
#from chats_models import ReadStatus, ArenaChatMessage, TacticsChatMessage
from extensions import db
from assistant import Assistant
from datetime import datetime
from core_common import CoreCommon
from status_manager import StatusManager
from config import Config
from messaging_manager import MessageManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlayerManager:
    def __init__(self):
        self.step_number = 0
        self.step_tactic = 0
        self.start_step = 0
        self.sm = StatusManager()
        self.mm = MessageManager()
        self.ccom = CoreCommon()
        self.ReadState = False
        self.tcm = TacticsManager(self)
        self.flm = FighterManager(self)
        self.config = Config()
        self.battle_process = False
        self.arena_id = None
        self.battleStart = True
        self.once = {}
        
        self.user_status = False
        self.game_status = ""
        self.error_status = ""
        self.battle_status = ""
        self.timer_status = 0
        self.arena_status = "" 

    def initial(self, user_id, response):
        self.game_status = ""
        self.error_status = ""
        self.battle_status = ""
        self.timer_status = 0
        self.arena_status = ""  

    async def initial_mess(self, user_id):
        res_stat = await self.mm.create_channel_message(f'stat_{user_id}')
        res_chat = await self.mm.create_channel_message(f'chat_{user_id}')

        logger.info(f"User: {user_id} | stat: {res_stat} | chat: {res_chat} ")
        logger.info(f"channels: {await self.mm.get_name_channels()}")

        
    # chat_40719177622694151  
    # chat_4789789882024500043  
    
      
    async def set_statuses_subscribe(self): 
        subscribe_stat = {  'game':self.game_callback,
                            'error':self.error_callback,
                            'battle':self.battle_callback,
                            'timer':self.timer_callback,
                            'battle_process':self.battle_process_callback
                         }
        logger.info(f"---- PLM SUBSCRIBE ----")
        await self.sm.subscribe_statuses(subscribe_stat)
        
    def timer_callback(self, response):
        self.timer_status = response   
        
    def game_callback(self, response):
        self.game_status = response
        
    def error_callback(self, response):
        self.error_status = response

    async def battle_callback(self, response):
        self.battle_status= response    
    
    async def arena_callback(self, response):
        self.arena_status = response   
        
    async def battle_process_callback(self, response):
        self.battle_process = response     
        print('battle_process:', self.battle_process)

    async def get_statuses(self,user_id):
        self.user_status = await self.sm.get_status(f'stat_{user_id}')
        self.timer_status = await self.sm.get_status('timer')
        self.game_status = await self.sm.get_status('game')
        self.error_status = await self.sm.get_status('error')
        self.battle_status = await self.sm.get_status('battle')
        self.arena_status =  await self.sm.get_status('arena')
        self.battle_process = await self.sm.get_status('battle_process')

    def add_PreRegistrar(self, user_id, character_id):
        # Проверяем, есть ли запись в PreRegistrar
        pre_reg_exists = PreRegistrar.query.filter_by(user_id=user_id, character_id=character_id, arena_id=1).first()
        if not pre_reg_exists:
            pre_reg = PreRegistrar(user_id=user_id, character_id=character_id, arena_id=1)
            db.session.add(pre_reg)
            logger.info(f"Registered in PreRegistrar: {user_id} with character {character_id}")
        else:
            logger.info(f"Character {character_id} is already registered in PreRegistrar for user {user_id}")

    def get_cur_character(self, user_id):
        # Оставляем логику работы с персонажами напрямую, так как они не связаны с буфером сообщений
        registration = Registrar.query.filter_by(user_id=user_id).first()
        if not registration:
            logger.error(f"Character for user {user_id} not found")
            return None

        character = Character.query.filter_by(character_id=registration.character_id).first()
        if not character:
            logger.error(f"Character with ID {registration.character_id} not found")
        return character

    async def battle_trigger(self, user_id):
        await self.get_statuses(user_id)
        
        if not self.once.get(user_id):
            await self.initial_mess(user_id)
            #await self.battle_start(user_id)
            self.once[user_id] = True 
   

    async def battle_start(self, user_id):

        logger.info(f'STAT PLM:{self.game_status}, error:{self.error_status}, battle:{self.battle_status}, timer:{self.timer_status}, arena:{self.arena_status}')

        if self.battle_process:
            await self.process_battle(user_id)

    async def process_battle(self, user_id):
        #cur_arena = await self.ccom.get_arena()  # получение арены
        arena = await self.sm.get_status('arena')
        ar = await self.sm.get_status('arena')
        
        print('ARENA:',ar)
        
        reg_character_list = await self.ccom.get_registered_character_data()  # получение списка зарегистрированных персонажей

        self.start_step+=1
        cur_character = self.get_cur_character(user_id)
        
        opponent_character_list = []
        for character in reg_character_list:
            if character['character_id'] != cur_character.character_id:  # Используем character_id для сравнения
                str_character = self.ccom.character_toStr(character)
                opponent_character_list.append(str_character)  # Добавляем оппонентов как строки

        register_users = Registrar.query.all()
        user_ids = [user.user_id for user in register_users]

        if self.game_status == 'stop' or self.game_status == 'error':
            self.battle_status = False
            logger.warning(f"User {user_id} Stop!!!! game_status: {self.game_status} | error: {self.error_status}")
        elif self.battle_status == 'stop' or self.battle_status == 'error':
            self.battle_status = False
            logger.warning(f"User {user_id} Stop!!!! battle_status: {self.battle_status} | error: {self.error_status}")
        else:        
            if self.battle_status:   
                self.tactic_step = True
                while self.tactic_step:
                    opponent_moves_list = []
                    # получаем ходы зарегистрированный пользователей (кроме своего)
                    for user_reg in user_ids: 
                        if user_reg != user_id:
                            opponent_mov = await self.mm.get_message_chatArena(sender='fighter', arena_id=None, user_id=user_reg)
                            opponent_moves_list.append(opponent_mov)
                    # получаем оценки рефери
                    referee_rating_list = await self.mm.get_message_chatArena(sender='referee', arena_id=None, user_id=self.config.SYS_ID)
                    
                    if await self.sm.get_status(f'stat_{user_id}') == False:
                        recomendation = await self.tcm.generate_tactics(user_id, arena, cur_character, opponent_character_list, opponent_moves_list, referee_rating_list)
                        await self.mm.message_to_Tactics(f'For: {cur_character.name} - {recomendation}', sender="tactician", user_id=user_id)
                        await self.sm.set_status(f'stat_{user_id}', True)
                    await asyncio.sleep(1)

                    if await self.sm.get_status(f'stat_{user_id}'):
                        fighter_step = await self.flm.generate_fighter(user_id, arena, cur_character, opponent_moves_list, referee_rating_list)
                        if fighter_step:
                            message = f"fighter: {cur_character.name}\n"
                            message += f"step: {fighter_step}\n"
                            await self.mm.message_to_Arena(message, "fighter", arena.id, user_id, cur_character.name)
                            await self.sm.set_status(f'stat_{user_id}', False)
                            self.step_number +=1
                            self.tactic_step = False
                    await asyncio.sleep(1)        
            # регистрируемся на новую битву        
            self.add_PreRegistrar(user_id, cur_character.character_id)
            
class TacticsManager:
    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.ccom = CoreCommon()
        self.sm = StatusManager()
        self.mm = MessageManager()
    #================= TACTIC =========================
        
    async def generate_tactics(self, user_id, cur_arena, cur_character, opponent_character_list, opponent_moves_list, referee_rating_list):

        cur_arena_txt = cur_arena.to_str() 
        cur_character_txt = cur_character.to_str() 

        prompt = f"Arena: {cur_arena_txt}\n"
        prompt += f"Our fighter: {cur_character_txt}\n"
        for opponent in opponent_character_list:
            prompt += f"Opponent: {opponent}\n"
        for opponent_move in opponent_moves_list:
            prompt += f"opponent move: {opponent_move}\n"
        for referee_rating in referee_rating_list:
            prompt += f"referee rating: {referee_rating}\n"
        prompt += "Generate tactical recommendations for the character's next move."

        try:
            assistant = Assistant("tactician")
            response = await assistant.send_message(prompt,'gemini')
            return response 
        except Exception as e:
            logger.error(f"Sending message tectic for {user_id}: {e}")
            self.battle_status = False
        return None 

class FighterManager:
    
    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.ccom = CoreCommon()
        self.sm = StatusManager()
        self.mm = MessageManager()

    #================== FIGHTER ===================== 

    async def generate_fighter(self, user_id, cur_arena, cur_character, opponent_moves_list, referee_rating_list):
        
        tactical_recommendation = await self.mm.get_message_chatTactics(sender='tactic', user_id=user_id)
        user_wishes = await self.mm.get_message_chatTactics(sender='user', user_id=user_id)
        logger.info(f'-- generate_fighter >>> {user_wishes}')
        cur_arena_txt = cur_arena.to_str() 
        cur_character_txt =cur_character.to_str() 
        prompt = f"Arena: {cur_arena_txt}\n\n"
        prompt += f"cur character: {cur_character_txt}\n\n"
        prompt += f"Tactic recommendations: {tactical_recommendation}\n\n"
        prompt += f"user wishes: {user_wishes}\n\n"

        for opponent_move in opponent_moves_list:
            prompt += f"opponent move: {opponent_move}\n\n"
        for referee_rating in referee_rating_list:
            prompt += f"referee rating: {referee_rating}\n\n"
        prompt += "Generate the character's next move based on the information above."

        try:
            assistant = Assistant("fighter")
            response = await assistant.send_message(prompt,'gemini')
            if response:
                return response

        except Exception as e:
            logger.error(f"Sending sending message fighter for {user_id}: {e}")
            self.battle_status = False

        return None





