# --- config.py ---

import os

def load_dotenv(dotenv_path):
    res = {}
    try:
        with open(dotenv_path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    res[key] = value
    except FileNotFoundError:
        print(f"Error: The file {dotenv_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return res
       

class Config:
    key_env = load_dotenv('.env')
    #print('Config:',key_env)
    
    # Secret key for session data protection
    # SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SECRET_KEY = key_env['SECRET_KEY']
    # API token for accessing Gemini
   # GEMINI_API_TOKEN = os.getenv('GEMINI_API_TOKEN')
    GEMINI_API_TOKEN = key_env['GEMINI_API_TOKEN']
   
    #OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_API_KEY = key_env['OPENAI_API_KEY']
    
    # Define the base directory of the project
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # SQLite database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'aiarena.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Folder for storing uploaded images
    IMAGE_UPLOADS = os.path.join('static', 'images')
    
    IMAGE_QUALITY = 'standard'
    IMAGE_SIZE = '1024x1024'
    
    # Logging configuration
    LOG_DIR = 'logs'
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    LOG_FILE = os.path.join(LOG_DIR, 'app.log')
    

    
    
