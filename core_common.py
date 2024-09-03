import logging
from datetime import datetime
from flask import current_app
from models import (Arena, ArenaChatMessage, AssistantReadStatus, Character, GeneralChatMessage, PreRegistrar, Registrar, Role, TacticsChatMessage, db)
from multiproc import StatusManager
from message_buffer import MessageManager
# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoreCommon:
    
    def __init__(self):

        self.sm = StatusManager()
        self.mm = MessageManager()
    
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
            characters_data = []
            for registration in registrations:
                character = Character.query.filter_by(character_id = registration.character_id).first()
                if character:
                    characters_data.append({
                        "id": character.id,
                        "name": character.name,
                        "description": character.description,
                        "traits": character.traits,
                        "user_id": registration.user_id,
                        "character_id":registration.character_id
                    })
            return characters_data    
    
    def newTM(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return current_time
 
    def get_arena(self, arena_id=None):
        if arena_id != None:
            arena = Arena.query.offset(arena_id).first()
        else:
            end_arena = Arena.query.count()-1
            arena = Arena.query.offset(end_arena).first()   
        return arena
    
        
    def message_to_Arena(self, message, sender, arena_id, user_id, name):
        if sender is None or arena_id is None or user_id is None:
            logger.error("Cannot add message to arena chat: 'name' and 'arena_id' must not be None.")
            return

        message_data = {
            "content": f'{message}\n\n',
            "sender": sender,
            "user_id": user_id,
            "name": name,
            "arena_id": arena_id,
            "read_status": 0,
            "timestamp": self.newTM()
        }

       
        self.mm.add_message_to_buffer(message_data)

    def get_message_chatArena(self, sender, arena_id, user_id=None):
        messages = self.get_unread_messages(sender, arena_id, user_id)
        
        for message in messages:
            self.mark_message_as_read(user_id, message.id)
        
        return messages    

    # read message ArenaChatMessage
    def get_unread_messages(self, sender, arena_id, user_id=None):
        if user_id is not None:
            unread_messages = db.session.query(ArenaChatMessage).outerjoin(
                AssistantReadStatus,
                db.and_(
                    ArenaChatMessage.id == AssistantReadStatus.message_id,
                    AssistantReadStatus.user_id == user_id
                )
            ).filter(
                db.and_(
                    ArenaChatMessage.sender == sender,
                    ArenaChatMessage.arena_id == arena_id,
                    AssistantReadStatus.read_status == False
                )
            ).all()
        else:
            unread_messages = db.session.query(ArenaChatMessage).outerjoin(
                AssistantReadStatus,
                db.and_(
                    ArenaChatMessage.id == AssistantReadStatus.message_id,
                )
            ).filter(
                db.and_(
                    ArenaChatMessage.sender == sender,
                    ArenaChatMessage.arena_id == arena_id,
                    AssistantReadStatus.read_status == False
                )
            ).all()

        return unread_messages

    def mark_message_as_read(self, user_id, message_id):
        read_status = AssistantReadStatus.query.filter_by(user_id=user_id, message_id=message_id).first()
        if read_status:
            read_status.read_status = True
        else:
            read_status = AssistantReadStatus(
                user_id=user_id,
                message_id=message_id,
                read_status=True
            )
            db.session.add(read_status)
        db.session.commit()

    def add_message_to_arena(self, content, sender, user_id, name, arena_id):
        message = ArenaChatMessage(
            content=content,
            sender=sender,
            user_id=user_id,
            name=name,
            arena_id=arena_id,
            read_status=0  # Устанавливаем статус сообщения как непрочитанное.
        )
        db.session.add(message)
        db.session.commit()

        logger.info(f"Message from {sender} added to ArenaChatMessage: {content[:50]}")

    def convert_dict_toStr(self, dict_obj):
        return ', '.join(f'{key}: {value}' for key, value in dict_obj.items())
