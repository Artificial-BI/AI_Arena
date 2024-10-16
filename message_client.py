import asyncio
import pickle
from config import Config
import time
import logging 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Transport:
    action = None
    channel = None
    message_type = None
    message_id = None
    message_time = None
    message = None
    
    def __init__(self, action, channel, message_type, message_id, message_time, message):
        self.action = action
        self.channel = channel
        self.message_type = message_type
        self.message_id = message_id
        self.message_time = message_time
        self.message = message

class MessageClient:
    def __init__(self):
        self.config = Config()
        self.host = self.config.MESS_HOST
        self.port = self.config.MESS_PORT

    async def make_transport(self, action, channel, message_box=None):
        """Формирование контейнера сообщения."""
        return {
            'action': action,
            'channel': channel,
            'time': self.cur_tm(),
            'message_box': message_box
        }
    # 'new_character = Character(
    #        name=name,
    #        description=description,
    def transport_extraction(self, message_box):
        #print('CLIENT MESSAGE BOX:',message_box)
        if isinstance(message_box, dict):
            transport =Transport(
            action = message_box['action'],
            channel = message_box['channel'],
            message_type = message_box['message_type'],
            message_id = message_box['message_id'],
            message_time = message_box['time'],
            message = message_box['message']
            )
            return transport
        else:
            logger.error(f'transport type error! {type(message_box)}')
        return {'message_box':f'transport type error! {type(message_box)}'}

    def cur_tm(self):
        """Текущая метка времени."""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    async def send_message(self, transport):
        """Отправка сообщения на сервер."""
        reader, writer = await asyncio.open_connection(self.host, self.port)
        serialized_message = pickle.dumps(transport)
        writer.write(len(serialized_message).to_bytes(8, 'big'))
        writer.write(serialized_message)
        await writer.drain()

        # Получаем ответ от сервера
        raw_size = await reader.read(8)
        size = int.from_bytes(raw_size, 'big')
        response = await reader.read(size)
        response = pickle.loads(response)

        writer.close()
        await writer.wait_closed()
        return self.transport_extraction(response)
    
   # ---------------- 
    async def subscribe_channel(self, channel_name, callback):
        """Подписка на канал и обработка сообщений через callback."""
        reader, writer = await asyncio.open_connection(self.host, self.port)

        message_box = await self.make_transport("SUBSCRIBE", channel_name)
        serialized_message = pickle.dumps(message_box)
        writer.write(len(serialized_message).to_bytes(8, 'big'))
        writer.write(serialized_message)
        await writer.drain()

        response = None
        while True:
            raw_size = await reader.read(8)
            if not raw_size:
                break
            size = int.from_bytes(raw_size, 'big')
            response = await reader.read(size)
            data = pickle.loads(response)
            resp_data = self.transport_extraction(data)
            # Проверка, является ли callback корутиной
            if asyncio.iscoroutinefunction(callback):
                await callback(resp_data)  # Если это корутина, используем await
            else:
                callback(resp_data)  # Если это обычная функция, просто вызываем её

        writer.close()
        await writer.wait_closed()
        return self.transport_extraction(response)

    async def subscribe(self, channel, callback):
        """Подписка на канал с использованием callback."""
        resp = await self.subscribe_channel(channel, callback)
        return resp
    # --------------

    async def create_channel(self, channel="default"):
        """Создание канала на сервере."""
        message_box = await self.make_transport("CREATE_CHANNEL", channel)  # Ожидаем результат корутины
        resp = await self.send_message(message_box)
        return resp

    async def send(self, message, channel="default"):
        """Отправка сообщения в канал."""
        message_box = await self.make_transport("SEND", channel, message)
        resp = await self.send_message(message_box)
        return resp

    async def get_channels(self):
        message_box = await self.make_transport("GET_CHANNELS", None)
        resp = await self.send_message(message_box)
        return resp
        
    async def get_message(self, channel="default", message_id=None):
        """Получение сообщения по ID или последнего сообщения в канале."""
        message_box = await self.make_transport("GET_MESSAGE", channel, {"message_id": message_id})
        resp = await self.send_message(message_box)
        return resp

    async def get_messages(self, channel="default"):
        """Получение всех сообщений в канале."""
        message_box = await self.make_transport("GET_MESSAGES", channel)
        resp = await self.send_message(message_box)
        return resp
    
    async def clear_messages(self, channel="default"):
        """Очистка канала на сервере."""
        message_box = await self.make_transport("CLEAR_MESSAGES", channel)
        resp = await self.send_message(message_box)
        return resp


#===================================== TEST ===========================================================

def test_callback(response):
    print('v------------------------v')
    print('test_callback:', response)
    print('^------------------------^')

async def make_subscribe(client):
    """Асинхронная версия подписки."""
    resp = await client.subscribe("test_channel", test_callback)
    print(f'make_subscribe: {resp}\n')

async def test_cicle(client):
    """Асинхронная версия тестового цикла."""
    # Создание канала
    resp = await client.create_channel("test_channel")
    print(f'resp: {resp}\n')

    for num in range(5):
        if num == 0:
            for num1 in range(3):
                resp = await client.send(f"тестовое сообщение! {num1}", "test_channel")
                print(f'send: {resp}\n')
        elif num == 1:
            # Получение последнего сообщения
            resp = await client.get_message("test_channel")
            print(f'get_message: {resp}\n')
        elif num == 2:
            resp = await client.get_messages("test_channel")
            print(f'get_messages: {resp}\n')
        elif num == 3:
            resp = await client.clear_messages("test_channel")
            print(f'clear_messages: {resp}\n')    
        elif num == 4:
            resp = await client.send(f"контрольное сообщение! {num1}", "test_channel")
            print(f'send: {resp}\n')

        await asyncio.sleep(4)

# Пример использования клиента
if __name__ == "__main__":
    client = MessageClient()
    loop = asyncio.get_event_loop()

    # Запускаем подписку и цикл тестирования
    loop.run_until_complete(make_subscribe(client))
    # loop.run_until_complete(test_cicle(client))
