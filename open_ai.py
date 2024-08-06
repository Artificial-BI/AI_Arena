# import openai
# import base64
# from config import Config

# conf = Config()

# openai.api_key = conf.OPENAI_API_KEY



# _prompt="""Kindom is a warrior of unmatched strength and ferocity. He was raised in a small village on the fringes of the kingdom, 
# where he learned to fight from a young age. His village was constantly under threat from raiders and monsters, and Kindom honed his 
# skills in the harsh environment.  Kindom is a master of the sword, able to swing it with terrifying speed and power. 
# He is also incredibly strong, able to lift and throw objects far heavier than any normal man.  
# While his intelligence is not his strong point, his instinct and experience in combat make him a formidable opponent. 
# Kindom is fiercely loyal to his friends and family and will fight tooth and nail to protect them. 
# His fierce nature makes him intimidating to most, and he rarely speaks, letting his actions do the talking.  
# Though he may not be eloquent, he commands respect with every swing of his sword."""


# # Generate an image from text using DALL-E
# try:
#     response = openai.Image.create(
#         prompt=_prompt,
#         n=1,
#         size="1024x1024"
#     )

#     # Print the URL of the generated image
#     image_url = response['data'][0]['url']
#     print("Generated Image URL:", image_url)
# except Exception as e:
#     print(f"Error generating image: {e}")

import openai
import requests
from config import Config
conf = Config()
# Set your OpenAI API key
openai.api_key = conf.OPENAI_API_KEY

# Define the prompt
prompt = "A futuristic city with flying cars"

try:
    # Generate an image from the text prompt
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="1024x1024"
    )

    # Extract the URL of the generated image
    image_url = response['data'][0]['url']
    print("Generated Image URL:", image_url)

    # Download the image
    image_response = requests.get(image_url)
    if image_response.status_code == 200:
        with open('generated_image.png', 'wb') as f:
            f.write(image_response.content)
        print("Image downloaded and saved as 'generated_image.png'")
    else:
        print("Failed to download the image")

except Exception as e:
    print(f"Error generating image: {e}")


