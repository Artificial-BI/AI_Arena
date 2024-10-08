import logging
from concurrent_log_handler import ConcurrentRotatingFileHandler
import os
from config import Config

def configure_logging(app):
    if not app.debug:
        if not os.path.exists(Config.LOG_DIR):
            os.makedirs(Config.LOG_DIR)
        file_handler = ConcurrentRotatingFileHandler(Config.LOG_FILE, maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('AI Arena startup')

    # Установка уровня логирования для werkzeug
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)
