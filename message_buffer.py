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
from datetime import datetime

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
        # Инициализация базы данных
        self.initialize_database()

        self.message_buffer = []
        self.lock = threading.Lock()

        # Запуск фонового потока для записи сообщений в базу данных
        self.saving_thread = threading.Thread(target=self.save_messages_to_db)
        self.saving_thread.daemon = True
        self.saving_thread.start()
        

    def initialize_database(self):
        """Создаем таблицы в базе данных, если их нет"""
        inspector = inspect(self.engine)
        if not inspector.has_table(ReadStatus.__tablename__):
            Base.metadata.tables[ReadStatus.__tablename__].create(self.engine)
            logger.info(f"Table '{ReadStatus.__tablename__}' created.")
        
        if not inspector.has_table(ArenaChatMessage.__tablename__):
            Base.metadata.tables[ArenaChatMessage.__tablename__].create(self.engine)
            logger.info(f"Table '{ArenaChatMessage.__tablename__}' created.")
        
        if not inspector.has_table(GeneralChatMessage.__tablename__):
            Base.metadata.tables[GeneralChatMessage.__tablename__].create(self.engine)
            logger.info(f"Table '{GeneralChatMessage.__tablename__}' created.")
        
        if not inspector.has_table(TacticsChatMessage.__tablename__):
            Base.metadata.tables[TacticsChatMessage.__tablename__].create(self.engine)
            logger.info(f"Table '{TacticsChatMessage.__tablename__}' created.")

    def validate_message(self, message):
        required_fields = ['table', 'data']
        for field in required_fields:
            if field not in message:
                raise ValueError(f"Missing required field: {field}")


    def add_message_to_buffer(self, message_json):
        try:
            with self.lock:
                self.message_buffer.append(message_json)
                #logger.info(f"Message added to buffer: {message_json}")
        except Exception as e:
            logger.error(f"Error adding message to buffer: {e}")

    def save_messages_to_db(self):
        """Записываем сообщения из буфера в базу данных"""
        while self.buffer_cicle:
            time.sleep(1)  # Ждем 1 секунду перед каждой проверкой буфера
            game_status = self.sm.get_state('game')
            if game_status != 'stop':
                with self.lock:
                    if self.message_buffer:
                        session = self.Session()
                        try:
                            logger.info(f"Buffer: {len(self.message_buffer)}")

                            for message_json in self.message_buffer:
                                # Десериализуем JSON обратно в словарь
                                try:
                                    message = json.loads(message_json)
                                except json.JSONDecodeError as e:
                                    logger.error(f"Error decoding JSON: {e}")
                                    continue  # Пропускаем сообщение, если оно не декодируется

                                #logger.info(f"Попытка записать сообщение: {message}")

                                # Проверяем, что ключ 'data' присутствует в сообщении
                                if not isinstance(message, dict) or 'data' not in message:
                                    logger.error(f"Message is not a dict or missing 'data': {message}")
                                    continue  # Пропускаем некорректные сообщения

                                # Преобразуем строку `timestamp` в объект `datetime`
                                if 'timestamp' in message['data']:
                                    message['data']['timestamp'] = datetime.strptime(
                                        message['data']['timestamp'], '%Y-%m-%d %H:%M:%S'
                                    )

                                # Определяем тип сообщения и добавляем в базу данных
                                if message['table'] == 'general_chat_message':
                                    new_message = GeneralChatMessage(**message['data'])
                                elif message['table'] == 'tactics_chat_message':
                                    new_message = TacticsChatMessage(**message['data'])
                                elif message['table'] == 'arena_chat_message':
                                    new_message = ArenaChatMessage(**message['data'])
                                else:
                                    logger.error(f"Unknown table: {message['table']}")
                                    continue  # Пропускаем неизвестные типы таблиц

                                session.add(new_message)

                            # Фиксируем изменения
                            session.commit()
                        except Exception as e:
                            self.sm.set_state('game', 'stop', self.ccom.newTM())
                            self.sm.set_state('battle', 'error', self.ccom.newTM())
                            self.sm.set_state('error', f'Error saving message to DB: {e}', self.ccom.newTM())
                            logger.error(f"Error saving messages: {e}")
                            session.rollback()
                            self.buffer_cicle = False
                        finally:
                            session.close()

                        # Очищаем буфер после успешной записи
                        self.message_buffer.clear()


    def receive_response_from_buffer(self, chat_type):
        """Получаем ответ от буфера сообщений"""
        try:
            response = self.get_messages_from_buffer(chat_type, limit=100)
            return response
        except Exception as e:
            logger.error(f"Error receiving response from buffer: {e}")
            return {"status": "error", "message": [str(e)]}

    

    # def get_messages_from_buffer(self, chat_type, limit=100):
    #     """Получаем сообщения из базы данных по типу чата и заполняем буфер."""
    #     session = self.Session()
    #     try:
    #         if chat_type == "arena_chat_message":
    #             messages = session.query(ArenaChatMessage).order_by(ArenaChatMessage.timestamp.desc()).limit(limit).all()
    #         elif chat_type == "tactics_chat_message":
    #             messages = session.query(TacticsChatMessage).order_by(TacticsChatMessage.timestamp.desc()).limit(limit).all()
    #         elif chat_type == "general_chat_message":
    #             messages = session.query(GeneralChatMessage).order_by(GeneralChatMessage.timestamp.desc()).limit(limit).all()
    #         else:
    #             raise ValueError(f"Unknown chat type: {chat_type}")

    #         # Заполняем буфер сообщениями
    #         with self.lock:
    #             for message in messages:
    #                 # Преобразуем объект ORM в словарь
    #                 data = {
    #                     "id": message.id,
    #                     "user_id": message.user_id,
    #                     "content": message.content,
    #                     "sender": message.sender,
    #                     "timestamp": message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    #                 }

    #                 if isinstance(message, ArenaChatMessage):
    #                     data["arena_id"] = message.arena_id

    #                 # Добавляем сообщение в буфер
    #                 message_data = {
    #                     "table": chat_type,
    #                     "data": data
    #                 }
    #                 self.message_buffer.append(message_data)

    #         logger.info(f"Messages for {chat_type} | {len(messages)} added to buffer.")
    #         return {"status": "ok", "messages": messages}

    #     except Exception as e:
    #         logger.error(f"Error fetching messages from buffer: {e}")
    #         return {"status": "error", "messages": [str(e)]}

    #     finally:
    #         session.close()
    def get_messages_from_buffer(self, chat_type, limit=100):
        """Получаем сообщения из базы данных по типу чата и заполняем буфер."""
        session = self.Session()
        try:
            if chat_type == "arena_chat_message":
                messages = session.query(ArenaChatMessage).order_by(ArenaChatMessage.timestamp.desc()).limit(limit).all()
            elif chat_type == "tactics_chat_message":
                messages = session.query(TacticsChatMessage).order_by(TacticsChatMessage.timestamp.desc()).limit(limit).all()
            elif chat_type == "general_chat_message":
                messages = session.query(GeneralChatMessage).order_by(GeneralChatMessage.timestamp.desc()).limit(limit).all()
            else:
                raise ValueError(f"Unknown chat type: {chat_type}")

            # Заполняем буфер сообщениями, обращаясь к полям объекта напрямую
            messages_data = []
            for message in messages:
                data = {
                    "id": message.id,
                    "user_id": message.user_id,
                    "content": message.content,
                    "sender": message.sender,
                    "timestamp": message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    "read_status": message.read_status
                }
                if chat_type == "arena_chat_message":
                    data["arena_id"] = message.arena_id
                    data["name"] = message.name

                messages_data.append({
                    "table": chat_type,
                    "data": data
                })

            # Возвращаем список сообщений
            return {"status": "ok", "messages": messages_data}

        except Exception as e:
            logger.error(f"Error fetching messages from buffer: {e}")
            return {"status": "error", "messages": [str(e)]}

        finally:
            session.close()


    async def clear_previous_battle(self):
        """Очищаем сообщения и статус прошлой битвы"""
        session = self.Session()
        try:
            session.query(ReadStatus).delete()
            session.query(ArenaChatMessage).delete()
            session.query(TacticsChatMessage).delete()
            
            # Фиксируем изменения
            session.commit()
        except Exception as e:
            # Откатываем изменения в случае ошибки
            session.rollback()
            logger.error(f"Error clearing previous battle: {e}")
        finally:
            # Закрываем сессию
            session.close()

    def mark_message_as_read(self, user_id, message_id):
        """Отмечаем сообщение как прочитанное для пользователя"""
        session = self.Session()
        try:
            # Проверяем, существует ли запись о прочтении для данного пользователя и сообщения
            status = session.query(ReadStatus).filter_by(user_id=user_id, message_id=message_id).first()
            if not status:
                # Если нет, создаем новую запись
                read_status = ReadStatus(user_id=user_id, message_id=message_id, read_status=True)
                session.add(read_status)
            else:
                # Обновляем статус, если запись уже существует
                status.read_status = True
            
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error marking message as read: {e}")
        finally:
            session.close()

import zmq

class ZMQServer:
    def __init__(self):
        self.conf = Config()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(self.conf.MESS_PUB_PORT)
        self.manager = MessageManager(self)

    def run(self):
        """Основной цикл обработки запросов"""
        while True:
            message = self.socket.recv_json()
            command = message.get("command")

            if command == "add_message":
                # Добавляем сообщение в буфер
                self.manager.add_message_to_buffer(message.get("message_data"))
                self.socket.send_json({"status": "ok", "message": "Message added to buffer"})
            elif command == "clear_previous_battle":
                # Очищаем предыдущие сообщения и статус
                self.manager.clear_previous_battle()
                self.socket.send_json({"status": "ok", "message": "Previous battle cleared"})
            elif command == "mark_as_read":
                # Отмечаем сообщение как прочитанное
                user_id = message.get("user_id")
                message_id = message.get("message_id")
                self.manager.mark_message_as_read(user_id, message_id)
                self.socket.send_json({"status": "ok", "message": f"Message {message_id} marked as read for user {user_id}"})
            else:
                self.socket.send_json({"status": "error", "message": "Unknown command"})
