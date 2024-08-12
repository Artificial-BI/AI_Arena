# --- config.py ---

import os
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_dotenv(dotenv_path):
    res = {}
    try:
        with open(dotenv_path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    res[key] = value
    except FileNotFoundError:
        logger.error(f"Error: The file {dotenv_path} was not found.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    return res
       

class Config:
    
    # Logging configuration
    LOG_DIR = 'logs'
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    LOG_FILE = os.path.join(LOG_DIR, 'app.log')
    
    key_env = load_dotenv('.env')
    
    # Secret key for session data protection
    SECRET_KEY = key_env['SECRET_KEY']
    
    # API token for accessing Gemini
    GEMINI_API_TOKEN = key_env['GEMINI_API_TOKEN']
    OPENAI_API_KEY = key_env['OPENAI_API_KEY']
    
    # Define the base directory of the project
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # SQLite database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'aiarena.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Increase SQLite timeout to prevent database lock errors
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'timeout': 1}  # Set timeout to 1 seconds
    }
    
    # Folder for storing uploaded images
    IMAGE_UPLOADS = os.path.join('static', 'images')
    
    IMAGE_QUALITY = 'standard'
    IMAGE_SIZE = '1024x1024'
    
    DEBUG = False

    # Путь к JSON-файлу
    FIRST_VISIT_FILE = 'first_visit.json'
    
    # Путь к JSON-файлу
    VISIT_TRACKING_FILE = 'game_visit_tracking.json'