import torch
import urllib
import matplotlib.pyplot as plt
from PIL import Image
from torchvision import transforms
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import os

# Устанавливаем путь к локальному кэшу
os.environ['TORCH_HOME'] = "D:/GIT/2024/ArtificialBI/ARENA/CACHE"

# Задаем путь к скачанной модели
model_path = "D:/GIT/2024/ArtificialBI/ARENA/DPT/dpt_beit_large_384.pt"

# Загружаем модель
model = torch.load(model_path)

# Загружаем модель на устройство (GPU или CPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

# Используем стандартный преобразователь для модели DPT
transform = torch.hub.load("intel-isl/MiDaS", "transforms").dpt_transform

# Загружаем изображение (замени путь на своё изображение)
image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Mount_Everest_as_seen_from_Drukair2_PLW_edit.jpg/1024px-Mount_Everest_as_seen_from_Drukair2_PLW_edit.jpg"
image_path, _ = urllib.request.urlretrieve(image_url)
img = Image.open(image_path)

# Преобразуем изображение для модели
input_batch = transform(img).to(device)

# Предсказываем карту глубин
with torch.no_grad():
    prediction = model(input_batch)

# Преобразуем предсказанную карту глубин
depth_map = prediction.squeeze().cpu().numpy()

# Настроим шаг сетки для выборки 3D-точек
step = 10  # Шаг в см (это соответствует разрешению изображения в пикселях)
rows, cols = depth_map.shape
x_coords = []
y_coords = []
z_coords = []

# Сканируем изображение с заданным шагом
for x in range(0, rows, step):
    for y in range(0, cols, step):
        z = depth_map[x, y]  # глубина (яркость пикселя)
        x_coords.append(x)
        y_coords.append(y)
        z_coords.append(z)

# Преобразуем списки координат в numpy массивы
x_coords = np.array(x_coords)
y_coords = np.array(y_coords)
z_coords = np.array(z_coords)

# Строим 3D-график с помощью matplotlib
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Используем scatter для построения сетки 3D-точек
ax.scatter(x_coords, y_coords, z_coords, c=z_coords, cmap='viridis')

ax.set_xlabel('X (cm)')
ax.set_ylabel('Y (cm)')
ax.set_zlabel('Depth')

plt.show()
