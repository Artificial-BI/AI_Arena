import re
import json

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

def save_to_json(character, filename='character_data.json'):
    try:
        with open(filename, 'w') as f:
            json.dump(character, f, indent=4)
        print(f"Character data saved to {filename}")
    except Exception as e:
        print(f"Error saving character data to JSON: {e}")

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
    print('TEST CHARACTERS:',parsed_character)
    save_to_json(parsed_character)
