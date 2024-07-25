from models import db, User, Role

def add_default_values():
    # Добавление роли character_creator
    if not Role.query.filter_by(name='character_creator').first():
        character_creator_instructions = """
        Your instructions for the character creator role.
        """
        new_role = Role(name='character_creator', instructions=character_creator_instructions)
        db.session.add(new_role)
        db.session.commit()
    
    # Другие значения по умолчанию, такие как пользователи, сообщения и т.д.
    if not User.query.filter_by(username='default_user').first():
        default_user = User(username='default_user', name='Default User', email='default@example.com', password='password')
        db.session.add(default_user)
        db.session.commit()

def remove_default_values():
    # Функция для удаления значений по умолчанию
    User.query.filter_by(username='default_user').delete()
    Role.query.filter_by(name='character_creator').delete()
    db.session.commit()
