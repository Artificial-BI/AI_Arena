import asyncio
import requests
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageGenerator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.endpoint = "https://api.example.com/generate"  # Замените на фактический URL API

    async def generate_image(self, description):
        logger.info(f"Generating image for description: {description}")
        payload = {
            "description": description,
            "api_key": self.api_key
        }
        response = requests.post(self.endpoint, json=payload)
        if response.status_code == 200:
            data = response.json()
            image_url = data.get('image_url')
            if image_url:
                logger.info(f"Generated image URL: {image_url}")
                return image_url
            else:
                logger.error("No image URL found in response")
                return None
        else:
            logger.error(f"Failed to generate image: {response.status_code}")
            return None

    def download_image(self, image_url, save_path):
        try:
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                with open(save_path, 'wb') as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                logger.info(f"Image downloaded and saved to: {save_path}")
                return save_path
            else:
                logger.error(f"Failed to download image: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return None

    async def generate_and_save_image(self, description, filename, return_type='url'):
        image_url = await self.generate_image(description)
        if image_url:
            if return_type == 'local':
                save_path = os.path.join('static', 'images', filename)
                return self.download_image(image_url, save_path)
            elif return_type == 'url':
                return image_url
            else:
                logger.error("Invalid return type specified")
                return None
        else:
            return None

def generate_image():
    try:
        # Статические данные для тестирования
        description = "Aethelred is a wizened mage of immense arcane knowledge and power. His years of study have gifted him with a mastery of elemental magic, particularly fire and ice. He wields a staff crafted from ancient oak, imbued with potent runes that amplify his spells. Though physically frail, Aethelred's intellect and magical prowess make him a formidable opponent. He is often seen as a recluse, preferring the company of his books and scrolls to that of other people. However, he is known to possess a keen mind and a sharp wit, capable of seeing through deception and manipulating situations to his advantage. His loyalty lies with those who seek knowledge and truth, and he will defend them with the full force of his magic."
        filename = 'test_img.png'
        return_type = 'url'

        if not description or not filename:
            logger.error("Description and filename are required")
            return None

        api_key = "YOUR_API_KEY"  # Замените на ваш API ключ
        generator = ImageGenerator(api_key)
        image_link = asyncio.run(generator.generate_and_save_image(description, filename, return_type))

        if image_link:
            logger.info(f"Image generated successfully: {image_link}")
            if return_type == 'local':
                return {"status": "success", "file_path": image_link}
            else:
                return {"status": "success", "image_link": image_link}
        else:
            logger.error("Image generation failed")
            return None
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        return None

if __name__ == "__main__":
    result = generate_image()
    if result:
        print(result)
    else:
        print("Failed to generate image")
