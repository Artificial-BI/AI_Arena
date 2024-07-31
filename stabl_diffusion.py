import torch
from diffusers import StableDiffusionPipeline

# Настройка модели
model_name = "CompVis/stable-diffusion-v1-4"
pipeline = StableDiffusionPipeline.from_pretrained(model_name, torch_dtype=torch.float16)
pipeline = pipeline.to("cuda")

def generate_image(description, filename):
    try:
        # Генерация изображения
        image = pipeline(description).images[0]

        # Сохранение изображения
        save_path = f'static/images/{filename}'
        image.save(save_path)
        print(f"Image saved at {save_path}")
    except Exception as e:
        print(f"Error generating image: {e}")

if __name__ == "__main__":
    description = "A wizard casting a powerful spell"
    filename = "generated_image.png"
    generate_image(description, filename)
