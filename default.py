import json
from extensions import db
from models import User, Role, Character

def add_default_values():
    # Добавление роли character_creator
    if not Role.query.filter_by(name='character_creator').first():
        character_creator_instructions = """
        Your instructions for the character creator role.
        """
        new_role = Role(name='character_creator', instructions=character_creator_instructions)
        db.session.add(new_role)
        db.session.commit()
    
    # Добавление пользователя по умолчанию
    if not User.query.filter_by(username='default_user').first():
        default_user = User(username='default_user', name='Default User', email='default@example.com', password='password')
        db.session.add(default_user)
        db.session.commit()

    # Добавление персонажей по умолчанию
    default_user = User.query.filter_by(username='default_user').first()
    if not Character.query.filter_by(name='Маг').first():
        mage_traits = {
            "Здоровье": 50,
            "Интеллект": 80,
            "Сила": 30,
            "Магия": 90,
            "Атака": 40,
            "Защита": 50,
            "Скорость": 60,
            "Ловкость": 70,
            "Выносливость": 40,
            "Удача": 50
        }
        mage = Character(
            user_id=default_user.id,
            name='Маг',
            description='Мастер магии с высоким интеллектом и магической силой.',
            image_url='images/default/mage.png',
            traits=json.dumps(mage_traits)
        )
        db.session.add(mage)
        db.session.commit()

    if not Character.query.filter_by(name='Воин').first():
        warrior_traits = {
            "Здоровье": 80,
            "Интеллект": 40,
            "Сила": 90,
            "Магия": 20,
            "Атака": 70,
            "Защита": 60,
            "Скорость": 50,
            "Ловкость": 40,
            "Выносливость": 70,
            "Удача": 50
        }
        warrior = Character(
            user_id=default_user.id,
            name='Воин',
            description='Сильный и выносливый воин с мощной атакой.',
            image_url='images/default/warrior.png',
            traits=json.dumps(warrior_traits)
        )
        db.session.add(warrior)
        db.session.commit()

def remove_default_values():
    # Функция для удаления значений по умолчанию
    User.query.filter_by(username='default_user').delete()
    Role.query.filter_by(name='character_creator').delete()
    Character.query.filter_by(user_id=None).delete()
    db.session.commit()
