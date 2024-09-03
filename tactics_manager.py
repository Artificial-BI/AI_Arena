import logging
import asyncio
from flask import current_app
from models import Character, TacticsChatMessage, Registrar, Arena, ArenaChatMessage
from extensions import db
from gemini import GeminiAssistant
from datetime import datetime
from core_common import CoreCommon
from multiproc import StatusManager
from message_buffer import MessageManager
# --- tactic_manager.py ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlayerManager:
    def __init__(self, loop=None):
        
        self.stm = StatusManager()
        self.ccom = CoreCommon()
        self.tcm = TacticsManager()
        self.flm = FighterManager()
        self.battle_state = False
        self.arena_id = None
        self.user_id = None

    def get_message_chatTactic(self, user_id, content_type):
        
        if content_type == 'recommendations': 
            result = TacticsChatMessage.query.filter(
                TacticsChatMessage.user_id != user_id, 
            ).order_by(TacticsChatMessage.timestamp.desc()).all()
        elif content_type == 'wishes': 
             result = TacticsChatMessage.query.filter(
                TacticsChatMessage.user_id != user_id, 
            ).order_by(TacticsChatMessage.timestamp.desc()).all()   
            
        return result    
         

    def get_cur_character(self, user_id):
        registration = Registrar.query.filter_by(user_id=user_id).first()
        if not registration:
            logger.error(f"Character for user {user_id} not found")
            return None

        character = Character.query.filter_by(character_id=registration.character_id).first()
        if not character:
            logger.error(f"Character with ID {registration.character_id} not found")
        return character

    async def battle_start(self, user_id, game_status):
        self.battle_state = (game_status == 'battle')
        if self.battle_state:
            await self.battle_process(user_id)

    async def battle_process(self, user_id):
        cur_arena = self.ccom.get_arena()  # получение арены
        reg_character_list = await self.ccom.get_registered_character_data()  # получение списка зарегистрированных персонажей

        opponent_character_list = []

        cur_character = self.get_cur_character(user_id)
        cur_character_txt = cur_character.to_str()  # Переводим текущего персонажа в строку
        
        # logger.info(f"----------- battle_process: {reg_character_list[0]}")
        
        for character in reg_character_list:
            if character['character_id'] != cur_character.character_id:  # Используем character_id для сравнения
                #logger.info(f"-----------cur_character: {cur_character}")
                str_character = self.ccom.convert_dict_toStr(character)
                opponent_character_list.append(str_character)  # Добавляем оппонентов как строки
                
        logger.info(f"---- PERS START ----")
        register_users = Registrar.query.all()
        user_ids = [user.user_id for user in register_users]
        
        while self.battle_state:
            opponent_moves_list = []
            for user_reg in user_ids:
                opponent_mov = self.ccom.get_message_chatArena(sender='fighter', arena_id=cur_arena.id, user_id=user_reg)
                opponent_moves_list.append(opponent_mov)

            referee_rating_list = self.ccom.get_message_chatArena(sender='referee',arena_id=cur_arena.id)
            
            # Генерация тактических рекомендаций
            await self.tcm.generate_tactics(self.user_id, cur_arena, cur_character_txt, opponent_character_list, opponent_moves_list, referee_rating_list)
            
            tactical_recommendation = self.get_message_chatTactic(self.user_id, 'recommendations')
            user_wishes = self.get_message_chatTactic(self.user_id, 'wishes')
            
            # Генерация хода бойца
            await self.flm.generate_fighter(self.user_id, cur_arena, cur_character_txt, tactical_recommendation, user_wishes, opponent_moves_list, referee_rating_list)

class TacticsManager:
    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.ccom = CoreCommon()
        self.stm = StatusManager()
        
    async def generate_tactics(self, user_id, cur_arena, cur_character_txt, opponent_character_list, opponent_moves_list, referee_rating_list):
        
        #logger.info(f"Recommendations for Fighter: {cur_character.name}")
        
        cur_arena_txt = cur_arena.to_str() 
        #cur_character_txt = cur_character.to_str() 

        prompt = f"Arena: {cur_arena_txt}\n\n"
        prompt += f"Our fighter: {cur_character_txt}\n\n"
        for opponent in opponent_character_list:
            prompt += f"Opponent: {opponent}\n\n"
        for opponent_move in opponent_moves_list:
            prompt += f"opponent move: {opponent_move}\n\n"
        for referee_rating in referee_rating_list:
            prompt += f"referee rating: {referee_rating}\n\n"
        prompt += "Generate tactical recommendations for the character's next move."

        try:
            assistant = GeminiAssistant("tactician")
            response = await assistant.send_message(prompt)
        except Exception as e:
            logger.error(f"Error sending message for {user_id}: {e}")
            return None, None

        if not response.strip():
            logger.error("Received empty response from assistant")
            await asyncio.sleep(10)

        tactics_message = TacticsChatMessage(content=response, sender="tactician", user_id=user_id)
        db.session.add(tactics_message)
        db.session.commit()

        logger.info(f"Tactical recommendation for {user_id} saved.")
    

class FighterManager:
    
    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.ccom = CoreCommon()
        self.stm = StatusManager()

    async def generate_fighter(self, user_id, cur_arena, cur_character, tactical_recommendation, user_wishes, opponent_moves_list, referee_rating_list):
        
        logger.info(f"step Fighter: {cur_character.name}")
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

        await asyncio.sleep(2)

        try:
            assistant = GeminiAssistant("fighter")
            response = await assistant.send_message(prompt)
        except Exception as e:
            logger.error(f"Error sending message for {user_id}: {e}")
            return "Error sending message"

        if not response.strip():
            logger.error("Received empty response from assistant")
            return "Received empty response from assistant"

        with current_app.app_context():
            
            message = f"fighter: {cur_character.name}\n\n"
            message += f"step: {response}\n\n"
            
            self.ccom.message_to_Arena(self, message, "fighter", cur_arena.id, user_id, cur_character.name)



