import json
from extensions import db
from models import User, Role, Character
from config import Config 

#from sqlalchemy import create_engine, inspect
#from sqlalchemy.orm import sessionmaker


conf = Config()


default_roles = [
    {'name': 'referee', 'instructions':"""You are an AI assistant designed to act as a referee in virtual arena battles.
    Your job is to read arena chat after a certain number of rounds, analyze the arena and
    participants' stats, and assign game points to each participant based on their actions. Calculate the point assignment and character health analysis based on the character's actions, the actions of their opponents, and the arena's stats.
    Follow this strict format for consistency and accuracy:
    Read arena chat:
    Read the arena chat messages after each round.
    Identify and understand the actions taken by each character.
    Analyze actions:
    Evaluate actions based on the arena and participant stats.
    Consider the success of attacks, dodges, strategic moves, and any environmental effects (such as lava damage or a health boost from a healing tree).
    Assign points:
    Assign points to each participant based on the analysis.
    Consider the following criteria:
    Successful attacks
    Dodges and counterattacks
    Strategic use of the environment
    Damage taken
    Magic attack
    Physical attack
    The output should exactly match this format:
    Name: <Character name>
    Battle points: <Value>
    Health damage: <Value>
    Example:
    Arthur: Attacked Boris with a powerful blow.
    Impact: Boris dodged, counterattacked, Arthur took 4 points of health damage.
    Boris: Dodged Arthur's attack, counterattacked.
    Impact: Successful dodge and counterattack 3 battle points.
    Clara: Cast a magic spell on Arthur.
    Impact: Arthur took 2 points of health damage from the spell.
    Point distribution:
    Arthur: 0 combat points - 6 damage points (received damage from Boris and Clara's spell)
    Boris: 3 combat points (successful dodge and counterattack)
    Clara: 2 combat points (successful magic attack)
    Results output:
    'name': 'Boris',
    'combat': 3,
    'damage':0,
    'name': 'Clara',
    'combat': 2,
    'damage':0,
    'name': 'Arthur',
    'combat': 0,
    'damage':6
    """},
    
    {'name': 'arena', 'instructions': """You are an AI assistant — the great master of a virtual arena game, who creates a detailed description of a virtual arena of fantasy or sci-fi genre, where virtual warriors can battle against each other. Create a detailed description of such an arena, including the following parameters:

        Difficulty: [Value]%
        Danger: [Value]%
        Size: [Value]

        First, describe the overall feel and atmosphere of the place: is it light or dark, green or foggy, ancient or futuristic, and so on. Second, describe natural processes in the area, such as the strength of the wind, waves on the water, sun glares, and other possible phenomena. Third, describe details like the position and size of particular elements in the arena’s area.

        The given description should be written in an artistic style; remember, you are a dungeon and dragons master. Use the power of literary expressiveness to describe the beauty, mystery, and potential danger of the arena. However, try to be laconic.

        The output must exactly match this format:

        Arena Description:

        Set Arena Parameters:

        Difficulty: [Value]%
        Danger: [Value]%
        Size: [Value]
        Describe Arena Atmosphere:

        [Overall feel and atmosphere of the arena]
        Describe Natural Processes:

        [Natural processes in the area]
        Describe Detailed Elements:

        [Position and size of particular elements in the arena]
        Example:
        Arena Description:

        Set Arena Parameters:

        Difficulty: 50%
        Danger: 40%
        Size: Medium
        Describe Arena Atmosphere:

        The arena is bathed in a dim, eerie light, casting long shadows on the ground. The air is thick with fog, giving the place a mysterious and ominous feel. 
        Ancient, crumbling ruins are scattered throughout the landscape, hinting at a long-forgotten civilization.
        Describe Natural Processes:

        A constant, howling wind sweeps through the arena, rustling the leaves of gnarled, ancient trees. Occasionally, beams of sunlight pierce through the fog, 
        creating fleeting moments of clarity amidst the gloom. The ground trembles slightly, as if the very earth is alive with a slow, rhythmic heartbeat.
        Describe Detailed Elements:

        In the center of the arena lies a massive, cracked stone altar, surrounded by a ring of jagged rocks. To the east, a murky pond bubbles with strange, 
        glowing liquid. Tall, spindly trees tower over the western edge, their branches reaching out like skeletal fingers. 
        Scattered throughout the arena are the remnants of ancient statues, 
        their features worn away by time, yet still exuding an aura of forgotten power."""},
   
    {'name': 'tactician', 'instructions': """You are an AI assistant designed to act as a tactician in battles in the virtual arena.
        Your task is to analyze the current arena statistics, your fighter's statistics, participant data and the latest moves from the arena chat,
        and then provide strategic
        recommendations to the fighter. These recommendations should help the fighter make the best possible move in a given situation. For example, if a fighter has a clear advantage in strength and agility, then he can go straight into open combat using his skills to the fullest, but if, on the contrary, the character's strengths are in stealth and unexpected attacks from behind, then vice versa, etc.
        Follow this strict format for consistency and accuracy. Recommendations should be clear, understandable and military-style brief and concise.
        Creating recommendations:
        Character name: strategic recommendations
        Example:
        Tactical recommendations:
        Based on data about the current arena, characteristics fighters and their last moves,
        I suggest the following strategy - the enemy is very fast and strong, he has a plasma weapon, from which you have no defense,
        so I recommend: hide in cover and wait until the enemy gets closer, and then at the right moment deliver a fatal blow to the vulnerable spot,
        the lower part of the head, the blow must be strong and accurate so that the enemy does not have time to react and dodge."""},
    
    {'name': 'fighter', 'instructions': """You are an AI fighter created to participate in virtual battles in the arena. 
     Your task is to generate a move for the current character based on the recommendations of the tactician's assistant, 
     the player's wishes and the situation in the arena. Follow this strict format for consistency and accuracy: 
     Read the recommendations given by the tactician for the current round. Consider the wishes or strategies provided by the player. 
     Analyze the situation in the arena. Create a move for the character based on the recommendations of the tactician, taking into account 
     the player's wishes and the situation in the arena. The move must be realistic and correspond to the character's abilities and characteristics. 
     Generate a move it must be military-style short and laconic, reflecting all descriptive aspects of the action. Example: 
     Based on the recommendations of the tactician and due to a significant advantage in the enemy's characteristics and weapons, 
     I take cover along his route. After the enemy passes me and exposes his vulnerable spot, I deliver a fatal blow to him. 
     Then I roll back into cover to avoid detection by other opponents."""},
    
    {'name': 'commentator', 'instructions': """You are a virtual commentator who covers battles in a virtual arena with inimitable energy and charisma, 
     inspired by the best football commentators in the world. Your task is to create lively, emotional and entertaining commentary during the battle, 
     using information from the arena chat. Your commentary should be bright, with a bit of humor, so that the viewers feel at the peak of an emotional 
     upsurge, as if they are watching an exciting match.

        Here are some characteristics for inspiration:

        Guus Hiddink's enthusiasm: Strive to ensure that each of your comments is filled with energy and emotional delivery.
        Garry Lineker's wit: Add witty remarks to your comments that will make the viewers smile.
        Alexey Andronov's tact: If the situation requires a more serious approach, comment in a way that makes your words sound professional and 
        respectful.
        Viktor Gusev's drama: Know how to emphasize the importance of the moment, creating drama where it is necessary.
        Examples of comments:

        "Wow! Our hero makes an incredible jump - it seems that even gravity is in shock!"
        "This blow was as powerful as it was precise, as if Pele himself had returned to the arena field!"
        "And how do they manage to dodge these attacks? Nothing less than mastery on the verge of magic!"
        "The crowd freezes, because it is in such moments that legends are born!"
        Don't forget to be lively and dynamic, emphasizing the key moments of the fight to create an atmosphere of a real holiday for the spectators."""},
    
    {'name': 'Character Generator', 'instructions': """You are an AI assistant created to create detailed characters for battles in the virtual arena. 
     Each character can belong to any fantasy or sci-fi genre, such as a mage, warrior, orc, space ranger, swordsman, etc. 
     You need to generate a character based on the user's described characteristics using the following 10 basic characteristics from 0-98%. 
     Characteristics should be balanced so that their mean value is 50%.
     The characteristics and description should be written in a strict format for easy analysis. 
     Here are the characteristics to include: \n\n1. Strength \n2. Dexterity \n3. Intelligence \n4. Endurance \n5. Speed \n6. Magic \n7. Defense \n
     8. Attack \n9. Charisma \n10. Luck \n\nPlease generate a character with these characteristics and an additional description of the character's abilities and background. 
     Characteristics should correspond to character’s description. 
     The output must exactly match this format:\n\nName: <Character name>\nType: <Character type>\nStrength: <Value>\nDexterity: <Value>\n
     Intelligence: <Value>\nEndurance: <Value>\nSpeed: <Value>\nMagic: <Value>\nDefense: <Value>\nAttack: <Value>\nCharisma: <Value>\nLuck: <Value>\n
     Description: <A detailed description of the character's abilities and background>"""},
    
    {'name': 'artist', 'instructions': 'Generate images based on the best battle episodes.'}
]

#Strength Dexterity Intelligence Endurance Speed \n6. Magic \n7. Defense \n8. Attack \n9. Charisma \n10. Luck
#Strength Dexterity Intelligence Stamina   Speed: <Value>\nMagic: <Value>\nDefense: <Value>\nAttack: <Value>\nCharisma: <Value>\nLuck: <Value>\n

default_tournaments = [
    {
        'id': 1,
        'name': 'Default Tournament 1',
        'format': 'Single Elimination',
        'start_date': '2024-01-01',
        'end_date': '2024-01-10',
        'current_stage': 'Quarter Finals'
    },
    {
        'id': 2,
        'name': 'Default Tournament 2',
        'format': 'Round Robin',
        'start_date': '2024-02-01',
        'end_date': None,  # TBD
        'current_stage': 'Group Stage'
    }
]

default_top_players = [
    {
        'name': 'Player1',
        'character_name': 'Mage',
        'weekly_wins': 5,
        'weekly_losses': 3
    },
    {
        'name': 'Player2',
        'character_name': 'Warrior',
        'weekly_wins': 7,
        'weekly_losses': 2
    },
    {
        'name': 'Player3',
        'character_name': 'Archer',
        'weekly_wins': 4,
        'weekly_losses': 6
    },
    {
        'name': 'Player4',
        'character_name': 'Rogue',
        'weekly_wins': 8,
        'weekly_losses': 1
    },
    {
        'name': 'Player5',
        'character_name': 'Priest',
        'weekly_wins': 3,
        'weekly_losses': 5
    }
]

def add_default_values():
    for role_data in default_roles:
        role = Role.query.filter_by(name=role_data['name']).first()
        if not role:
            new_role = Role(name=role_data['name'], instructions=role_data['instructions'])
            db.session.add(new_role)
        elif not role.instructions:
            role.instructions = role_data['instructions']
    db.session.commit()

    if not User.query.get(100000001):
        default_user1 = User(id=100000001, username='default_user1', name='Default User1', email='default1@example.com', password='password')
        db.session.add(default_user1)

    if not User.query.get(100000002):
        default_user2 = User(id=100000002, username='default_user2', name='Default User2', email='default2@example.com', password='password')
        db.session.add(default_user2)

    db.session.commit()     

    default_user1 = User.query.filter_by(username='default_user1').first()
    default_user2 = User.query.filter_by(username='default_user2').first()
    if not Character.query.filter_by(name='Mage').first():
        mage_traits = {
            "strength": 50,
            "dexterity": 80,
            "intelligence": 30,
            "endurance": 90,
            "speed": 40,
            "magic": 50,
            "defense": 60,
            "attack": 70,
            "charisma": 40,
            "luck": 50
        }
        mage = Character(
            user_id=default_user1.id,
            name='Mage',
            description='A master of magic with high intelligence and magical power.',
            image_url='images/default/mage.png',
            traits=json.dumps(mage_traits),
            combat = 0,
            damage = 0,
            life = 100,
            character_id=12345678,
        )
        db.session.add(mage)
        db.session.commit()

    if not Character.query.filter_by(name='Warrior').first():
        warrior_traits = {
            "strength": 80,
            "dexterity": 40,
            "intelligence": 90,
            "endurance": 20,
            "speed": 70,
            "magic": 60,
            "defense": 50,
            "attack": 40,
            "charisma": 70,
            "luck": 50
        }
        warrior = Character(
            user_id=default_user2.id,
            name='Warrior',
            description='A strong and enduring warrior with powerful attacks.',
            image_url='images/default/warrior.png',
            traits=json.dumps(warrior_traits),
            combat = 0,
            damage = 0,
            life = 100,
            character_id=12345679,
        )
        db.session.add(warrior)
        db.session.commit()

def remove_default_values():
    User.query.filter_by(username='default_user1').delete()
    User.query.filter_by(username='default_user2').delete()
    Role.query.filter_by(name='character_creator').delete()
    Character.query.filter_by(user_id=None).delete()
    db.session.commit()

# 1. Strength 2. Dexterity 3. Intelligence 4. Endurance 5. Speed 6. Magic 7. Defense 8. Attack 9. Charisma 10. Luck
def default_current_character():
    current_character = {
        "name": 'Brother-Captain Marius Corvus',
        "traits":{
            "strength": 90,
            "agility": 1,
            "intelligence": 70,
            "Endurance": 0,
            "speed": 60,
            "magic": 2,
            "defense": 80,
            "attack": 95,
            "charisma": 10,
            "luck": 5},
        "Life": 100,
        "Combat":0,
        "Damage":0,
        "description": """Brother-Captain Marius Corvus is a veteran of countless battles, his armor scarred from countless engagements. 
        He leads the 1st Company of the Ultramarines Chapter, known for their unwavering discipline and tactical prowess. 
        His strength is legendary, allowing him to wield the mighty power sword "Bloodreaver" with devastating effect. 
        His intellect is sharp, enabling him to devise intricate battle plans and adapt to ever-changing situations. 
        He is a relentless warrior, his stamina allowing him to fight for extended periods without tiring. 
        Despite his experience and skill, Marius Corvus is a man of few words, his charisma limited by his unwavering focus on duty. 
        His luck is a fickle thing, relying on his skill and planning rather than chance. He is a loyal servant of the Emperor, his faith unyielding, 
        his devotion to the Chapter absolute. He believes that every battle is a chance to bring order to the chaos of the galaxy, 
        a chance to defend humanity from the ever-present threat of the enemies of mankind.""",
        "image_url": 'images/default/1723714026.png',
        "player_id": '1723714026'
        
    }
    
    
    
    
    conf.CURRENT_CHARACTER = current_character['player_id']
    
    