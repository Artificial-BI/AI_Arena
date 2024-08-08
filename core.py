from datetime import datetime
from models import db, Arena, Tournament, TournamentMatch, Fight, Role, Player, ArenaChatMessage, Score, Character, PreRegistrar, Registrar, TacticsChatMessage, GeneralChatMessage  # Добавлен импорт GeneralChatMessage
from gemini import GeminiAssistant
import asyncio
from flask import current_app
import logging
from utils import parse_arena
import json
from tactics_manager import TacticsManager  # Добавлен импорт TacticsManager
import time
# --- core.py ---
class CoreCommon:
    def get_role_instructions(self, role_name):
        with current_app.app_context():
            role = Role.query.filter_by(name=role_name).first()
            logging.info(f"Получены инструкции для роли: {role}")
            if not role:
                raise ValueError(f"Роль '{role_name}' не найдена в базе данных")
            return role.instructions

class ArenaManager:
    def __init__(self):
        self.assistant = None
        self.ccom = CoreCommon()

    async def generate_arena(self, character_data):
        logging.info("Генерация арены")
        if self.assistant is None:
            self.assistant = GeminiAssistant('arena')

        parameters = await self.assistant.send_message(f"Generate arena with the following character data: {character_data}")
        
        if not parameters.strip():
            logging.error("Получены пустые параметры от ассистента")
            raise ValueError("Недопустимые параметры: 'parameters' не должны быть пустыми. Пожалуйста, предоставьте ненулевое значение.")

        arena_description = "Сгенерированная арена на основе характеристик персонажей"
        #logging.info(f"Параметры арены: {parameters}")

        parsed_parameters = parse_arena(parameters)

        new_arena = Arena(description=arena_description, parameters=json.dumps(parsed_parameters))
        db.session.add(new_arena)
        db.session.commit()

        logging.info(f"Арена сгенерирована с ID: {new_arena.id}")
        return new_arena

# --- core.py ---
class BattleManager:
    def __init__(self):
        self.ccom = CoreCommon()
        self.referee_assistant = None
        self.commentator_assistant = None
        self.arena_manager = ArenaManager()
        self.battle_count = 0
        self.round_count = 0
        self.tactics_manager = TacticsManager()
        self.timer_in_progress = False
        self.battle_in_progress = False
        self.timer_start_time = None
        self.countdown_duration = 30  # Продолжительность таймера в секундах

    def is_battle_in_progress(self):
        return self.battle_in_progress

    def is_timer_in_progress(self):
        return self.timer_in_progress

    # ... (остальные методы остаются неизменными)

    async def manage_battle_round(self, character_data, arena):
        self.round_count += 1
        logging.info(f"--- Начало раунда {self.round_count} ---")

        # Генерация ходов бойцов
        for character in character_data:
            await self.generate_fighter_move(character['id'], arena.id)

        # Ожидание получения ходов от всех участников
        await self.wait_for_moves(arena.id, len(character_data))

        # Получение непрочитанных сообщений от бойцов
        unread_messages = ArenaChatMessage.query.filter_by(arena_id=arena.id, read_status=0, sender='fighter').all()
        moves = [(msg.user_id, msg.content) for msg in unread_messages]

        # Пометка сообщений как прочитанных
        for msg in unread_messages:
            msg.read_status = 1
        db.session.commit()

        # Оценка ходов рефери
        referee_evaluation = await self.evaluate_moves(character_data, arena, moves)

        # Генерация комментариев комментатора
        commentary = await self.generate_commentary(character_data, arena, moves, referee_evaluation)

        logging.info(f"--- Раунд {self.round_count} завершен ---")

    async def wait_for_moves(self, arena_id, num_participants):
        logging.info("Ожидание ходов от участников")
        while True:
            unread_count = ArenaChatMessage.query.filter_by(arena_id=arena_id, read_status=0, sender='fighter').count()
            if unread_count >= num_participants:
                break
            await asyncio.sleep(1)
        logging.info("Все ходы получены")

    async def evaluate_moves(self, character_data, arena, moves):
        logging.info("Оценка ходов рефери")
        if self.referee_assistant is None:
            self.referee_assistant = GeminiAssistant('referee')
        evaluation_message = f"Оцените следующие ходы в арене {arena.id}: {moves}"
        if not evaluation_message.strip():
            logging.error("Пустое сообщение для оценки, пропуск оценки")
            return "Оценка не предоставлена"
        evaluation = await self.referee_assistant.send_message(evaluation_message)
        logging.info(f"Оценка рефери: {evaluation}")
    
        # Сохранение результатов судейства в чат арены
        evaluation_message = ArenaChatMessage(content=evaluation, sender='referee', user_id=None, arena_id=arena.id, read_status=0)
        db.session.add(evaluation_message)
        db.session.commit()
        
        return evaluation

    async def generate_commentary(self, character_data, arena, moves, evaluation):
        logging.info("Генерация комментариев")
        if self.commentator_assistant is None:
            self.commentator_assistant = GeminiAssistant('commentator')
        commentary_message = f"Сгенерируйте комментарии для следующих ходов в арене {arena.id}: {moves} с оценкой {evaluation}"
        if not commentary_message.strip():
            logging.error("Пустое сообщение для комментариев, пропуск комментариев")
            return "Комментарии не предоставлены"
        commentary = await self.commentator_assistant.send_message(commentary_message)
        logging.info(f"Комментарии: {commentary}")
        
        # Сохранение комментариев в общий чат
        commentary_message = ArenaChatMessage(content=commentary, sender='commentator', user_id=None, arena_id=arena.id, read_status=0)
        db.session.add(commentary_message)
        db.session.commit()
        
        return commentary

    async def start_battle(self):
        logging.info(f"--- Начало битвы {self.battle_count + 1} ---")
        try:
            self.battle_in_progress = True
            self.battle_count += 1
            ArenaChatMessage.query.delete()
            TacticsChatMessage.query.delete()
            db.session.commit()

            battle_start_message = ArenaChatMessage(content=f"--- Битва № {self.battle_count} ---", sender='system', user_id=None, read_status=0)
            db.session.add(battle_start_message)
            db.session.commit()

            asyncio.create_task(self.tactics_manager.generate_tactics())

            character_data = await self.get_registered_character_data()
            arena = await self.arena_manager.generate_arena(character_data)

            for round_number in range(2):
                round_start_message = ArenaChatMessage(content=f"--- Раунд № {round_number + 1} ---", sender='system', user_id=None, arena_id=arena.id, read_status=0)
                db.session.add(round_start_message)
                db.session.commit()

                await self.manage_battle_round(character_data, arena)

            logging.info("Битва завершена")
        except Exception as e:
            logging.error(f"Ошибка в битве: {e}", exc_info=True)
            raise
        finally:
            self.battle_in_progress = False
            self.stop_timer()
            await self.handle_post_battle_registration()

    async def handle_post_battle_registration(self):
        with current_app.app_context():
            # Очистка таблицы регистрации
            Registrar.query.delete()
            db.session.commit()

            # Перемещение данных из предварительной регистрации в основную регистрацию
            pre_registrations = PreRegistrar.query.all()
            for pre_reg in pre_registrations:
                new_registration = Registrar(
                    user_id=pre_reg.user_id,
                    character_id=pre_reg.character_id,
                    arena_id=pre_reg.arena_id
                )
                db.session.add(new_registration)
            db.session.commit()

            # Очистка таблицы предварительной регистрации
            PreRegistrar.query.delete()
            db.session.commit()

            logging.info("Таблица регистрации обновлена данными из предварительной регистрации")

    async def get_registered_character_data(self):
        logging.info("Получение данных зарегистрированных персонажей")
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

    async def generate_fighter_move(self, character_id, arena_id):
        character = Character.query.get(character_id)
        arena = Arena.query.get(arena_id)
        
        if not character or not arena:
            logging.error("Персонаж или арена не найдены")
            return "Персонаж или арена не найдены"

        # Получение последнего сообщения тактика
        tactics_message = TacticsChatMessage.query.filter_by(user_id=character.user_id).order_by(TacticsChatMessage.timestamp.desc()).first()
        tactics_content = tactics_message.content if tactics_message else ""

        # Получение последнего сообщения игрока
        player_message = GeneralChatMessage.query.filter_by(user_id=character.user_id).order_by(GeneralChatMessage.timestamp.desc()).first()
        player_content = player_message.content if player_message else ""

        # Конструирование запроса для ассистента бойца
        prompt = f"Атмосфера арены: {arena.description}\n"
        prompt += f"Параметры арены: {arena.parameters}\n\n"
        prompt += f"Имя персонажа: {character.name}\n"
        prompt += f"Характеристики персонажа: {character.traits}\n\n"
        prompt += f"Совет тактика: {tactics_content}\n"
        prompt += f"Ввод игрока: {player_content}\n\n"
        prompt += "Сгенерируйте следующий ход персонажа на основе вышеуказанной информации."

        assistant = GeminiAssistant("fighter")
        response = await assistant.send_message(prompt)

        if not response.strip():
            logging.error("Получен пустой ответ от ассистента")
            return "Получен пустой ответ от ассистента"

        fighter_move = ArenaChatMessage(content=response, sender="fighter", user_id=character.user_id, arena_id=arena.id)
        db.session.add(fighter_move)
        db.session.commit()

        logging.info(f"Ход бойца для {character.name} успешно создан")
        return "Ход бойца успешно создан"

    def start_timer(self, duration):
        self.timer_in_progress = True
        self.timer_start_time = time.time()
        self.countdown_duration = duration
        logging.info(f"Таймер запущен на {duration} секунд")

    def stop_timer(self):
        self.timer_in_progress = False
        self.timer_start_time = None
        logging.info("Таймер остановлен")

    def get_remaining_time(self):
        if not self.timer_in_progress:
            return 0
        elapsed_time = time.time() - self.timer_start_time
        remaining_time = self.countdown_duration - elapsed_time
        return max(0, remaining_time)
