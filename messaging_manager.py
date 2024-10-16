import threading
import asyncio
import time
import logging
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from chats_models import GeneralChatMessage, Base
from config import Config
from datetime import datetime
from status_manager import StatusManager
from message_client import MessageClient, Transport
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatArena:
    message = None
    sender = None
    user_id = None
    arena_id = None
    name = None

    def __init__(self, message, sender, user_id, arena_id, name):
        self.message = message
        self.sender = sender
        self.user_id = user_id
        self.arena_id = arena_id
        self.name = name

class ChatTactic:
    message = None
    sender = None
    user_id = None
    
    def __init__(self, message, sender, user_id):
        message = message,
        sender = sender,
        user_id = user_id,

class MessageManager:
    def __init__(self):
        self.conf = Config()
        self.sm = StatusManager()
        self.client = MessageClient()
        #self.ccom = core_com
        self.engine = create_engine(self.conf.MESSAGES_DB)
        # Initialize database
        self.initialize_database()

    async def box_extraction(self, transport):
        #print('MM transport:',transport)
        if isinstance(transport, Transport):
            message_box = transport.message
           # print('MM message_box:',type(message_box), message_box)
            if message_box:
                if isinstance(message_box, dict):
                    mess = message_box.get('message')
                    if isinstance(mess, dict):
                        mess = mess['message']
                    return mess
                elif isinstance(message_box, list):
                    mess = message_box
                    return mess
        else:
            message_box = transport
        return message_box    

    async def get_list_extract(self, messages):
        res_list = []
        for mess in messages:
            if isinstance(mess, dict):
                res = mess['message']
                res_list.append(res)
            else:
                res_list.append(mess)    
        return res_list        
    
    async def to_chatArena(self, message, sender, user_id, arena_id, name):
        chatMess =ChatArena(
            message = message,
            sender = sender,
            user_id = user_id,
            arena_id = arena_id,
            name = name
            )
        return chatMess
    
    async def get_chatArena(self, chat_mess):
        if isinstance(chat_mess, ChatArena):
            message_box = {
                "message": chat_mess.message,
                "sender": chat_mess.sender,
                "user_id": chat_mess.user_id,
                "arena_id": chat_mess.arena_id,
                "name": chat_mess.name
            }
        return message_box

    #======================================================
    async def create_channel_message(self, channel):
        response = await self.client.create_channel(channel)
        return await self.box_extraction(response)

    async def create_message_channels(self):
        channel_list = ['arena_chat', 'general_chat']
        for channel in channel_list:
            resp = await self.client.create_channel(channel)
            res = await self.box_extraction(resp)
            logger.info(f'{channel}: {res}')

    async def subscribe_messagess(self, channels):
        """Подписываемся на каналы в фоновом режиме, используя asyncio.create_task."""
        tasks = []
        for channel in channels:
            # Создаём задачу для каждой подписки
            resp = asyncio.create_task(await self.client.subscribe(channel, channels[channel]))
            task = await self.box_extraction(resp)       
            tasks.append(task)
    
    async def send_message(self, name, message):
        resp = await self.client.send(message, name)
        return await self.box_extraction(resp)
                
    async def get_message(self, name):
        message_box = await self.client.get_message(name)
        return await self.box_extraction(message_box)
    
    async def get_messages(self, name):
        response = await self.client.get_messages(name)
        messages = await self.box_extraction(response)
        mess_list = []
       # print('get_messages:',type(messages),messages)
        if isinstance(messages, list): 
            for message_box in messages:
                message = await self.box_extraction(message_box)
                mess_list.append(message)
        else:
            return messages       
        return mess_list    

    async def get_name_channels(self):
        response = await self.client.get_channels()
        channels = await self.box_extraction(response)
        return channels

    async def general_callback(self, response):
        print('general_callback:',response)

    async def message_subscribes(self):
        resp = asyncio.create_task(await self.client.subscribe('general_chat', self.general_callback))
        return await self.box_extraction(resp) 
    
#----------------------------------------------------------------------------------

    async def message_to_Arena(self, message, sender, arena_id, user_id, name):
       
        message_box = await self.to_chatArena(message, sender, user_id, arena_id, name)
        await self.send_message('arena_chat', message_box)

    async def get_message_chatArena(self, sender, arena_id, user_id):
        resp = await self.get_message('arena_chat')
        if isinstance(resp, dict):
            mess_box = await self.box_extraction(resp) 
            if isinstance(mess_box, dict):
                chat_box = mess_box['message']
                if isinstance(chat_box, ChatArena):
                    if sender != None:
                        if sender not in chat_box.sender:
                            return ''
                    if arena_id != None:
                        if arena_id not in chat_box.arena_id:
                            return ''          
                    if user_id != None:
                        if user_id not in chat_box.user_id:
                            return ''
       
    async def get_all_message_chatArena(self, sender, arena_id, user_id):
        res_list = []
        message_list = await self.get_messages('arena_chat')    
        for message_box in message_list:
            if isinstance(message_box, dict):
                mess_box = await self.box_extraction(message_box) 
                if isinstance(mess_box, dict):
                    chat_box = mess_box['message']
                    if isinstance(chat_box, ChatArena):
                        if sender != None:
                            if sender not in chat_box.sender:
                                continue
                        if arena_id != None:
                            if arena_id not in chat_box.arena_id:
                                continue          
                        if user_id != None:
                            if user_id not in chat_box.user_id:
                                continue
                            
                        res_list.append(chat_box.message)
        return res_list
    
    #--------------------------------------------------------------------------
    async def message_to_GeneralChat(self, message, sender, user_id):
        message_box = {
                "message": message,
                "sender": sender,
                "user_id": user_id
            }
        await self.send_message('general_chat', message_box)

    async def get_message_GeneralChat(self, sender, user_id):
        res_list = []
        message_list = await self.get_messages('general_chat')    
        for message_box in message_list:
            mess_box = await self.box_extraction(message_box) 
            if sender != None:
                if sender not in mess_box:
                    continue  
            if user_id != None:
                if user_id not in mess_box:
                    continue
            res_list.append(mess_box)
        print('GeneralChat:',res_list)
        return res_list
        
        
    async def get_all_message_GeneralChat(self, sender, user_id):
        res_list = []
        message_list = await self.get_messages('general_chat')    
        for message_box in message_list:
            mess_box = await self.box_extraction(message_box) 
            if sender != None:
                if sender not in mess_box:
                    continue  
            if user_id != None:
                if user_id not in mess_box:
                    continue
            res_list.append(mess_box)
            
        print('All GeneralChat:',res_list)
            
        return res_list   
    #--------------------------------------------------------------------------
    async def message_to_Tactics(self, message, sender, user_id):
        chatMess = ChatTactic(
            message = message,
            sender = sender,
            user_id = user_id,
            )
        res = await self.send_message(f'chat_{user_id}', chatMess)
        print('to_Tactics:',res)

    async def get_message_chatTactic(self, sender, user_id):
        message_box = await self.get_messages(f'chat_{user_id}')  
        res = '' 
        if isinstance(message_box, dict):
            mess_box = await self.box_extraction(message_box)      
            if isinstance(mess_box, dict):
                chat_box = mess_box['message']
                if isinstance(chat_box, ChatArena):    
                    if sender != None:
                        if sender not in chat_box.sender:  
                            return ''
                        else:
                            res = chat_box.message
        return res
    
    async def get_all_message_chatTactics(self, sender, user_id):
        res_list = []
        message_list = await self.get_messages(f'chat_{user_id}') 
        print('>>> all chatTactics:',type(message_list),message_list) 
        if isinstance(message_list, list):   
            for message_box in message_list:
                mess_box = await self.box_extraction(message_box) 
                if isinstance(mess_box, dict):
                    chat_box = mess_box['message']
                    if isinstance(chat_box, ChatArena):    
                        if sender != None:
                            if sender in chat_box.sender:  
                                res_list.append(chat_box.message)
                        else:
                            res_list.append(chat_box.message)
  
        return res_list

#---------------------------------------------------------------------------    
    def initialize_database(self):
        inspector = inspect(self.engine)
        if not inspector.has_table(GeneralChatMessage.__tablename__):
            Base.metadata.tables[GeneralChatMessage.__tablename__].create(self.engine)
            logger.info(f"Table '{GeneralChatMessage.__tablename__}' created.")
            
        # await self.box_extraction(resp)  
        



    
    