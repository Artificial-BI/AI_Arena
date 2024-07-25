from models import db, Character, Role
from gemini import GeminiAssistant
import json
import re
from flask import current_app

class CharacterManager:
    def __init__(self):
        with current_app.app_context():
            self.assistant = GeminiAssistant(self.get_role_instructions('character_creator'))

    def get_role_instructions(self, role_name):
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            raise ValueError(f"Role '{role_name}' not found in the database")
        return role.instructions

    async def generate_character(self, description):
        # Генерация характеристик персонажа на основе описания
        message = f"Create a character based on the following description: {description}"
        response = await self.assistant.send_message(message)
        
        # Парсинг ответа
        character_data = self.parse_character_response(response)
        character_data['description'] = description
        
        # Генерация изображения персонажа
        character_data['image_url'] = self.generate_character_image(description)
        
        return character_data

    def parse_character_response(self, response):
        character_data = {}
        character_data['traits'] = {}
        
        # Парсинг текста ответа
        traits = re.findall(r"(\w+)\s*=\s*([\d.]+)%", response)
        for trait in traits:
            character_data['traits'][trait[0]] = float(trait[1])
        
        # Добавление базовых характеристик
        character_data['traits']['health'] = 1000  # Пример базовой характеристики
        character_data['traits']['mana'] = 500     # Пример базовой характеристики
        
        return character_data

    async def chat_with_assistant(self, message):
        response = await self.assistant.send_message(message)
        return response

    def generate_character_image(self, description):
        # Логика для генерации ссылки на изображение персонажа
        # Это место можно заменить на реальную логику генерации изображений
        return "images/default/character.png"
