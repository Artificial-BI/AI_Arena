
#--- config.py ---

import os
from dotenv import load_dotenv
class Config:
    load_dotenv()
    # Секретный ключ для защиты данных сессий
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # Токен для доступа к API Gemini
    GEMINI_API_TOKEN = os.getenv('GEMINI_API_TOKEN')
    
    # Определение базовой директории проекта
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Настройка базы данных SQLite
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'aiarena.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Папка для хранения загружаемых изображений
    IMAGE_UPLOADS = os.path.join('static', 'images')
    
    # Настройки для логирования
    LOG_DIR = 'logs'
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    LOG_FILE = os.path.join(LOG_DIR, 'app.log')


