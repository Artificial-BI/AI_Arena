import google.generativeai as genai
from config import Config
import logging
import json
from models import Role

# Configure logging
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

# gemini.py
class GeminiAssistant:
    def __init__(self, role_name, use_history=False):
        self.chat_history = []
        self.use_history = use_history

        role = Role.query.filter_by(name=role_name).first()
        if role:
            role_instructions = f"system_instruction: {role.instructions}"
            logger.info(f"Loaded instructions for role: {role_name}")
        else:
            try:
                with open('default_role.json', 'r', encoding='utf-8') as file:
                    role_data = json.load(file)
                    role_instructions = role_data.get(role_name, '')
                    if role_instructions:
                        logger.info(f"Loaded instructions for role from JSON file: {role_name}")
                    else:
                        logger.warning(f"No instructions found for role in JSON file: {role_name}")
            except FileNotFoundError:
                role_instructions = ''
                logger.error(f"JSON file not found: default_role.json")

        conf = Config()
        genai.configure(api_key=conf.GEMINI_API_TOKEN)
        self.model = genai.GenerativeModel(
            'gemini-1.5-flash',
            system_instruction=role_instructions
        )
        self.chat = self.model.start_chat(history=[])
        logger.info("GeminiAssistant initialized with instructions from database or JSON file")

    async def send_message(self, msg):
        logger.info(f"Sending message: {msg}")
        self.chat_history.append({"role": "user", "content": msg})
        
        response = await self.chat.send_message_async(msg)
        
        if response and response.candidates:
            result = response.candidates[0].content.parts[0].text
            self.chat_history.append({"role": "assistant", "content": result})
            logger.info(f"Received response: {result}")
            return result
        else:
            logger.error("No response received")
            return "Sorry, I couldn't understand your message."
