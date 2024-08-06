import google.generativeai as genai
from config import Config
import logging
import json
from models import Role
import asyncio
import time

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

class GeminiAssistant:
    def __init__(self, role_instructions, use_history=False):
        self.chat_history = []
        self.use_history = use_history
        conf = Config()
        genai.configure(api_key=conf.GEMINI_API_TOKEN)
        self.model = genai.GenerativeModel(
            'gemini-1.5-flash',
            system_instruction=role_instructions
        )
        self.chat = self.model.start_chat(history=[])
        #logger.info("GeminiAssistant initialized with instructions from database")

    async def send_message(self, msg, max_retries=5):
        self.chat_history.append({"role": "user", "content": msg})
        
        retries = 0
        while retries < max_retries:
            try:
                response = await self.chat.send_message_async(msg)
                
                if response and response.candidates:
                    result = response.candidates[0].content.parts[0].text
                    self.chat_history.append({"role": "assistant", "content": result})
                    return result
                else:
                    logger.error("No response received")
                    return "Sorry, I couldn't understand your message."
            except Exception as e:
                if "429" in str(e):
                    retries += 1
                    logger.warning(f"429 Too Many Requests. Retry {retries}/{max_retries}")
                    await asyncio.sleep(2 ** retries)  # Exponential backoff
                else:
                    logger.error(f"Error in send_message: {e}")
                    raise e
        raise Exception("Exceeded maximum retry attempts for send_message")
