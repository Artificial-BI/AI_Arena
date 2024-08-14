import json
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_json_file(file_path):
    """Чтение данных из JSON-файла."""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error reading JSON file {file_path}: {e}")
        return {}

def write_json_file(file_path, data):
    """Запись данных в JSON-файл."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Error writing to JSON file {file_path}: {e}")
