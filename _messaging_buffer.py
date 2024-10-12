import threading
import asyncio
import time
import logging
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from chats_models import ReadStatus, ArenaChatMessage, GeneralChatMessage, TacticsChatMessage, Base
from config import Config
from datetime import datetime
from status_manager import StatusManager
from message_client import MessageClient
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageManager:
    def __init__(self, core_com):
        self.conf = Config()
        self.engine = create_engine(self.conf.MESSAGES_DB)
        self.Session = sessionmaker(bind=self.engine)
        self.sm = StatusManager()
        self.client = MessageClient()
        self.ccom = core_com
        self.buffer_cicle = True
        # Initialize database
        self.initialize_database()

        self.message_buffer = []
        self.lock = threading.Lock()

        # Start background thread for saving messages to the database
        self.saving_thread = threading.Thread(target=self._run_event_loop)
        self.saving_thread.daemon = True
        self.saving_thread.start()

        self.chat_model_map = {
            "arena_chat_message": ArenaChatMessage,
            "tactics_chat_message": TacticsChatMessage,
            "general_chat_message": GeneralChatMessage
        }

    async def box_extraction(self, message_box):
        if isinstance(message_box, dict):
            message_resp = message_box['message']
            #print('message_resp:',message_resp)
            if isinstance(message_resp, dict):
                message = message_resp['message']
                return message
            else:
                return message_resp
        return message_box

    async def create_channels(self):
        channel_list = ['tactic_chat', 'arena_chat', 'general_chat']
        for channel in channel_list:
            await self.client.create_channel(channel)
    
    async def send_message(self, name, message):
        resp = await self.client.send(message, name)
        return await self.box_extraction(resp)
                
    async def get_message(self, name):
        message_box = await self.client.get_message(name)
        return self.box_extraction(message_box)
    
    async def get_messages(self, name):
        messages = await self.client.get_messages(name)
        mess_list = []
        for message_box in messages:
            message = self.box_extraction(message_box)
            mess_list.append(message)
        return mess_list    

    def _run_event_loop(self):
        """Запуск отдельного цикла событий в потоке"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        #loop.run_until_complete(self.asinc_save_messages_to_db())

    def initialize_database(self):
        """Create tables in the database if they don't exist"""
        inspector = inspect(self.engine)
        tables = [ReadStatus, ArenaChatMessage, GeneralChatMessage, TacticsChatMessage]
        for table_class in tables:
            if not inspector.has_table(table_class.__tablename__):
                Base.metadata.tables[table_class.__tablename__].create(self.engine)
                logger.info(f"Table '{table_class.__tablename__}' created.")



    def add_message_to_buffer(self, message_json):
        try:
            with self.lock:
                self.message_buffer.append(message_json)
        except Exception as e:
            logger.error(f"Error adding message to buffer: {e}")

    async def asinc_save_messages_to_db(self):
        """Асинхронное сохранение сообщений из буфера в базу данных"""
        while self.buffer_cicle:
            game_state = await self.sm.get_status('game')
            await asyncio.sleep(1)  # Асинхронная пауза перед каждой проверкой буфера

            if game_state == 'stop' or game_state == 'error':
                self.buffer_cicle = False

            if self.buffer_cicle:    
                with self.lock:
                    if self.message_buffer:
                        session = self.Session()
                        try:
                            for message_json in self.message_buffer:
                                try:
                                    message = json.loads(message_json)
                                    if not isinstance(message, dict) or 'data' not in message:
                                        logger.error(f"Message is not a dict or missing 'data': {message}")
                                        continue

                                    if 'timestamp' in message['data']:
                                        message['data']['timestamp'] = datetime.strptime(
                                            message['data']['timestamp'], '%Y-%m-%d %H:%M:%S'
                                        )

                                    chat_model = self.chat_model_map.get(message['table'])
                                    if chat_model:
                                        new_message = chat_model(**message['data'])
                                        session.add(new_message)
                                    elif message['table'] == 'read_status':
                                        new_message = ReadStatus(**message['data'])
                                        session.add(new_message)
                                    else:
                                        logger.error(f"Unknown table: {message['table']}")
                                        continue
                                except Exception as e:
                                    logger.error(f"Error processing message: {e}")
                                    session.rollback()
                                    continue  # Move on to the next message
                            session.commit()
                        except Exception as e:
                            await self.sm.set_status('game', 'error', self.ccom.newTM())
                            await self.sm.set_status('battle', 'error', self.ccom.newTM())
                            await self.sm.set_status('error', f'Error saving message to DB: {e}', self.ccom.newTM())
                            logger.error(f"Saving messages: {e}\n MESS ERR:{message}")
                            session.rollback()
                            self.buffer_cicle = False
                        finally:
                            session.close()
                        # Clear buffer after successful save
                        self.message_buffer.clear()

    def receive_response_from_buffer(self, chat_type, user_id):
        """Receive response from message buffer"""
        try:
            response = self.get_messages_from_db(chat_type, user_id)
            return response
        except Exception as e:
            logger.error(f"Error receiving response from buffer: {e}")
            return {"status": "error", "message": [str(e)]}

    def get_messages_from_db(self, chat_type, user_id, limit=100):
        """Get messages from the database by chat type and user_id"""
        session = self.Session()
        try:
            messages_data = []
            chat_model = self.chat_model_map.get(chat_type)
            if chat_model:
                messages = session.query(chat_model).outerjoin(
                    ReadStatus, (chat_model.id == ReadStatus.message_id) & (ReadStatus.user_id == user_id)
                ).filter(
                    (ReadStatus.read_status != True) | (ReadStatus.read_status == None)
                ).order_by(chat_model.timestamp.desc()).limit(limit).all()
                for message in messages:
                    data = {
                        "id": message.id,
                        "user_id": message.user_id,
                        "content": message.content,
                        "sender": message.sender,
                        "timestamp": message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    if chat_type == "arena_chat_message":
                        data["arena_id"] = message.arena_id
                        data["name"] = message.name
                        data["read_status"] = message.read_status
                    messages_data.append({"table": chat_type,"data": data})
            else:
                raise ValueError(f"Unknown chat type: {chat_type}")
            return {"status": "ok", "messages": messages_data}

        except Exception as e:
            logger.error(f"Fetching messages from db: {e}")
            return {"status": "error", "messages": [str(e)]}

        finally:
            session.close()

    async def clear_previous_battle(self):
        """Clear messages and status of the previous battle"""
        session = self.Session()
        try:
            session.query(ReadStatus).delete()
            session.query(ArenaChatMessage).delete()
            session.query(TacticsChatMessage).delete()
            session.query(GeneralChatMessage).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error clearing previous battle: {e}")
        finally:
            session.close()

    def mark_message_as_read(self, user_id, message_id):
        """Mark a message as read for a user"""
        state_read = False
        session = self.Session()
        try:
            status = session.query(ReadStatus).filter_by(user_id=user_id, message_id=message_id).first()
            if not status:
                read_status = ReadStatus(user_id=user_id, message_id=message_id, read_status=True)
                session.add(read_status)
            else:
                status.read_status = True
            session.commit()
            state_read = True
        except Exception as e:
            session.rollback()
            logger.error(f"Error marking message as read: {e}")
        finally:
            session.close()
        return state_read
