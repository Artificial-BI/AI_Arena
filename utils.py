# -- utils.py --

import re
import json
import hashlib


def convert_hash_mini(original_code):
    # Generate a hash using SHA1
    hash_object = hashlib.sha1(original_code.encode())
    hash_code = hash_object.hexdigest()
    # Trim to desired length (e.g. 8 characters)
    short_code = hash_code[:8]
    return short_code


def parse_character(text):
    # Define regular expressions for each field
    name_pattern = re.compile(r"Name:\s*(.*)")
    type_pattern = re.compile(r"Type:\s*(.*)")
    strength_pattern = re.compile(r"Strength:\s*(\d+)")
    agility_pattern = re.compile(r"Agility:\s*(\d+)")
    intelligence_pattern = re.compile(r"Intelligence:\s*(\d+)")
    endurance_pattern = re.compile(r"Endurance:\s*(\d+)")
    speed_pattern = re.compile(r"Speed:\s*(\d+)")
    magic_pattern = re.compile(r"Magic:\s*(\d+)")
    defense_pattern = re.compile(r"Defense:\s*(\d+)")
    attack_pattern = re.compile(r"Attack:\s*(\d+)")
    charisma_pattern = re.compile(r"Charisma:\s*(\d+)")
    luck_pattern = re.compile(r"Luck:\s*(\d+)")
    description_pattern = re.compile(r"Description:\s*(.*)", re.DOTALL)

    # Extract values using regular expressions
    name = name_pattern.search(text)
    char_type = type_pattern.search(text)
    strength = strength_pattern.search(text)
    agility = agility_pattern.search(text)
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
    character = {
        "name": name.group(1) if name else None,
        "type": char_type.group(1) if char_type else None,
        "strength": int(strength.group(1)) if strength else None,
        "agility": int(agility.group(1)) if agility else None,
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

def save_to_json(data, filename='data.json'):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving data to JSON: {e}")

# Example usage
if __name__ == "__main__":
    character_text = """
    Name: Arathorn
    Type: Warrior
    Strength: 85
    Agility: 60
    Intelligence: 50
    Endurance: 80
    Speed: 70
    Magic: 30
    Defense: 75
    Attack: 90
    Charisma: 65
    Luck: 50
    Description: Arathorn is a seasoned warrior known for his strength and combat skills. He has fought in numerous battles and his presence on the battlefield inspires his comrades.
    """

    parsed_character = parse_character(character_text)
    print('TEST CHARACTERS:', parsed_character)
    save_to_json(parsed_character)

    arena_text = """
    Set Arena Parameters:

    Difficulty: 60%
    Danger: 45%
    Size: Medium

    Describe Arena Atmosphere:

    The arena is a sprawling, sun-drenched clearing within a vast, ancient forest. Towering trees, gnarled and twisted by time, cast long, dappled shadows across the verdant floor. The air is thick with the scent of pine needles and damp earth, a heady mix of life and decay. The silence is broken only by the rustling of leaves and the occasional chirp of unseen birds. A sense of hidden danger hangs heavy in the air, as if the very forest itself is watching, waiting for a moment to unleash its fury.
    """

    parsed_arena = parse_arena(arena_text)
    print('TEST ARENA:', parsed_arena)
    save_to_json(parsed_arena, 'arena_data.json')
