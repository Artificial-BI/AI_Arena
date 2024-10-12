# status_manager.py

import asyncio
import logging
import zmq.asyncio
import time
from datetime import datetime
from config import Config
from message_client import MessageClient
# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StatusManager:
    def __init__(self):
        self.client = MessageClient()
        self.status_list = ['arena','game', 'battle', 'error', 'users', 'timer', 'characters','registred', 'battle_process']
        self.conf = Config()
        self.states = {}

    def newTM(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    async def get_name_statuses(self):
        message_box = await self.client.get_channels()
        stats = await self.box_extraction(message_box)
        stat_name_list = []
        if stats:
            for stat in stats:
                if 'chat' not in stat: 
                    stat_name_list.append(stat)
        return stat_name_list

    async def create_status(self, name):
        res = await self.client.create_channel(name)
        stat = await self.box_extraction(res)
        return stat
        
    async def create_status_channels(self):
        for name in self.status_list:
            await self.client.create_channel(name)

    def make_status(self, name, status):
        return {"name":name, "status": status, "timestamp": time.time()}

    async def box_extraction(self, transport):
        message_box = transport.message
        #print('transport message_box:',transport.channel, type(message_box), message_box)
        if message_box:
            if isinstance(message_box, dict):
                #print('statust dict:',transport.channel, message_box)
                mes = message_box.get('message')
                if mes:
                    status = mes['status']
                else:    
                    status = message_box['status']
                return status
            else:
                #print('message_box message_box:',transport.channel, message_box)
                return message_box
        else:
            return None    

    async def channel_extraction(self, name):
        message_box = await self.client.get_message(name)
        res = await self.box_extraction(message_box)
        if res:
            return res
        
    async def get_all_statuses(self):
        list_state = []
        for name in self.status_list:
            response = await self.client.get_message(name)
            name_stat = await self.box_extraction(response)
            #print('name_stat:',name,name_stat)
            list_state.append({'name':name,'status':name_stat})
        return list_state

    async def get_statuses(self, name):
        response = await self.client.get_messages(name)
        stats = self.box_extraction(response)
        if stats:
            return stats
    
    async def status_subscribe(self, name, callback):
        resp = await self.client.subscribe(name, callback)
        res = await self.box_extraction(resp)  
        if res:
            return res 

    async def subscribe_statuses(self, channels):
        """Подписываемся на каналы в фоновом режиме, используя asyncio.create_task."""
        tasks = []
        for channel in channels:
            # Создаём задачу для каждой подписки
            task = asyncio.create_task(self.status_subscribe(channel, channels[channel]))
            tasks.append(task)

        # Выполняем подписку на все статусы параллельно, но не блокируем приложение
        await asyncio.gather(*tasks)   

    async def set_status(self, name, status):
        status_box = self.make_status(name, status)
        resp = await self.client.send(status_box, name)
        res = await self.box_extraction(resp)
        #print('stat set_status:',res)
        return res

    async def get_status(self, name):
        message_box = await self.client.get_message(name)
       # print('get_status message_box:',message_box)
        status = await self.box_extraction(message_box)
        #print('stat status:',status)
        return status
       
    async def init_statuses(self):
        for name in self.status_list:
            res = await self.set_status(name, 'init')
            #logger.init(f'init: {res}')
        
        # await self.set_status('characters', 'init')
        # await self.set_status('arena', 'init')
        # await self.set_status('timer', 0)
        # await self.set_status('battle', 'init')
        # await self.set_status('battle_process', False)
        # await self.set_status('error', 'init')

