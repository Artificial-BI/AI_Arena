from models import Character, TacticsChatMessage, Registrar, Arena, ArenaChatMessage, GeneralChatMessage
from extensions import db
from gemini import GeminiAssistant
import logging
import asyncio
from flask import current_app

# --- tactic_manager.py ---
# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TacticsManager:
    def __init__(self):
        self.assistant = None
        self.running = False
        self.fighters = {}  # Словарь для хранения бойцов
        
    def add_fighter(self, user_id):
        self.fighters[user_id] = None  # Инициализируем без данных о персонаже


    async def gather_arena_info(self, arena_id, user_id):
        """Собирает информацию о характеристиках арены, последних ходах противников и характеристиках персонажа."""
        with current_app.app_context():
            # Получаем данные об арене
            arena = Arena.query.get(arena_id)
            if not arena:
                logger.error(f"Арена с ID {arena_id} не найдена")
                return None, None

            # Получаем данные о персонаже
            registration = Registrar.query.filter_by(user_id=user_id).first()
            if not registration:
                logger.error(f"Персонаж для пользователя {user_id} не найден")
                return None, None

            character = Character.query.get(registration.character_id)
            if not character:
                logger.error(f"Персонаж с ID {registration.character_id} не найден")
                return None, None

            # Собираем последние ходы противников
            opponent_moves = ArenaChatMessage.query.filter(ArenaChatMessage.user_id != user_id, ArenaChatMessage.arena_id == arena_id).order_by(ArenaChatMessage.timestamp.desc()).all()
            opponent_moves_text = "\n".join([f"{move.sender}: {move.content}" for move in opponent_moves])

            return arena, character, opponent_moves_text
    async def generate_tactics(self, user_id):
        """Генерация тактических рекомендаций для персонажа."""
        logger.info(f"Запуск процесса генерации тактических рекомендаций для пользователя {user_id}")

        self.running = True
        while self.running:
            with current_app.app_context():
                # Получение арены и персонажа
                registration = Registrar.query.filter_by(user_id=user_id).first()
                if not registration:
                    logger.error(f"Персонаж для пользователя {user_id} не найден")
                    await asyncio.sleep(10)
                    continue

                arena, character, opponent_moves_text = await self.gather_arena_info(registration.arena_id, user_id)
                if not arena or not character:
                    await asyncio.sleep(10)
                    continue

                # Генерация тактической рекомендации
                prompt = f"Атмосфера арены: {arena.description}\n"
                prompt += f"Параметры арены: {arena.parameters}\n\n"
                prompt += f"Имя персонажа: {character.name}\n"
                prompt += f"Характеристики персонажа: {character.traits}\n\n"
                if opponent_moves_text:
                    prompt += f"Последние ходы противников:\n{opponent_moves_text}\n\n"
                prompt += "Сгенерируйте тактические рекомендации для следующего хода персонажа."

                if self.assistant is None:
                    self.assistant = GeminiAssistant("tactician")

                try:
                    response = await self.assistant.send_message(prompt)
                except Exception as e:
                    logger.error(f"Ошибка при отправке сообщения для {character.name}: {e}")
                    await asyncio.sleep(10)
                    continue

                if not response.strip():
                    logger.error("Получен пустой ответ от ассистента")
                    await asyncio.sleep(10)
                    continue

                # Запись тактической рекомендации в чат
                tactics_message = TacticsChatMessage(content=response, sender="tactician", user_id=user_id)
                db.session.add(tactics_message)
                db.session.commit()

                logger.info(f"Рекомендация тактика для {character.name}")

                # Ожидание, пока боец прочитает рекомендацию
                while True:
                    await asyncio.sleep(1)
                    with current_app.app_context():
                        latest_tactics_message = TacticsChatMessage.query.filter_by(
                            user_id=user_id, sender="tactician"
                        ).order_by(TacticsChatMessage.timestamp.desc()).first()
                        if latest_tactics_message and latest_tactics_message.read_status == 1:
                            logger.info(f"Рекомендация для {character.name} прочитана бойцом, генерируем новую")
                            break
                        await asyncio.sleep(10)
                        
            await asyncio.sleep(10)  # Периодическое выполнение

    def stop(self):
        self.running = False
        logger.info("Процесс генерации тактических рекомендаций остановлен")

class Fighter:
    def __init__(self):
        self.assistant = None
        self.running = False
        self.fighters = {}  # Словарь для хранения бойцов

    def add_fighter(self, user_id):
        self.fighters[user_id] = None  # Инициализируем без данных о персонаже

    async def wait_for_instructions(self, user_id):
        """Ждет получения тактических инструкций или пожеланий от игрока."""
        while self.running:
            with current_app.app_context():
                # Проверка наличия новых тактических рекомендаций
                tactics_message = TacticsChatMessage.query.filter_by(
                    user_id=user_id, sender='tactician', read_status=0
                ).order_by(TacticsChatMessage.timestamp.desc()).first()
                if tactics_message:
                    logger.info(f"Получена тактическая рекомендация для Fighter: {user_id}")
                    return tactics_message

            await asyncio.sleep(1)  # Ожидание перед следующей проверкой

    async def get_player_input(self, user_id):
        """Получает пожелания игрока, если они есть."""
        with current_app.app_context():
            player_message = TacticsChatMessage.query.filter_by(
                user_id=user_id, sender='user', read_status=0
            ).order_by(TacticsChatMessage.timestamp.desc()).first()
            if player_message:
                logger.info(f"Получено пожелание игрока для пользователя {user_id}: {player_message.content}")
                return player_message
            return None

    async def generate_fighter_move(self, character, arena, tactics_content, player_content):
        """Генерирует ход бойца на основе инструкций тактика и пожеланий игрока."""
        prompt = f"Атмосфера арены: {arena.description}\n"
        prompt += f"Параметры арены: {arena.parameters}\n\n"
        prompt += f"Имя персонажа: {character.name}\n"
        prompt += f"Характеристики персонажа: {character.traits}\n\n"
        prompt += f"Совет тактика: {tactics_content}\n"
        if player_content:
            prompt += f"Пожелания игрока: {player_content}\n\n"
        prompt += "Сгенерируйте следующий ход персонажа на основе вышеуказанной информации."

        if self.assistant is None:
            self.assistant = GeminiAssistant("fighter")

        response = await self.assistant.send_message(prompt)

        if not response.strip():
            logger.error("Получен пустой ответ от ассистента")
            return "Получен пустой ответ от ассистента"

        # Запись хода в чат арены
        fighter_move = ArenaChatMessage(content=response, sender="fighter", user_id=character.user_id, arena_id=arena.id)
        db.session.add(fighter_move)
        db.session.commit()

        logger.info(f"Ход бойца для {character.name} успешно создан")

        return "Ход бойца успешно создан"

    async def generate_move(self, user_id):
        logger.info("Запуск бойца")
        self.running = True
        while self.running:
            with current_app.app_context():
                registration = Registrar.query.filter_by(user_id=user_id).first()
                if registration:
                    character = Character.query.get(registration.character_id)
                    arena = Arena.query.get(registration.arena_id)
                    if not character or not arena:
                        logger.error("Персонаж или арена не найдены")
                        break

                    # Ждет получения инструкций от тактика
                    tactics_message = await self.wait_for_instructions(user_id)
                    if tactics_message:
                        player_message = await self.get_player_input(user_id)
                        player_content = player_message.content if player_message else ""

                        # Генерирует и выполняет ход
                        await self.generate_fighter_move(character, arena, tactics_message.content, player_content)

                        # Отмечает сообщения как прочитанные
                        tactics_message.read_status = 1
                        if player_message:
                            player_message.read_status = 1
                        db.session.commit()

            await asyncio.sleep(1)  # Ожидание перед следующим ходом

    def stop(self):
        self.running = False
        logger.info("Процесс генерации ходов бойца остановлен")