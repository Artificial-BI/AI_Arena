# character_manager.py
import os
from models import db, Character, Role
from gemini import GeminiAssistant

class CharacterManager:
    def __init__(self):
        print('gemini init')

    async def generate_character(self, description, role_name):
        # Получение инструкций для роли из базы данных
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            raise ValueError(f"Role '{role_name}' not found in the database")

        # Инициализация ассистента с инструкциями для роли
        character_assistant = GeminiAssistant(role.instructions)
        
        # Генерация характеристик персонажа на основе описания
        message = f"Generate character traits based on the following description: {description}"
        traits = await character_assistant.send_message(message)
        
        # Создание нового персонажа в базе данных
        character = Character(description=description, traits=traits)
        db.session.add(character)
        db.session.commit()
        return character

    async def create_character(self, name, description, user_id):
        # Создание нового персонажа в базе данных
        character = await self.generate_character(description, 'default_role')  # Используем роль по умолчанию
        character.name = name
        character.user_id = user_id
        character.image_url = self.generate_character_image(description, user_id, name)
        character.health_points = self.calculate_initial_health(description)
        db.session.commit()
        return character

    def generate_character_image(self, description, user_id, character_name):
        image_filename = 'character_image.png'  # Название файла изображения
        user_folder = os.path.join('static/images', f'user_{user_id}')
        character_folder = os.path.join(user_folder, character_name)

        if not os.path.exists(character_folder):
            os.makedirs(character_folder)

        image_path = os.path.join(character_folder, image_filename)

        # Здесь будет логика сохранения изображения на диск
        with open(image_path, 'wb') as f:
            f.write(b'')  # Сюда нужно поместить реальные данные изображения

        return os.path.relpath(image_path, 'static')

    def calculate_initial_health(self, description):
        return 1000
