import os
import random
import requests
from openai import OpenAI
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- open_ai.py ---
class AIDesigner:
    def __init__(self):
        self.conf = Config()
        oai_api_key = self.conf.OPENAI_API_KEY
        self.client = OpenAI(api_key=oai_api_key)
    
    def create_image(self, _prompt, folder, filename=''):
        path = os.path.join(self.conf.IMAGE_UPLOADS, folder)
        
        # Убедитесь, что путь корректен
        if not os.path.exists(path):
            os.makedirs(path)
        
        try:
            logger.info(f"DEBUG: {self.conf.DEBUG}")
            if self.conf.DEBUG == False:
                raise Exception("RANDOM IMAGE")  # Исключение для тестирования fallback
            
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=_prompt,
                size=self.conf.IMAGE_SIZE,
                quality=self.conf.IMAGE_QUALITY,
                n=1,
            )
            image_url = response.data[0].url
            if filename:
                image_data = requests.get(image_url).content
                file_path = os.path.join(path, filename)
                with open(file_path, 'wb') as handler:
                    handler.write(image_data)
                print(f"Image saved as {file_path}")

                # Приведение путей к стандартному виду (с прямыми слэшами)
                file_path = file_path.replace("\\", "/")

                # Убираем дублирование 'static' и добавляем только один раз
                if file_path.startswith("static/"):
                    file_path = file_path[len("static/"):]

                return file_path
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при загрузке изображения: {e}")
            return self.load_random_arena_image()
        except Exception as e:  # Общий обработчик других исключений
            print(f"Произошла ошибка: {e}")
            return self.load_random_arena_image()

    def load_random_arena_image(self):
        arena_images_path = os.path.join(self.conf.IMAGE_UPLOADS, 'arena')
        
        if not os.path.exists(arena_images_path):
            raise FileNotFoundError(f"Папка с изображениями арены не найдена: {arena_images_path}")
        
        # Получаем список всех файлов в папке arena
        image_files = [f for f in os.listdir(arena_images_path) if os.path.isfile(os.path.join(arena_images_path, f))]
        
        if not image_files:
            raise FileNotFoundError(f"Нет изображений в папке: {arena_images_path}")
        
        # Выбираем случайное изображение
        random_image = random.choice(image_files)
        
        # Возвращаем путь к изображению
        random_image_path = os.path.join("images/arena", random_image)
        print(f"Выбрано случайное изображение арены: {random_image_path}")
        
        return random_image_path.replace("\\", "/")
