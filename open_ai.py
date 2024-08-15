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
    
    def create_image(self, _prompt):
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=_prompt,
            size=self.conf.IMAGE_SIZE,
            quality=self.conf.IMAGE_QUALITY,
            n=1,
        )
        image_url = response.data[0].url
        return image_url
       