
#=========================================================================
import logging
import asyncio
import pickle
import uuid
import time
import os
from config import Config
from utils import set_glob_var

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageServer:
    def __init__(self):
        self.config = Config()
        self.host = self.config.MESS_HOST
        self.port = self.config.MESS_PORT
        self.stop_event = None
        self.channels = {}
        self.is_running = True
        self.server_statue = False

    def create_channel(self, channel_name):
        if channel_name not in self.channels:
            self.channels[channel_name] = {"subscribers": [], "messages": []}
            #print(f"Канал {channel_name} создан.")

    def subscribe_to_channel(self, channel_name, writer):
        if channel_name in self.channels:
            if writer not in self.channels[channel_name]["subscribers"]:
                self.channels[channel_name]["subscribers"].append(writer)
                #print(f"Подписка на канал {channel_name} успешна.")

    async def send_message_to_channel(self, channel_name, message):
        if channel_name in self.channels:
            self.channels[channel_name]["messages"].append(message)
            
           # logger.info(f"в канал: {channel_name} count: {len(self.channels[channel_name])}")
            #logger.info(f"в канал: {channel_name} add: {self.channels[channel_name]} |mes: ({message})")
            # for chan in self.channels[channel_name]["messages"]:
            #     logger.info(f"--- chan: {chan}")
            
            for subscriber in self.channels[channel_name]["subscribers"]:
                try:
                    await self.message_writer(subscriber, message)
                except Exception as e:
                    logger.error(f"Ошибка при отправке сообщения подписчику: {e}")
        else:
            logger.warning(f"Канал: {channel_name} не найден.")

    # если пришло новое сообщение, то отправляем в канал все сообщения (для обновления чатов)
    async def send_all_message_to_channel(self, channel_name, new_message):
        if channel_name in self.channels:
            self.channels[channel_name]["messages"].append(new_message)
            for subscriber in self.channels[channel_name]["subscribers"]:
                try:
                    messages = self.channels[channel_name]["messages"]
                    await self.message_writer(subscriber, messages)
                except Exception as e:
                    logger.error(f"Ошибка при отправке списка сообщений подписчику {subscriber} -: {e}")
        else:
            logger.warning(f"Канал: {channel_name} не найден.")

    async def clear_messages(self, channel_name):
        self.channels[channel_name]["messages"].clear()
        return len(self.channels[channel_name]["messages"])

    async def get_messages(self, channel_name):
        if channel_name in self.channels:
            channel_messages = self.channels[channel_name]["messages"]
            message_list = []
            for message_box in channel_messages:
                if message_box['message'] != []:
                    message_list.append(message_box)
            #print('channels_messages - >>:',message_list)
            return message_list
        else:
            return f'no channel: {channel_name}'

    async def get_channels(self):
        channels = []
        for key in self.channels.keys():
            channels.append(key)
        return channels

    async def get_message(self, channel_name):
        #print('--SERVER -1:',channel_name,'>>',self.channels.keys())
        if channel_name in self.channels.keys():
            count = len(self.channels[channel_name]["messages"])
            if count > 0:
                resp = self.channels[channel_name]["messages"][-1]
               # print('SERVER get mess:',channel_name, '|',resp.get("message"), resp)
                if resp.get("message"):
                    return resp
        return None

    def make_transport(self, message_type, message_time, message_box):
        return {
            'message_type': message_type,
            'message_id': str(uuid.uuid4()),
            'time': message_time,
            'message': message_box
        }

    def response_transport(self, channel, message, message_type):
        return {
            'action': 'response',
            'channel': channel,
            'message_type': message_type,
            'message_id': str(uuid.uuid4()),
            'time': self.cur_tm(),
            'message': message
        }

    def cur_tm(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    async def message_reader(self, reader):
        raw_size = await reader.read(8)
        if raw_size:
            size = int.from_bytes(raw_size, 'big')
            response = await reader.read(size)
            return pickle.loads(response)
        return None

    async def message_writer(self, writer, message):
        serialized_message = pickle.dumps(message)
        writer.write(len(serialized_message).to_bytes(8, 'big'))
        writer.write(serialized_message)
        await writer.drain()

    async def handle_client(self, reader, writer):
        message_content = ""
        try:
            while not self.stop_event.is_set():
                transport = await self.message_reader(reader)
                if not transport or not self.is_running:
                    break
                action = transport.get("action")
                if action == "CREATE_CHANNEL":
                    channel_name = transport.get("channel")
                    self.create_channel(channel_name)
                    response = self.response_transport(channel_name, f"Канал {channel_name} создан.",  type(""))
                    await self.message_writer(writer, response)
                
                elif action == "SUBSCRIBE":
                    channel_name = transport.get("channel")
                    self.subscribe_to_channel(channel_name, writer)
                    response = self.response_transport(channel_name, f"Подписка на {channel_name} успешна.",  type(""))
                    await self.message_writer(writer, response)
                
                # подписчикам отправляется последнее сообщение из канала
                elif action == "SEND":
                    channel_name = transport.get("channel")
                    message_time = transport.get("time")
                    message_content = transport.get("message_box")
                    message_box = self.make_transport(transport.get("message_type"), message_time, message_content)
                    #print(message_content,'--->>> ',message_box)
                    await self.send_message_to_channel(channel_name, message_box)
                    response = self.response_transport(channel_name, "Сообщение отправлено.", type(""))
                    await self.message_writer(writer, response)
                
                # подписчикам отправляются все сообщения из канала
                elif action == "SEND_ALL":
                    channel_name = transport.get("channel")
                    message_time = transport.get("time")
                    message_content = transport.get("message_box")
                    message_box = self.make_transport(transport.get("message_type"), message_time, message_content)
                    await self.send_all_message_to_channel(channel_name, message_box)
                    response = self.response_transport(channel_name, "Сообщение отправлено.", type(""))
                    await self.message_writer(writer, response)

                elif action == "GET_CHANNELS": # channel list
                    channels = await self.get_channels()
                    #print('channels:',channels)
                    response = self.response_transport('channel list', channels, type([]))
                    await self.message_writer(writer, response)

                elif action == "GET_MESSAGES":
                    channel_name = transport.get("channel")
                    messages = await self.get_messages(channel_name)
                    response = self.response_transport(channel_name, messages, type([]))
                    await self.message_writer(writer, response)

                elif action == "GET_MESSAGE":
                    channel_name = transport.get("channel")
                    message_content = await self.get_message(channel_name)
                    #print('SERVER:',channel_name, message_content)
                    response = self.response_transport(channel_name, message_content, type(message_content))
                    #print('SERVER1:',response)
                    await self.message_writer(writer, response)

                elif action == "CLEAR_MESSAGES":
                    channel_name = transport.get("channel")
                    message_count = await self.clear_messages(channel_name)
                    response = self.response_transport(channel_name, f"Канал очищен, {message_count} сообщений удалено.", type(""))
                    await self.message_writer(writer, response)

                elif action == "STOP":
                    await self.shutdown()
                    response = self.response_transport("server", "Сервер остановлен.",  type(""))
                    await self.message_writer(writer, response)

                else:
                    response = self.response_transport("unknown", "Неизвестная команда.",  type(""))
                    await self.message_writer(writer, response)

        except Exception as e:
            logger.error(f"Ошибка [{action}] при обработке клиента: {e}")
            logger.error(f"Подробности - message: {message_content} | response: {response}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def shutdown(self):
        self.is_running = False
        logger.info("Сервер остановлен.")

    async def start(self, stop_event):
        self.stop_event = stop_event
        while not stop_event.is_set():
            try:
                server = await asyncio.start_server(self.handle_client, self.host, self.port)
                #server = await asyncio.start_server(lambda r, w: self.handle_client(r, w, stop_event), self.host, self.port)
                async with server:
                    logger.info(f"Сервер сообщений запущен на {self.host}:{self.port}")
                    await server.serve_forever()
                    self.config.MESS_PORT = self.port
                    break
            except OSError as e:
                if "[Errno 10048]" in str(e):
                    set_glob_var('flask', False)
                    logger.warning(f"MessageServer уже запущен.")
                    #self.port += 1  # Увеличиваем порт на 1 и пробуем снова
                    break
                else:
                    logger.error(f"Ошибка при запуске MessageServer: {e}")
                    break

async def startMessagesServer(stop_event):
    server = MessageServer()
    await server.start(stop_event)
    #asyncio.run(server.start())
