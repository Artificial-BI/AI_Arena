import threading
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from chats_models import ArenaChatMessage, GeneralChatMessage, TacticsChatMessage
from config import Config

class MessageManager:
    def __init__(self):
        self.conf = Config()
        self.engine = create_engine(self.conf.MESSAGES_DB)
        self.Session = sessionmaker(bind=self.engine)
        self.message_buffer = []
        self.lock = threading.Lock()

        # Запуск фонового потока для записи сообщений в базу данных
        self.saving_thread = threading.Thread(target=self.save_messages_to_db)
        self.saving_thread.daemon = True
        self.saving_thread.start()

    def add_message_to_buffer(self, message_data):
        with self.lock:
            self.message_buffer.append(message_data)

    def save_messages_to_db(self):
        while True:
            time.sleep(1)
            with self.lock:
                if self.message_buffer:
                    session = self.Session()
                    try:
                        for message in self.message_buffer:
                            if message['table'] == 'GeneralChatMessage':
                                new_message = GeneralChatMessage(**message['data'])
                            elif message['table'] == 'TacticsChatMessage':
                                new_message = TacticsChatMessage(**message['data'])
                            elif message['table'] == 'ArenaChatMessage':
                                new_message = ArenaChatMessage(**message['data'])
                            session.add(new_message)
                        session.commit()
                    except Exception as e:
                        session.rollback()
                        print(f"Error saving messages: {e}")
                    finally:
                        session.close()
                    self.message_buffer.clear()



# # Добавление сообщения в буфер
# mm = MessageManager()
# mm.add_message_to_buffer({
#     'table': 'GeneralChatMessage',
#     'data': {'user_id': 1, 'content': 'Hello!', 'sender': 'User1'}
# })


import zmq

class ZMQServer:
    def __init__(self):
        self.conf = Config()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(self.conf.MESS_PUB_PORT)
        #self.socket.bind(f"tcp://*:{port}")
        self.manager = MessageManager()

    def run(self):
        while True:
            message = self.socket.recv_json()
            command = message.get("command")

            if command == "add_message":
                self.manager.add_message_to_buffer(message.get("message_data"))
                self.socket.send_json({"status": "ok", "message": "Message added to buffer"})
            else:
                self.socket.send_json({"status": "error", "message": "Unknown command"})

# Пример использования:
# server = ZMQServer(5555, manager)
# server.run()
