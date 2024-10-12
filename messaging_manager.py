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
        print('MM transport:',transport)
        if isinstance(transport, Transport):
            message_box = transport.message
            print('MM message_box dict:',transport.channel, message_box)
            if message_box:
                if isinstance(message_box, dict):
                    mess = message_box.get('message')
                    if isinstance(mess, dict):
                        mess = mess['message']
                    return mess
        else:
            message_box = transport
        return message_box    

    
    #======================================================
    async def create_channel_message(self, channel):
        response = await self.client.create_channel(channel)
        return self.box_extraction(response)

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
        print('MM name:',name,response)
        messages = await self.box_extraction(response)
        print('MM--->>:',messages)
        mess_list = []
        for message_box in messages:
            message = await self.box_extraction(message_box)
            mess_list.append(message)
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
        message_box = {
                "message": message,
                "sender": sender,
                "user_id": user_id,
                "arena_id": arena_id,
                "name": name
            }
        await self.send_message('arena_chat', message_box)

    async def get_message_chatArena(self):
        resp = self.get_message('arena_chabattle_processt')
        box_message = await self.box_extraction(resp) 
        print('box_message:', box_message)
        return box_message
    
    
    async def get_all_message_chatArena(self, sender, arena_id, user_id):
        res_list = []
        message_list = await self.get_messages('arena_chat')    
        print('>> message_list:',message_list)
        for message_box in message_list:
            mess_box = await self.box_extraction(message_box) 
            if sender != None:
                if sender not in mess_box:
                    continue  
            if arena_id != None:
                if arena_id not in mess_box:
                    continue
            if user_id != None:
                if user_id not in mess_box:
                    continue
            res_list.append(mess_box)
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
        return res_list   
    #--------------------------------------------------------------------------
    async def message_to_Tactics(self, message, sender, user_id):
        message_box = {
                "message": message,
                "sender": sender,
                "user_id": user_id,
            }
        await self.send_message(f'chat_{user_id}', message_box)

    async def get_message_chatTactics(self, sender, user_id):
        res_list = []
        message_list = await self.get_messages(f'chat_{user_id}')    
        for message_box in message_list:
            mess_box = await self.box_extraction(message_box) 
            if sender != None:
                if sender not in mess_box:
                    continue  
            res_list.append(mess_box)
        return res_list
    
    async def get_all_message_chatTactics(self, sender, user_id):
        res_list = []
        message_list = await self.get_messages(f'chat_{user_id}')    
        for message_box in message_list:
            mess_box = await self.box_extraction(message_box) 
            if sender != None:
                if sender not in mess_box:
                    continue  
            res_list.append(mess_box)
        return res_list

#---------------------------------------------------------------------------    
    def initialize_database(self):
        inspector = inspect(self.engine)
        if not inspector.has_table(GeneralChatMessage.__tablename__):
            Base.metadata.tables[GeneralChatMessage.__tablename__].create(self.engine)
            logger.info(f"Table '{GeneralChatMessage.__tablename__}' created.")
            
        # await self.box_extraction(resp)  
        



    
    