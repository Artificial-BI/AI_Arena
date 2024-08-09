import os
from openai import OpenAI
from config import Config
import requests
# --- open_ai.py ---
class AIDesigner:
    def __init__(self):
        self.conf = Config()

        oai_api_key = self.conf.OPENAI_API_KEY
        self.client = OpenAI(api_key=oai_api_key)
    
    def create_image(self, _prompt, folder, filename=''):
        path = os.path.join(self.conf.IMAGE_UPLOADS, folder)
        # Замена пробелов в имени файла на подчеркивания

        if not os.path.exists(path):
            os.makedirs(path)
        
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=_prompt,
            size=self.conf.IMAGE_SIZE,
            quality=self.conf.IMAGE_QUALITY,
            n=1,
        )
        image_url = response.data[0].url
        file_path = ''
        if filename != '':
            image_data = requests.get(image_url).content
            file_path = os.path.join(path, filename)
            with open(file_path, 'wb') as handler:
                handler.write(image_data)
            print(f"Image saved as {file_path}")
        
        return file_path
