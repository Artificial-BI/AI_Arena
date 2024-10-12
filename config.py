# --- config.py ---

import os
import logging
from utils import win_to_unix_path

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
    LOG_FILE = win_to_unix_path(os.path.join(LOG_DIR, 'app.log'))
    
    key_env = load_dotenv('.env')
    
    # Secret key for session data protection
    SECRET_KEY = key_env['SECRET_KEY']
    
    # API token for accessing Gemini
    GEMINI_API_TOKEN = key_env['GEMINI_API_TOKEN']
    OPENAI_API_KEY = key_env['OPENAI_API_KEY']
    
    # Define the base directory of the project
    BASE_DIR = win_to_unix_path(os.path.abspath(os.path.dirname(__file__)))
    
    # SQLite database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + win_to_unix_path(os.path.join(BASE_DIR, 'instance', 'aiarena.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Increase SQLite timeout to prevent database lock errors
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'timeout': 1}  # Set timeout to 1 seconds
    }
    
   # MESSAGES_DB = 'sqlite:///messages.db'
    MESSAGES_DB = 'sqlite:///' + win_to_unix_path(os.path.join(BASE_DIR, 'instance', 'messages.db'))
    
    SYS_ID = 3210123
    # Folder for storing uploaded images
    IMAGE_UPLOADS = win_to_unix_path(os.path.join('static', 'images'))
    
    IMAGE_QUALITY = 'standard'
    IMAGE_SIZE = '1024x1024'
    
    DEBUG = True

    # Путь к JSON-файлу
    FIRST_VISIT_FILE = 'first_visit.json'
    
    # Путь к JSON-файлу
    VISIT_TRACKING_FILE = 'game_visit_tracking.json'
    
    CURRENT_CHARACTER = {'410620035969326635':{}}
    
    ARENA_MODE = 'random'
    
    NEW_BATTLE_WAIT = 20
    WAIT_COUNT = 30
    
    PLAYER_COUNT = 2
    
    STAT_PORT =  6571 
    STAT_PUB_PORT =  6566 
    STAT_HOST =  f"tcp://localhost:{STAT_PORT}"
    STAT_PUB_HOST =  f"tcp://*:{STAT_PUB_PORT}" 
    
    MESS_HOST = 'localhost'
    MESS_PUB_PORT =  "tcp://*:6568" 
    MESS_PORT=  48888 #"tcp://localhost:6573" 
    
    COUNT_ROUND = 3
    WAITING_STEPS = 10