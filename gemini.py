import google.generativeai as genai
from config import Config
import logging
import json
from models import Role
from extensions import db

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatMessageHistory:
    def __init__(self):
        self.messages = []

    def add_user_message(self, message):
        self.messages.append({"role": "user", "content": message})

    def add_ai_message(self, message):
        self.messages.append({"role": "assistant", "content": message})

    def get_history(self):
        return self.messages

class GeminiAssistant:
    def __init__(self, role_name):
        self.chat_history = ChatMessageHistory()

        # Загрузка инструкции роли из базы данных
        role = Role.query.filter_by(name=role_name).first()
        if role:
            role_instructions = {f"system_instruction: {role.instructions}"}
            logger.info(f"Loaded instructions for role: {role_name}")
        else:
            role_instructions = ''
            logger.warning(f"No instructions found for role: {role_name}")

        conf = Config()
        genai.configure(api_key=conf.GEMINI_API_TOKEN)
        self.model = genai.GenerativeModel(
            'gemini-1.5-flash',
            system_instruction=role_instructions
        )
        self.chat = self.model.start_chat(history=[])
        logger.info("GeminiAssistant initialized with instructions from database")

    async def send_message(self, msg):
        logger.info(f"Sending message: {msg}")
        self.chat_history.add_user_message(msg)
        response = await self.chat.send_message_async(msg)
        if response and response.candidates:
            result = response.candidates[0].content.parts[0].text
            self.chat_history.add_ai_message(result)
            logger.info(f"Received response: {result}")
            return result
        else:
            logger.error("No response received")
            return "Sorry, I couldn't understand your message."
        

