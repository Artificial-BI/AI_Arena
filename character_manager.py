from models import db, Character, Role
from gemini import GeminiAssistant

class CharacterManager:
    def __init__(self, gemini_api_key):
        self.gemini_api_key = gemini_api_key

    async def generate_character(self, description, role_name):
        # Получение инструкций для роли из базы данных
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            raise ValueError(f"Role '{role_name}' not found in the database")

        # Инициализация ассистента с инструкциями для роли
        character_assistant = GeminiAssistant(self.gemini_api_key, role.instructions)
        
        # Генерация характеристик персонажа на основе описания
        message = f"Generate character traits based on the following description: {description}"
        traits = await character_assistant.send_message(message)
        
        # Создание нового персонажа в базе данных
        character = Character(description=description, traits=traits)
        db.session.add(character)
        db.session.commit()
        return character
