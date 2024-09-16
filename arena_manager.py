

import re
import json
from assistant import Assistant
from open_ai import AIDesigner
import logging
from core_common import CoreCommon
from multiproc import StatusManager
from utils import parse_arena
from models import (Arena, db)
# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArenaManager:
    def __init__(self):
        self.assistant = None
        self.ccom = CoreCommon()
        self.sm = StatusManager()

    def create_arena_image(self, new_arena, arena_description):
        designer = AIDesigner()
        filename = re.sub(r'[\\/*?:"<>|]', "", f"arena_{new_arena.id}")
        image_filename = f"{filename}.png"
        image_url = designer.create_image(arena_description, "arena", image_filename)
        return image_url

    async def generate_arena(self):
        logger.info("Generating arena")
        self.assistant = Assistant('arena')

        character_data = await self.ccom.get_registered_character_data()

        parameters = await self.assistant.send_message(character_data, 'gemini')

        if not parameters.strip():
            logger.error("Received empty parameters from assistant")
            raise ValueError("Invalid parameters: 'parameters' must not be empty. Please provide a non-null value.")

        arena_description = parameters
        parsed_parameters = parse_arena(parameters)

        new_arena = Arena(description=arena_description, parameters=json.dumps(parsed_parameters))
        db.session.add(new_arena)
        db.session.commit()

        image_url = self.create_arena_image(new_arena, arena_description) 

        new_arena.image_url = image_url
                                     #  message, sender, arena_id, user_id, name
        #self.ccom.message_to_Arena(f"Arena description: {arena_description} \n Parameters: {parsed_parameters}", _sender='sys', _name='sys', _arena_id=new_arena.id)

        logger.info(f"Arena generated with ID: {new_arena.id} and image {image_url}")
        return new_arena