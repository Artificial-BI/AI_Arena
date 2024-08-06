from models import Character, TacticsChatMessage, Registrar, Arena
from extensions import db
from gemini import GeminiAssistant
import logging
import asyncio
from flask import current_app

class TacticsManager:
    def __init__(self):
        self.assistant = None

    async def generate_tactics(self):
        logging.info("Запуск процесса генерации тактических рекомендаций")
        arena = None
        while not arena:
            with current_app.app_context():
                arena = Arena.query.order_by(Arena.id.desc()).first()
            await asyncio.sleep(1)

        while True:
            with current_app.app_context():
                registered_characters = Registrar.query.all()
                for registration in registered_characters:
                    character = Character.query.get(registration.character_id)
                    if character:
                        await self.generate_tactic_for_character(character, arena)
            await asyncio.sleep(10)  # Периодическое выполнение

    async def generate_tactic_for_character(self, character, arena):
        logging.info(f"Генерация тактической рекомендации для персонажа {character.name}")
        # Конструирование запроса для ассистента тактика
        prompt = f"Атмосфера арены: {arena.description}\n"
        prompt += f"Параметры арены: {arena.parameters}\n\n"
        prompt += f"Имя персонажа: {character.name}\n"
        prompt += f"Характеристики персонажа: {character.traits}\n\n"
        prompt += "Сгенерируйте тактические рекомендации для следующего хода."

        # Создание ассистента и получение ответа
        assistant = GeminiAssistant("tactician")
        response = await assistant.send_message(prompt)

        if not response.strip():
            logging.error("Получен пустой ответ от ассистента")
            return "Получен пустой ответ от ассистента"

        # Сохранение рекомендации тактика в чат тактики
        tactics_message = TacticsChatMessage(content=response, sender="tactician", user_id=character.user_id)
        db.session.add(tactics_message)
        db.session.commit()

        logging.info(f"Рекомендация тактика для {character.name} успешно создана")
        return "Рекомендация тактика успешно создана"
