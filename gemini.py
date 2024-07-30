import asyncio
import google.generativeai as genai
from config import Config
import logging
import json
import os
import requests
from flask import Blueprint, request, jsonify
from models import Role
from extensions import db




# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask Blueprint for routes
image_bp = Blueprint('image_bp', __name__)

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
            # Если роли нет в базе данных, загружаем из JSON файла
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

import google.generativeai as genai
from config import Config
import logging
import json
import os
import requests
from flask import Blueprint, request, jsonify
from models import Role
from extensions import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask Blueprint for routes
image_bp = Blueprint('image_bp', __name__)

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

        # Load role instructions from the database
        role = Role.query.filter_by(name=role_name).first()
        if role:
            role_instructions = f"system_instruction: {role.instructions}"
            logger.info(f"Loaded instructions for role: {role_name}")
        else:
            # Load from JSON file if role not in the database
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

class GeminiDesigner:
    def __init__(self):
        conf = Config()
        genai.configure(api_key=conf.GEMINI_API_TOKEN)
        self.client = genai.Client(api_key=conf.GEMINI_API_TOKEN)
        logger.info("GeminiDesigner initialized for image generation")

    async def generate_image(self, description):
        logger.info(f"Generating image for description: {description}")
        response = self.client.text_to_image(description)
        if response and response['images']:
            image_url = response['images'][0]['url']
            logger.info(f"Generated image URL: {image_url}")
            return image_url
        else:
            logger.error("No image generated")
            return None

    def download_image(self, image_url, save_path):
        try:
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                with open(save_path, 'wb') as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                logger.info(f"Image downloaded and saved to: {save_path}")
                return save_path
            else:
                logger.error(f"Failed to download image: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return None

    async def generate_and_save_image(self, description, filename, return_type='url'):
        image_url = await self.generate_image(description)
        if image_url:
            if return_type == 'local':
                save_path = os.path.join('static', 'images', filename)
                return self.download_image(image_url, save_path)
            elif return_type == 'url':
                return image_url
            else:
                logger.error("Invalid return type specified")
                return None
        else:
            return None

# Route to test image generation
# @image_bp.route('/generate_image', methods=['POST'])
# def generate_image():
#     try:
#         data = request.get_json()
#         description = data.get('description')
#         filename = data.get('filename')
#         return_type = data.get('return_type', 'url')

#         if not description or not filename:
#             return jsonify({"error": "Description and filename are required"}), 400

#         designer = GeminiDesigner()
#         image_link = asyncio.run(designer.generate_and_save_image(description, filename, return_type))

#         if image_link:
#             return jsonify({"status": "success", "image_link": image_link}), 200
#         else:
#             return jsonify({"error": "Image generation failed"}), 500
#     except Exception as e:
#         logger.error(f"Error generating image: {e}")
#         return jsonify({"error": str(e)}), 500


# Route to test image generation
@image_bp.route('/generate_image', methods=['POST'])
def generate_image():
    try:
        # data = request.get_json()
        # description = data.get('description')
        # filename = data.get('filename')
        
        description = "Aethelred is a wizened mage of immense arcane knowledge and power. His years of study have gifted him with a mastery of elemental magic, particularly fire and ice. He wields a staff crafted from ancient oak, imbued with potent runes that amplify his spells. Though physically frail, Aethelred's intellect and magical prowess make him a formidable opponent. He is often seen as a recluse, preferring the company of his books and scrolls to that of other people. However, he is known to possess a keen mind and a sharp wit, capable of seeing through deception and manipulating situations to his advantage. His loyalty lies with those who seek knowledge and truth, and he will defend them with the full force of his magic."
        filename = 'test_img.png'
        return_type = 'url'
        #return_type = data.get('return_type', 'url')

        if not description or not filename:
            return jsonify({"error": "Description and filename are required"}), 400

        designer = GeminiDesigner()
        image_link = asyncio.run(designer.generate_and_save_image(description, filename, return_type))

        return image_link

        if image_link:
            return jsonify({"status": "success", "image_link": image_link}), 200
        else:
            return jsonify({"error": "Image generation failed"}), 500
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        return jsonify({"error": str(e)}), 500


#print(generate_image())