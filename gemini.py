import google.generativeai as genai

class GeminiAssistant:
    def __init__(self, gemini_api_key, role_instructions):
        genai.configure(api_key=gemini_api_key)
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


