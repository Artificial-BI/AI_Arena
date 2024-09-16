import logging
import json
from datetime import datetime
from flask import current_app
from models import Arena, Character, Registrar, Role
from multiproc import StatusManager
from message_buffer import MessageManager

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoreCommon:
    
    def __init__(self):
        self.sm = StatusManager()
        self.mm = MessageManager(self)

    def newTM(self):
        # Returns the current time in string format
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def get_registered_character_data(self):
        with current_app.app_context():
            registrations = Registrar.query.all()
            characters_data = []
            for registration in registrations:
                character = Character.query.filter_by(character_id=registration.character_id).first()
                if character:
                    characters_data.append({
                        "id": character.id,
                        "name": character.name,
                        "description": character.description,
                        "traits": character.traits,
                        "user_id": registration.user_id,
                        "character_id": registration.character_id
                    })
            return characters_data    

    def character_toStr(self, character):
        ch_str = f"name: {character['name']}\n"
        ch_str += f"description: {character['description']}\n"
        ch_str += f"traits: {character['traits']}"
        return ch_str

    async def get_arena(self, arena_id=None):
        # Get arena by ID
        with current_app.app_context():
            if arena_id is not None:
                arena = Arena.query.offset(arena_id).first()
            else:
                end_arena = Arena.query.count() - 1
                arena = Arena.query.offset(end_arena).first()
            return arena

    async def clear_chats(self):
        await self.mm.clear_previous_battle()

    # ------------------ Arena Chat ------------------------
    async def message_to_Arena(self, message, sender, arena_id, user_id, name, read_status=0):
        if sender is None or arena_id is None or user_id is None:
            logger.error(f"Cannot add message to arena chat: {name} and {arena_id} must not be None.")
            return

        message_json = json.dumps({
            "table": "arena_chat_message",
            "data": {
                "content": message,
                "sender": sender,
                "user_id": user_id,
                "name": name,
                "arena_id": arena_id,
                "read_status": read_status,
                "timestamp": self.newTM()
            }
        })
        self.mm.add_message_to_buffer(message_json)

    # Method to get messages
    async def get_message_chatArena(self, sender, arena_id, user_id, mark_user_id):
        messages = await self.get_unread_messages("arena_chat_message", user_id, sender, arena_id)
        chat_messages = []
        for message in messages:
            if 'id' in message['data']:
                if mark_user_id:
                    await self.mark_message_as_read(mark_user_id, message['data']['id'])
                chat_messages.append(message['data'])
            else:
                logger.error(f"Message does not contain 'id': {message['data']}")
        return chat_messages  

    # ------------------- Tactic Chat -------------------
    async def message_to_Tactics(self, message, sender, user_id, read_status=0):
        if sender is None or user_id is None:
            logger.error(f"Cannot add message to tactics chat: sender: {sender} and user_id: {user_id} must not be None.")
            return

        message_json = json.dumps({
            "table": "tactics_chat_message",
            "data": {
                "content": message,
                "sender": sender,
                "user_id": user_id,
                "read_status": read_status,
                "timestamp": self.newTM()
            }
        })
        self.mm.add_message_to_buffer(message_json)

    async def get_message_chatTactics(self, sender, user_id, mark_user_id):
        messages = await self.get_unread_messages("tactics_chat_message", user_id, sender)
        chat_messages = []
        for message in messages:
            if 'id' in message['data']:
                if mark_user_id:
                    await self.mark_message_as_read(mark_user_id, message['data']['id'])
                chat_messages.append(message['data'])
            else:
                logger.error(f"Message does not contain 'id': {message['data']}")
        return chat_messages

    # ------------------- General Chat ----------------------------
    async def message_to_GeneralChat(self, message, sender, user_id):
        if sender is None or user_id is None:
            logger.error(f"Cannot add message to general chat: {sender} user_id: {user_id}.")
            return

        message_json = json.dumps({
            "table": "general_chat_message",
            "data":{
                "content": message,
                "sender": sender,
                "user_id": user_id,
                "timestamp": self.newTM()
            }
        })
        self.mm.add_message_to_buffer(message_json)

    async def get_message_GeneralChat(self, sender, user_id, mark_user_id):
        messages = await self.get_unread_messages("general_chat_message", user_id, sender)
        chat_messages = []
        for message in messages:
            if 'id' in message['data']:
                if mark_user_id:
                    await self.mark_message_as_read(mark_user_id, message['data']['id'])
                chat_messages.append(message['data'])
            else:
                logger.error(f"Message does not contain 'id': {message['data']}")
        return chat_messages

    #-----------------------------------------------------------------------------------------------
    async def mark_message_as_read(self, user_id, message_id):
        res = self.mm.mark_message_as_read(user_id, message_id)
        return res

    # Universal method to get messages
    async def get_unread_messages(self, table, user_id, sender=None, arena_id=None):
        try:
            response = self.mm.receive_response_from_buffer(table, user_id)
            if response.get("status") == "ok":
                messages = response.get("messages", [])
                filtered_messages = []
                for message in messages:
                    if sender:
                        if message['data'].get('sender') != sender:
                            continue
                    if arena_id:
                        if message['data'].get('arena_id') != arena_id:
                            continue
                    filtered_messages.append(message)
                return filtered_messages
        except Exception as e:
            logger.error(f"Error fetching messages from buffer: {e}")
            return []
