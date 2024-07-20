# --- config.py ---
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite3'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    IMAGE_UPLOADS = os.path.join('static', 'images')  # Папка для хранения изображений

    # Настройки для логирования
    LOG_DIR = 'logs'
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    LOG_FILE = os.path.join(LOG_DIR, 'app.log')

