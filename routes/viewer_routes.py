from flask import Blueprint, render_template, jsonify
from models import Character

viewer_bp = Blueprint('viewer', __name__)

@viewer_bp.route('/')
def viewer():
    characters = Character.query.order_by(Character.id.desc()).limit(2).all()
    return render_template('viewer.html', characters=characters)

@viewer_bp.route('/get_characters')
def get_characters():
    characters = Character.query.order_by(Character.id.desc()).limit(2).all()
    characters_data = []
    for character in characters:
        characters_data.append({
            'name': character.name,
            'description': character.description,
            'image_url': character.image_url,
            'stats': {
                'Здоровье': character.health,
                'Интеллект': character.intelligence,
                'Сила': character.strength,
                'Магия': character.magic,
                'Атака': character.attack,
                'Защита': character.defense,
                'Скорость': character.speed,
                'Ловкость': character.agility,
                'Выносливость': character.endurance,
                'Удача': character.luck
            }
        })
    return jsonify(characters_data)
