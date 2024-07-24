import google.generativeai as genai
from config import Config

class GeminiAssistant:
    def __init__(self, role_instructions):
        conf = Config()
        genai.configure(api_key=conf.GEMINI_API_TOKEN)
        self.model = genai.GenerativeModel(
            'gemini-1.5-flash',
            system_instruction=role_instructions
        )
        self.chat = self.model.start_chat(history=[])

    async def send_message(self, msg):
        response = await self.chat.send_message_async(msg)
        if response and response.candidates:
            return response.candidates[0].content.parts[0].text
        else:
            return "Sorry, I couldn't understand your message."
