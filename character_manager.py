# --- character_manager.py ---

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
        # Generate character traits based on the description
        message = f"Create a character based on the following description: {description}"
        response = await self.assistant.send_message(message)
        
        # Parse the response
        character_data = self.parse_character_response(response)
        character_data['description'] = description
        
        # Generate character image
        character_data['image_url'] = await self.generate_character_image(description)
        
        return character_data

    def parse_character_response(self, response):
        character_data = {}
        character_data['traits'] = {}
        
        # Parse the response text
        traits = re.findall(r"(\w+)\s*=\s*([\d.]+)%", response)
        for trait in traits:
            character_data['traits'][trait[0]] = float(trait[1])
        
        # Add basic traits
        character_data['traits']['health'] = 1000  # Example basic trait
        character_data['traits']['mana'] = 500     # Example basic trait
        
        return character_data

    async def chat_with_assistant(self, message):
        response = await self.assistant.send_message(message)
        return response

    async def generate_character_image(self, description):
        try:
            image_url = await self.assistant.generate_image(description)
            return image_url
        except Exception as e:
            logging.error(f"Error generating character image: {e}")
            return "images/default/character.png"
