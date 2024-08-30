import logging
from datetime import datetime
from flask import current_app
from models import (ArenaChatMessage, Character, GeneralChatMessage, PreRegistrar, Registrar, Role, TacticsChatMessage, db)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class CoreCommon:
    def get_role_instructions(self, role_name):
        with current_app.app_context():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                raise ValueError(f"Role '{role_name}' not found in the database")
            logger.info(f"Instructions received for role: {role}")
            return role.instructions
        
    async def get_registered_character_data(self):
        logger.info("Fetching registered character data")
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
    
    def newTM(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return current_time
    
    
    def message_to_Arena(_message, _sender='sys', _name='sys', _user_id=None, _arena_id=None):
        if _name is None or _arena_id is None:
            logger.error("Cannot add message to arena chat: 'name' and 'arena_id' must not be None.")
            return

        set_message = ArenaChatMessage(
            content=f'{_message}\n', 
            sender=_sender, 
            user_id=_user_id, 
            name=_name, 
            arena_id=_arena_id, 
            read_status=0
        )
        db.session.add(set_message)
        db.session.commit()