from datetime import datetime
from models import db, Arena, ArenaChatMessage, Registrar, Character, TacticsChatMessage, GeneralChatMessage, PreRegistrar, Role
from gemini import GeminiAssistant
import asyncio
from flask import current_app, g
import logging
from utils import parse_arena
import json
from tactics_manager import TacticsManager, Fighter
import time

# --- core.py ---
# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoreCommon:
    def get_role_instructions(self, role_name):
        with current_app.app_context():
            role = Role.query.filter_by(name=role_name).first()
            logger.info(f"Получены инструкции для роли: {role}")
            if not role:
                raise ValueError(f"Роль '{role_name}' не найдена в базе данных")
            return role.instructions

class ArenaManager:
    def __init__(self):
        self.assistant = None
        self.ccom = CoreCommon()

    async def generate_arena(self, character_data):
        logger.info("Генерация арены")
        if self.assistant is None:
            self.assistant = GeminiAssistant('arena')

        parameters = await self.assistant.send_message(f"Generate arena with the following character data: {character_data}")
        
        if not parameters.strip():
            logger.error("Получены пустые параметры от ассистента")
            raise ValueError("Недопустимые параметры: 'parameters' не должны быть пустыми. Пожалуйста, предоставьте ненулевое значение.")

        arena_description = parameters
        parsed_parameters = parse_arena(parameters)

        new_arena = Arena(description=arena_description, parameters=json.dumps(parsed_parameters))
        db.session.add(new_arena)
        db.session.commit()

        # Добавляем описание арены в чат арены
        arena_chat_message = ArenaChatMessage(content=f"Описание арены: {arena_description}\nПараметры: {parsed_parameters}", sender='system', user_id=None, arena_id=new_arena.id, read_status=0)
        db.session.add(arena_chat_message)
        db.session.commit()

        logger.info(f"Арена сгенерирована с ID: {new_arena.id}")
        return new_arena
class BattleManager:
    def __init__(self):
        self.ccom = CoreCommon()
        self.referee_assistant = None
        self.commentator_assistant = None
        self.arena_manager = ArenaManager()
        self.battle_count = 0
        self.round_count = 0
        self.tactics_manager = TacticsManager()
        self.fighter = Fighter()
        self.timer_in_progress = False
        self.battle_in_progress = False
        self.timer_start_time = None
        self.countdown_duration = 30

    def start_timer(self, duration):
        self.countdown_duration = duration
        self.timer_start_time = time.time()
        self.timer_in_progress = True
        logging.info(f"Таймер запущен на {duration} секунд")

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
        logger.info("Таймер остановлен")

    async def start_battle(self, user_id):
        logger.info(f"--- Начало битвы {self.battle_count + 1} ---")
        try:
            self.battle_in_progress = True
            self.battle_count += 1
            ArenaChatMessage.query.delete()  # Очищаем чат арены перед началом новой битвы
            TacticsChatMessage.query.delete()  # Очищаем чат тактика перед началом новой битвы
            db.session.commit()

            battle_start_message = ArenaChatMessage(
                content=f"--- Битва № {self.battle_count} ---", sender='system', user_id=None, read_status=0
            )
            db.session.add(battle_start_message)
            db.session.commit()

            character_data = await self.get_registered_character_data()
            arena = await self.arena_manager.generate_arena(character_data)

            # Инициализация боя для каждого бойца
            for character in character_data:
                self.tactics_manager.add_fighter(character['user_id'])
                self.fighter.add_fighter(character['user_id'])
            num = 0
            
            logger.info("-------------- BASE CICLE ---------------")  
            
            while self.battle_in_progress:  # Основной цикл битвы
                num +=1
                await self.manage_battle_round(character_data, arena)
                
                logger.info(f"-------------- STEP {num} ---------------")
                
                if self.check_battle_end(character_data):
                    break
                if num >=2:
                    self.battle_in_progress = False
                   
                    
                    
                
            logger.info("Битва завершена")
        except Exception as e:
            logger.error(f"Ошибка в битве: {e}", exc_info=True)
            raise
        finally:
            self.battle_in_progress = False
            self.stop_timer()
            self.tactics_manager.stop()
            self.fighter.stop()
            await self.handle_post_battle_registration()

    async def get_registered_character_data(self):
        logger.info("Получение данных зарегистрированных персонажей")
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

    async def manage_battle_round(self, character_data, arena):
        self.round_count += 1
        logger.info(f"--- Начало раунда {self.round_count} ---")

        round_start_message = ArenaChatMessage(
            content=f"--- Раунд № {self.round_count} ---", sender='system', user_id=None, arena_id=arena.id, read_status=0
        )
        db.session.add(round_start_message)
        db.session.commit()

        # Запускаем генерацию тактик и ходов для всех бойцов одновременно
        tactics_tasks = [asyncio.create_task(self.tactics_manager.generate_tactics(char['user_id'])) for char in character_data]
        fighter_tasks = [asyncio.create_task(self.fighter.generate_move(char['user_id'])) for char in character_data]
        await asyncio.gather(*tactics_tasks, *fighter_tasks)  # Ожидаем завершения всех задач

        await self.wait_for_moves(arena.id, len(character_data))

        unread_messages = ArenaChatMessage.query.filter_by(arena_id=arena.id, read_status=0, sender='fighter').all()
        moves = [(msg.user_id, msg.content) for msg in unread_messages]

        logger.info(f">>>>>> moves:  {moves}")

        for msg in unread_messages:
            msg.read_status = 1
        db.session.commit()

        referee_evaluation = await self.evaluate_moves(character_data, arena, moves)
        commentary = await self.generate_commentary(character_data, arena, moves, referee_evaluation)

        general_chat_message = GeneralChatMessage(
            content=f"Комментатор: {commentary}", sender='commentator', user_id=None, read_status=0
        )
        db.session.add(general_chat_message)
        db.session.commit()

        logger.info(f"--- Раунд {self.round_count} завершен ---")

    async def wait_for_moves(self, arena_id, num_participants):
        logger.info("Ожидание ходов от участников")
        while True:
            unread_count = ArenaChatMessage.query.filter_by(arena_id=arena_id, read_status=0, sender='fighter').count()
            logger.info(f">>>>> {unread_count} >= {num_participants}")
            if unread_count >= num_participants:
                break
            await asyncio.sleep(1)
        logger.info("Все ходы получены")

    async def evaluate_moves(self, character_data, arena, moves):
        logger.info("Оценка ходов рефери")
        if self.referee_assistant is None:
            self.referee_assistant = GeminiAssistant('referee')
        evaluation_message = f"Оцените следующие ходы в арене {arena.id}: {moves}"
        if not evaluation_message.strip():
            logger.error("Пустое сообщение для оценки, пропуск оценки")
            return "Оценка не предоставлена"
        evaluation = await self.referee_assistant.send_message(evaluation_message)
        logger.info(f"Оценка рефери: {evaluation}")

        evaluation_message = ArenaChatMessage(
            content=evaluation, sender='referee', user_id=None, arena_id=arena.id, read_status=0
        )
        db.session.add(evaluation_message)
        db.session.commit()

        # Обновляем здоровье персонажей на основе оценки рефери
        self.update_character_health(evaluation)

        return evaluation
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

            logger.info("Таблица регистрации обновлена данными из предварительной регистрации")






    def update_character_health(self, evaluation):
        """Обновляет здоровье персонажей на основе оценки рефери."""
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
                        traits = json.loads
