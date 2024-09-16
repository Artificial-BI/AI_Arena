import logging
import asyncio
from flask import current_app
from models import Character, Registrar, Arena 
#from chats_models import ReadStatus, ArenaChatMessage, TacticsChatMessage
from extensions import db
from assistant import Assistant
from datetime import datetime
from core_common import CoreCommon
from multiproc import StatusManager
from config import Config
#from message_buffer import MessageManager
# --- tactic_manager.py ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlayerManager:
    def __init__(self, loop=None):
        self.step_number = 0
        self.step_tactic = 0
        self.start_step = 0
        self.stm = StatusManager()
        self.ccom = CoreCommon()
        self.ReadState = False
        self.tcm = TacticsManager(self)
        self.flm = FighterManager(self)
        self.config = Config()
        self.battle_state = False
        self.arena_id = None
        self.battleStart = True

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

    async def battle_start(self, user_id, battle_state):
        self.battle_state = (battle_state == 'start')
        if self.battle_state:
            await self.battle_process(user_id)
            self.battleStart = False

    async def battle_process(self, user_id):
        cur_arena = await self.ccom.get_arena()  # получение арены
        reg_character_list = await self.ccom.get_registered_character_data()  # получение списка зарегистрированных персонажей
        opponent_character_list = []
        #logger.info(f"User: {user_id} start battle num: {self.start_step}")
        self.start_step+=1
        cur_character = self.get_cur_character(user_id)

        for character in reg_character_list:
            if character['character_id'] != cur_character.character_id:  # Используем character_id для сравнения
                str_character = self.ccom.character_toStr(character)
                opponent_character_list.append(str_character)  # Добавляем оппонентов как строки

        register_users = Registrar.query.all()
        user_ids = [user.user_id for user in register_users]
        
        #logger.info(f"Registrar user count: {len(register_users)}")

        #while self.battle_state:
            
        game_state = self.stm.get_state('game')
        battle_state  = self.stm.get_state('game')
            
        if game_state == 'stop' or game_state == 'error' or battle_state == 'stop' or battle_state == 'error':
                self.battle_state = False
                logger.warning(f"User {user_id} Stop!!!! game_state: {game_state} | error: {self.stm.get_state('error')}")
                logger.warning(f"User {user_id} Stop!!!! battle_state: {battle_state} | error: {self.stm.get_state('error')}")
        else:        
            if self.battle_state:   
                
                self.tactic_step = True
                
                while self.tactic_step:
                
                    opponent_moves_list = []
                    # получаем ходы зарегистрированный пользователей (кроме своего)
                    for user_reg in user_ids: 
                        if user_reg != user_id:
                            opponent_mov = await self.ccom.get_message_chatArena(sender='fighter', arena_id=None, user_id=user_reg, mark_user_id=user_id)
                            opponent_moves_list.append(opponent_mov)
                    # получаем оценки рефери
                    referee_rating_list = await self.ccom.get_message_chatArena(sender='referee', arena_id=None, user_id=self.config.SYS_ID, mark_user_id=user_id)
                    
                    if self.stm.get_state(str(user_id)) == False:
                        recomendation = await self.tcm.generate_tactics(user_id, cur_arena, cur_character, opponent_character_list, opponent_moves_list, referee_rating_list)
                        await self.ccom.message_to_Tactics(f'For: {cur_character.name} - {recomendation}', sender="tactician", user_id=user_id)
                        self.stm.set_state(str(user_id), True, self.ccom.newTM())
                    await asyncio.sleep(1)
                    
                    read_state = self.stm.get_state(str(user_id))
                    logger.info(f'UID: {user_id} RS: {read_state}')

                    if self.stm.get_state(str(user_id)):
                        fighter_step = await self.flm.generate_fighter(user_id, cur_arena, cur_character, opponent_moves_list, referee_rating_list)
                        if fighter_step:
                            message = f"fighter: {cur_character.name}\n"
                            message += f"step: {fighter_step}\n"
                            await self.ccom.message_to_Arena(message, "fighter", cur_arena.id, user_id, cur_character.name)
                            self.stm.set_state(str(user_id), False, self.ccom.newTM())
                            self.step_number +=1
                            self.tactic_step = False
                    await asyncio.sleep(1)        

            
class TacticsManager:
    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.ccom = CoreCommon()
        self.stm = StatusManager()
    
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
            self.battle_state = False
        return None 

class FighterManager:
    
    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.ccom = CoreCommon()
        self.stm = StatusManager()

    #================== FIGHTER ===================== 

    async def generate_fighter(self, user_id, cur_arena, cur_character, opponent_moves_list, referee_rating_list):
        
        tactical_recommendation = await self.ccom.get_message_chatTactics(sender='tactic', user_id=user_id, mark_user_id=user_id)
        user_wishes = await self.ccom.get_message_chatTactics(sender='user', user_id=user_id, mark_user_id=user_id)

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
            self.battle_state = False

        return None





