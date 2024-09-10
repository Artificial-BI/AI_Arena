import unittest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from chats_models import ArenaChatMessage, GeneralChatMessage, TacticsChatMessage, ReadStatus, Base
from message_buffer import MessageManager
from datetime import datetime
import logging

# Глобальное подключение к базе данных, как в вашем app.py
engine = create_engine('sqlite:///test_db.sqlite', echo=False)
Session = sessionmaker(bind=engine)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Открываем одно соединение с базой данных
        cls.connection = engine.connect()
        cls.session = Session(bind=cls.connection)

        # Создаем таблицы в базе данных
        Base.metadata.create_all(cls.connection)

        # Инициализация MessageManager с использованием тестовой базы данных
        cls.message_manager = MessageManager(MessageManagerTests)
        cls.message_manager.engine = engine
        cls.message_manager.Session = sessionmaker(bind=cls.connection)

        # Выводим список таблиц
        log_tables_in_database(engine)

    @classmethod
    def tearDownClass(cls):
        # Закрываем соединение с базой данных
        cls.session.close()
        cls.connection.close()

    def setUp(self):
        # Очищаем буфер перед каждым тестом
        self.message_manager.message_buffer.clear()

    def test_add_message_to_buffer(self):
        # Создаем тестовые данные для сообщения
        test_message = {
            'table': 'arena_chat_message',
            'data': {
                'user_id': 1,
                'content': 'Test arena message',
                'timestamp': '2024-09-10 12:00:00',
                'sender': 'fighter',
                'name': 'Test Fighter',
                'arena_id': 1,
                'read_status': False
            }
        }

        # Добавляем сообщение в буфер
        self.message_manager.add_message_to_buffer(test_message)

        # Проверяем, что сообщение добавлено в буфер
        self.assertEqual(len(self.message_manager.message_buffer), 1)
        self.assertEqual(self.message_manager.message_buffer[0]['data']['content'], 'Test arena message')

    def test_save_messages_to_db(self):
        # Создаем тестовые данные для сообщения
        test_message = {
            'table': 'arena_chat_message',
            'data': {
                'user_id': 1,
                'content': 'Test arena message',
                'timestamp': '2024-09-10 12:00:00',
                'sender': 'fighter',
                'name': 'Test Fighter',
                'arena_id': 1,
                'read_status': False
            }
        }

        # Добавляем сообщение в буфер
        self.message_manager.add_message_to_buffer(test_message)

        # Логируем содержимое буфера перед записью
        logger.info(f"Попытка сохранить {self.message_manager.message_buffer} сообщений из буфера.")
        
        # Сохраняем сообщения в базу данных
        try:
            self.message_manager.save_messages_to_db()
            logger.info("Сообщения успешно сохранены в базу данных")
        except Exception as e:
            logger.error(f"Ошибка при сохранении сообщений: {e}")

        # Проверяем, что сообщение сохранено в базе данных
        saved_message = self.session.query(ArenaChatMessage).first()
        self.assertIsNotNone(saved_message)
        self.assertEqual(saved_message.content, 'Test arena message')

    def test_mark_message_as_read(self):
        # Сначала добавляем тестовое сообщение в базу данных
        test_message = ArenaChatMessage(
            user_id=1,
            content="Test arena message",
            timestamp=datetime.now(),
            sender="fighter",
            name="Test Fighter",
            arena_id=1,
            read_status=False
        )
        self.session.add(test_message)
        self.session.commit()

        # Теперь отмечаем сообщение как прочитанное
        self.message_manager.mark_message_as_read(user_id=1, message_id=test_message.id)

        # Проверяем, что статус сообщения обновился
        read_status = self.session.query(ArenaChatMessage).filter_by(id=test_message.id).first()
        self.assertTrue(read_status.read_status)


def log_tables_in_database(engine):
    """Выводим список всех таблиц в базе данных"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if tables:
        print("Tables in the database:")
        for table in tables:
            print(f" - {table}")
    else:
        print("No tables found in the database.")


if __name__ == '__main__':
    unittest.main()
