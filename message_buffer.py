import threading
import time
import logging
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from chats_models import ReadStatus, ArenaChatMessage, GeneralChatMessage, TacticsChatMessage, Base
from config import Config
from datetime import datetime
from multiproc import StatusManager
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageManager:
    def __init__(self, core_com):
        self.conf = Config()
        self.engine = create_engine(self.conf.MESSAGES_DB)
        self.Session = sessionmaker(bind=self.engine)
        self.sm = StatusManager()
        self.ccom = core_com
        self.buffer_cicle = True
        # Initialize database
        self.initialize_database()

        self.message_buffer = []
        self.lock = threading.Lock()

        # Start background thread for saving messages to the database
        self.saving_thread = threading.Thread(target=self.save_messages_to_db)
        self.saving_thread.daemon = True
        self.saving_thread.start()

        self.chat_model_map = {
            "arena_chat_message": ArenaChatMessage,
            "tactics_chat_message": TacticsChatMessage,
            "general_chat_message": GeneralChatMessage
        }

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

    def save_messages_to_db(self):
        """Save messages from buffer to database"""
        while self.buffer_cicle:
            game_state = self.sm.get_state('game')
            time.sleep(1)  # Wait 1 second before each buffer check
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
                            self.sm.set_state('game', 'error', self.ccom.newTM())
                            self.sm.set_state('battle', 'error', self.ccom.newTM())
                            self.sm.set_state('error', f'Error saving message to DB: {e}', self.ccom.newTM())
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
