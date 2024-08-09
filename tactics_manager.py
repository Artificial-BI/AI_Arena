from models import Character, TacticsChatMessage, Registrar, Arena, ArenaChatMessage, GeneralChatMessage
from extensions import db
from gemini import GeminiAssistant
import logging
import asyncio
from flask import current_app
import time

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TacticsManager:
    def __init__(self):
        self.assistant = None
        self.running = False

    async def generate_tactics(self, user_id):
        logger.info("Запуск процесса генерации тактических рекомендаций")
        arena = None
        while not arena:
            with current_app.app_context():
                arena = Arena.query.order_by(Arena.id.desc()).first()
            await asyncio.sleep(1)

        self.running = True
        while self.running:
            with current_app.app_context():
                registration = Registrar.query.filter_by(user_id=user_id).first()
                if registration:
                    character = Character.query.get(registration.character_id)
                    if character:
                        try:
                            await self.generate_tactic_for_character(character, arena)
                        except Exception as e:
                            logger.error(f"Ошибка при генерации тактики для {character.name}: {e}")
            await asyncio.sleep(10)  # Периодическое выполнение

    async def generate_tactic_for_character(self, character, arena):
        logger.info(f"Генерация тактической рекомендации для персонажа {character.name}")
        prompt = f"Атмосфера арены: {arena.description}\n"
        prompt += f"Параметры арены: {arena.parameters}\n\n"
        prompt += f"Имя персонажа: {character.name}\n"
        prompt += f"Характеристики персонажа: {character.traits}\n\n"
        prompt += "Сгенерируйте тактические рекомендации для следующего хода."

        assistant = GeminiAssistant("tactician")
        try:
            response = await assistant.send_message(prompt)
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения для {character.name}: {e}")
            return "Ошибка при отправке сообщения"

        if not response.strip():
            logger.error("Получен пустой ответ от ассистента")
            return "Получен пустой ответ от ассистента"

        tactics_message = TacticsChatMessage(content=response, sender="tactician", user_id=character.user_id)
        db.session.add(tactics_message)
        db.session.commit()

        logger.info(f"Рекомендация тактика для {character.name} успешно создана")
        return "Рекомендация тактика успешно создана"

    def stop(self):
        self.running = False
        logger.info("Процесс генерации тактических рекомендаций остановлен")

class FighterManager:
    def __init__(self):
        self.assistant = None
        self.running = False

    async def generate_fighter_move(self, character_id, arena_id):
        character = Character.query.get(character_id)
        arena = Arena.query.get(arena_id)

        if not character or not arena:
            logger.error("Персонаж или арена не найдены")
            return "Персонаж или арена не найдены"

        # Получение последнего сообщения тактика
        tactics_message = TacticsChatMessage.query.filter_by(user_id=character.user_id, read_status=0).order_by(TacticsChatMessage.timestamp.desc()).first()
        tactics_content = tactics_message.content if tactics_message else ""

        # Получение последнего сообщения игрока
        player_message = TacticsChatMessage.query.filter_by(user_id=character.user_id, sender='user', read_status=0).order_by(TacticsChatMessage.timestamp.desc()).first()
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
            logger.error("Получен пустой ответ от ассистента")
            return "Получен пустой ответ от ассистента"

        fighter_move = ArenaChatMessage(content=response, sender="fighter", user_id=character.user_id, arena_id=arena.id)
        db.session.add(fighter_move)
        db.session.commit()

        logger.info(f"Ход бойца для {character.name} успешно создан")

        # Отметка сообщений как прочитанных
        if tactics_message:
            tactics_message.read_status = 1
        if player_message:
            player_message.read_status = 1
        db.session.commit()

        return "Ход бойца успешно создан"

    async def generate_move(self, user_id):
        logger.info("Start fighter")
        self.running = True
        while self.running:
            with current_app.app_context():
                registration = Registrar.query.filter_by(user_id=user_id).first()
                if registration:
                    await self.generate_fighter_move(registration.character_id, registration.arena_id)
            await asyncio.sleep(1)

    def stop(self):
        self.running = False
        logger.info("Процесс генерации ходов бойца остановлен")

    def start_timer(self, duration):
        self.timer_in_progress = True
        self.timer_start_time = time.time()
        self.countdown_duration = duration
        logger.info(f"Таймер запущен на {duration} секунд")

    def stop_timer(self):
        self.timer_in_progress = False
        self.timer_start_time = None
        logger.info("Таймер остановлен")

    def get_remaining_time(self):
        if not self.timer_in_progress:
            return 0
        elapsed_time = time.time() - self.timer_start_time
        remaining_time = self.countdown_duration - elapsed_time
        return max(0, remaining_time)
