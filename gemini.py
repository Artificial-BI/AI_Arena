import google.generativeai as genai
from config import Config
import logging
import json

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
    def __init__(self, role_instructions_file):
        self.chat_history = ChatMessageHistory()
        
        # Загрузка инструкции роли из JSON файла
        with open(role_instructions_file, 'r') as file:
            role_data = json.load(file)
            role_instructions = role_data.get('system_instruction', '')
        
        conf = Config()
        genai.configure(api_key=conf.GEMINI_API_TOKEN)
        self.model = genai.GenerativeModel(
            'gemini-1.5-flash',
            system_instruction=role_instructions
        )
        self.chat = self.model.start_chat(history=[])
        logger.info("GeminiAssistant initialized with instructions from JSON file")

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

# Пример использования
# assistant = GeminiAssistant('role_instructions.json')
# response = asyncio.run(assistant.send_message("Generate a new character for the arena."))
# print(response)
