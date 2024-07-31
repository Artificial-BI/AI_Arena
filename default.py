import json
from extensions import db
from models import User, Role, Character

default_roles = [
    {'name': 'referee', 'instructions': 'Evaluate the battles and assign points.'},
    {'name': 'arena', 'instructions': 'Generate the arena based on characters\' characteristics.'},
    {'name': 'tactician', 'instructions': 'Read arena and character data, and provide move recommendations.'},
    {'name': 'fighter', 'instructions': 'Generate moves based on tactician recommendations and arena situation.'},
    {'name': 'commentator', 'instructions': 'Generate comments on the battle based on the actions.'},
    {'name': 'artist', 'instructions': 'Generate images based on the best battle episodes.'}
]

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
        if not Role.query.filter_by(name=role_data['name']).first():
            new_role = Role(name=role_data['name'], instructions=role_data['instructions'])
            db.session.add(new_role)
    db.session.commit()

    if not User.query.filter_by(username='default_user').first():
        default_user = User(username='default_user', name='Default User', email='default@example.com', password='password')
        db.session.add(default_user)
        db.session.commit()

    default_user = User.query.filter_by(username='default_user').first()
    if not Character.query.filter_by(name='Mage').first():
        mage_traits = {
            "Health": 50,
            "Intelligence": 80,
            "Strength": 30,
            "Magic": 90,
            "Attack": 40,
            "Defense": 50,
            "Speed": 60,
            "Agility": 70,
            "Endurance": 40,
            "Luck": 50
        }
        mage = Character(
            user_id=default_user.id,
            name='Mage',
            description='A master of magic with high intelligence and magical power.',
            image_url='images/default/mage.png',
            traits=json.dumps(mage_traits)
        )
        db.session.add(mage)
        db.session.commit()

    if not Character.query.filter_by(name='Warrior').first():
        warrior_traits = {
            "Health": 80,
            "Intelligence": 40,
            "Strength": 90,
            "Magic": 20,
            "Attack": 70,
            "Defense": 60,
            "Speed": 50,
            "Agility": 40,
            "Endurance": 70,
            "Luck": 50
        }
        warrior = Character(
            user_id=default_user.id,
            name='Warrior',
            description='A strong and enduring warrior with powerful attacks.',
            image_url='images/default/warrior.png',
            traits=json.dumps(warrior_traits)
        )
        db.session.add(warrior)
        db.session.commit()

def remove_default_values():
    User.query.filter_by(username='default_user').delete()
    Role.query.filter_by(name='character_creator').delete()
    Character.query.filter_by(user_id=None).delete()
    db.session.commit()
