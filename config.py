# --- config.py ---

import os

def load_dotenv(dotenv_path):
    with open(dotenv_path, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

class Config:
    load_dotenv('.env')
    
    # Secret key for session data protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # API token for accessing Gemini
    GEMINI_API_TOKEN = os.getenv('GEMINI_API_TOKEN')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    # Define the base directory of the project
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # SQLite database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'aiarena.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Folder for storing uploaded images
    IMAGE_UPLOADS = os.path.join('static', 'images')
    
    # Logging configuration
    LOG_DIR = 'logs'
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    LOG_FILE = os.path.join(LOG_DIR, 'app.log')
