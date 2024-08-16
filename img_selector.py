import os
import random
import logging
import requests
from config import Config
from utils import win_to_unix_path
from open_ai import AIDesigner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- open_ai.py ---
class IMGSelector:
    def __init__(self):
        self.conf = Config()

    def make_path(self, user_id, player_id):
        path_img_file = f"static/images/user_{user_id}/{player_id}.png"
        return path_img_file

    def save_file(self, path_img_file, image_url):
        image_data = requests.get(image_url).content
        with open(path_img_file, 'wb') as handler:
            handler.write(image_data)
        logger.info(f"File saved, path: {path_img_file}")

    # Функция для чтения всех изображений из папки и её подпапок
    def read_images_from_folder(self, folder_path, exclude_folders=None, _root=True):
        if exclude_folders is None:
            exclude_folders = []

        image_paths = []
        exclude_folders = [win_to_unix_path(os.path.join(folder_path, folder)) for folder in exclude_folders]

        # Проходимся по всем папкам и подпапкам
        for root, dirs, files in os.walk(folder_path):
            root_unix = win_to_unix_path(root)

            # Исключаем ненужные папки
            dirs[:] = [d for d in dirs if win_to_unix_path(os.path.join(root, d)) not in exclude_folders]

            # Добавляем в список пути к изображениям, только если мы не в корневой папке
            if _root == False and root == folder_path:
                continue

            # Добавляем в список пути к изображениям
            for file in files:
                if file.lower().endswith('.png'):
                    image_paths.append(win_to_unix_path(os.path.join(root, file)))

        return image_paths

    # Функция для случайного выбора изображения из списка с удалением
    def select_random_image(self, image_list):
        if not image_list:
            raise ValueError("The image list is empty.")

        # Выбираем случайный индекс
        random_index = random.randint(0, len(image_list) - 1)
        # Извлекаем изображение
        selected_image = image_list.pop(random_index)
        selected_image_path = win_to_unix_path(selected_image)
        return selected_image_path

    def load_image(self, theme_img):
        if theme_img == 'arena':
            folder_path = 'static/images/arena'
            image_list = self.read_images_from_folder(folder_path)
            path_img = self.select_random_image(image_list)
        elif theme_img == 'character':
            exclude_folders = ['default', 'arena']
            folder_path = 'static/images'
            image_list = self.read_images_from_folder(folder_path, exclude_folders, False)
           # logger.info(f'image_list: {image_list}')
            path_img = self.select_random_image(image_list)
        else:
            folder_path = 'static/images/default'
            image_list = self.read_images_from_folder(folder_path)
            path_img = self.select_random_image(image_list)
        return path_img    

    def selector(self, user_id, player_id, type_make, theme_img='', _name='', _prompt=''):
        path_img = ''
        if type_make == 'create':
            designer = AIDesigner()
            try:
                logger.info(f"--- GENERATE IMAGE {_name} ---")
                img_url = designer.create_image(_prompt)
                path_img = self.make_path(user_id, player_id)
                self.save_file(path_img, img_url)
            except requests.exceptions.RequestException as e:
                logger.info(f"Ошибка при загрузке изображения: {e}")
                path_img = self.load_image(theme_img)
            except Exception as e:  # Общий обработчик других исключений
                logger.info(f"Произошла ошибка: {e}")
                path_img = self.load_image(theme_img)
        else:
            path_img = self.load_image(theme_img)
        if path_img.startswith("static/"):
            path_img = path_img[len("static/"):]
        logger.info(f"File selected, path: {path_img}")
        return path_img
