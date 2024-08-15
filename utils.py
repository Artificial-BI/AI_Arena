# -- utils.py --
import os
import re
import json
import hashlib
import logging
import time

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def name_to_filename(name):
    filename = re.sub(r'[\\/*?:"<>|]', "", name.replace(" ", "_"))
    return filename


def win_to_unix_path(winpath):
    file_path = winpath.replace("\\", "/").replace('"', '')
    return file_path

def convert_hash_mini(original_code):
    # Generate a hash using SHA1
    hash_object = hashlib.sha1(original_code.encode())
    hash_code = hash_object.hexdigest()
    # Trim to desired length (e.g. 8 characters)
    short_code = hash_code[:8]
    return short_code

import re

def parse_referee(text):
    name_pattern = re.compile(r"'name':\s*'([^']*)'")
    combat_pattern = re.compile(r"'combat':\s*(\d+)")
    damage_pattern = re.compile(r"'damage':\s*(\d+)")

    names = name_pattern.findall(text)
    combats = combat_pattern.findall(text)
    damages = damage_pattern.findall(text)

    grades = []

    # Обрабатываем все найденные имена
    for i in range(len(names)):
        grade = {
            "name": names[i],
            "combat": int(combats[i]) if i < len(combats) else None,
            "damage": int(damages[i]) if i < len(damages) else None,
        }
        grades.append(grade)

    return grades

def parse_character(text): # Strength: 80 Dexterity: 65 Intelligence: 45 Stamina: 90 Speed: 70 Magic: 10 Defense: 85 Attack: 90 Charisma: 30 Luck: 25 
    # Define regular expressions for each field
    # 1. Strength 2. Dexterity 3. Intelligence 4. Endurance 5. Speed 6. Magic 7. Defense 8. Attack 9. Charisma 10. Luck
    name_pattern = re.compile(r"Name:\s*(.*)")
    type_pattern = re.compile(r"Type:\s*(.*)")
    strength_pattern = re.compile(r"Strength:\s*(\d+)")
    dexterity_pattern = re.compile(r"Dexterity:\s*(\d+)")
    intelligence_pattern = re.compile(r"Intelligence:\s*(\d+)")
    endurance_pattern = re.compile(r"Endurance:\s*(\d+)")
    speed_pattern = re.compile(r"Speed:\s*(\d+)")
    magic_pattern = re.compile(r"Magic:\s*(\d+)")
    defense_pattern = re.compile(r"Defense:\s*(\d+)")
    attack_pattern = re.compile(r"Attack:\s*(\d+)")
    charisma_pattern = re.compile(r"Charisma:\s*(\d+)")
    luck_pattern = re.compile(r"Luck:\s*(\d+)")
    description_pattern = re.compile(r"Description:\s*(.*)", re.DOTALL)
    #print('------text:',text)
    # Extract values using regular expressions
    name = name_pattern.search(text)
    char_type = type_pattern.search(text)
    strength = strength_pattern.search(text)
    dexterity = dexterity_pattern.search(text)
    intelligence = intelligence_pattern.search(text)
    endurance = endurance_pattern.search(text)
    speed = speed_pattern.search(text)
    magic = magic_pattern.search(text)
    defense = defense_pattern.search(text)
    attack = attack_pattern.search(text)
    charisma = charisma_pattern.search(text)
    luck = luck_pattern.search(text)
    description = description_pattern.search(text)

    # Create a dictionary with extracted values
    #print('endurance:',endurance)
    character = {
        "name": name.group(1) if name else None,
        "type": char_type.group(1) if char_type else None,
        "strength": int(strength.group(1)) if strength else None,
        "dexterity": int(dexterity.group(1)) if dexterity else None,
        "intelligence": int(intelligence.group(1)) if intelligence else None,
        "endurance": int(endurance.group(1)) if endurance else None,
        "speed": int(speed.group(1)) if speed else None,
        "magic": int(magic.group(1)) if magic else None,
        "defense": int(defense.group(1)) if defense else None,
        "attack": int(attack.group(1)) if attack else None,
        "charisma": int(charisma.group(1)) if charisma else None,
        "luck": int(luck.group(1)) if luck else None,
        "description": description.group(1).strip() if description else None
    }
    #print('character:',character['endurance'])
    return character

def parse_arena(text):
    # Define regular expressions for each field
    difficulty_pattern = re.compile(r"Difficulty:\s*(\d+)%")
    danger_pattern = re.compile(r"Danger:\s*(\d+)%")
    size_pattern = re.compile(r"Size:\s*(.*)")
    atmosphere_pattern = re.compile(r"Describe Arena Atmosphere:\s*(.*)", re.DOTALL)

    # Extract values using regular expressions
    difficulty = difficulty_pattern.search(text)
    danger = danger_pattern.search(text)
    size = size_pattern.search(text)
    atmosphere = atmosphere_pattern.search(text)

    # Create a dictionary with extracted values
    arena = {
        "difficulty": int(difficulty.group(1)) if difficulty else None,
        "danger": int(danger.group(1)) if danger else None,
        "size": size.group(1).strip() if size else None,
        "atmosphere": atmosphere.group(1).strip() if atmosphere else None
    }

    return arena

def load_from_json(filename):

    # Проверяем, существует ли JSON файл
    if not os.path.exists(filename):
        logger.error(f"JSON file not found for character: {filename}")
        character_data = f"JSON file not found for character: {filename}"
    # Чтение данных из JSON файла
    with open(filename, 'r', encoding='utf-8') as json_file:
        character_data = json.load(json_file)
    return character_data    

def save_to_json(data, filename):
    
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving data to JSON: {e}")

def generate_unixid():
    # Получаем текущее Unix-время в секундах
    unix_time = int(time.time())
    return str(unix_time)