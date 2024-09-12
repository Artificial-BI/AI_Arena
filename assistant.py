# gpt-4-turbo
# gpt-4-turbo 
# gpt-4-32k-turbo 
# gpt-4o-mini-2024-07-18

# --- assistant.py ---
import logging
import json
import asyncio
import tiktoken
import random
import google.generativeai as genai
from openai import RateLimitError, APIError 
from openai import AsyncOpenAI
#from openai import OpenAI

from config import Config
from models import Role

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Assistant:
    def __init__(self, role_name, use_history=False):
        self.chat_history = []
        self.use_history = use_history
        self.conf = Config()
        self.instructions = self.get_instructions(role_name)
        self.role_name = role_name
        self.old_request = ""

    async def send_message(self, message, assistant, max_retries=6):
        if self.conf.DEBUG:
            debug_mess = ['какие то данные', 'случайный выбор', 'неопределенно', 'эотносительно отладки', ' это письмо ', 'Рассылки',' письма точнее','С учетом позиции','Также на счету','есть консерванты','вкус другой','Качество продуктов высокое','Почта учится','в начале августа' ]
            rnd_mess = random.choice(debug_mess)
            return f"Заглушка assistant DEBUG MODE: {assistant}\n role: {self.role_name}\n send count: {len(message)}\n RETURN: {rnd_mess} ."
        else:
            retries = 0
            while retries < max_retries:
                try:
                    result = await self.selectAssistant(assistant, message) 
                    return result
                except Exception as e:
                    logger.error(f"Ошибка API: {assistant}: {e}")
                    return str(e)
            raise Exception("Exceeded maximum retry attempts for send_message")

    async def selectAssistant(self, assistant, message):
        await asyncio.sleep(5)

        if assistant == 'auto':
            if self.old_request == 'gemini':
                assistant = 'chatgpt'
            elif self.old_request == 'chatgpt': 
                assistant = 'gemini'
            else:
                choices = ['chatgpt', 'gemini']
                assistant = random.choice(choices)
     
        if assistant == 'gemini':
            ga = GeminiAssistant(self.instructions)
            response = await ga.send_message(message)  
        elif assistant == 'chatgpt': 
            cgpt = ChatGPTAssistant(self.instructions)
            response = await cgpt.send_message(message) 
        
        self.old_request =  assistant 
        return response

    def get_instructions(self, role_name):
        try:
            role = Role.query.filter_by(name=role_name).first()
            if role:
                return role.instructions
            else:
                return ""
        except Exception as e:
            logger.error(f"Error fetching instructions: {e}")
            return ""

class GeminiAssistant:
    def __init__(self, role_instructions):
        self.conf = Config()
        genai.configure(api_key=self.conf.GEMINI_API_TOKEN)
        self.model = 'gemini-1.5-flash'
        self.client = genai.GenerativeModel(
            self.model,
            system_instruction=role_instructions
        )
        self.chat = self.client.start_chat(history=[])

    async def send_message(self, msg):
        try:
            response = await self.chat.send_message_async(msg)
            if response and response.candidates:
                result = response.candidates[0].content.parts[0].text
                return result
            else:
                logger.error(f"Error {self.model} NONE")  
                return None
        except Exception as e:        
            if "429" in str(e):
                logger.error(f"Error {self.model} NONE")
                return None
            else:
                logger.error(f"Error {self.model} fetching instructions: {e}")
                return None
            

class ChatGPTAssistant:
    def __init__(self, role_instructions):
        self.conf = Config()
        self.instructions = role_instructions
        self.client = AsyncOpenAI(api_key=self.conf.OPENAI_API_KEY)
        self.model = "gpt-4o-mini-2024-07-18"  # либо "gpt-4-turbo"

    async def send_message(self, msg):
        messages = self.convert_role(msg)
        if messages is not None:
            try:
                # Правильное использование API
                response = await self.client.chat.completions.create(
                    model=self.model, 
                    messages=messages
                )
                # Доступ через атрибут 'content', а не как к словарю
                result =  response.choices[0].message.content.strip()
                return result
            except RateLimitError as e:
                logger.warning(f"Превышение лимита запросов {self.model}. {e} ")
                return None
            except APIError as e:
                logger.error(f"Ошибка {self.model} в send_message: {e}")
                return None
        else:
            logger.error(f"Error: пустой запрос: {messages}")
            return None

#---------------------------------------------------------------------------

    def convert_role(self, message):
        instruction = self.instructions
        role = [
            {"role": "system", "content": f"{instruction}"},
            {"role": "user", "content": "quest"},
            {"role": "assistant", "content": "answer"},
            {"role": "user", "content": f"{message}"}
        ]
        return role