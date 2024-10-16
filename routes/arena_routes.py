import logging
import json
from flask import Blueprint, render_template, jsonify, request, g, url_for, redirect, current_app, make_response
from cookies import Cookies
from models import Character, Registrar, Arena, PreRegistrar
from status_manager import StatusManager
from core_common import CoreCommon
from messaging_manager import MessageManager
from load_user import load_user
from player_manager import PlayerManager

arena_bp = Blueprint('arena', __name__)
logger = logging.getLogger(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

cok = Cookies()
sm = StatusManager()
mm = MessageManager()
plm = PlayerManager()
#ccom = CoreCommon()
battle_start = False
@arena_bp.before_request
def before_request():
    response = load_user()
    if response.status_code not in [200, 201]:
        return response
    user_data = response.get_json()
    g.user_id = user_data.get('user_id')
    g.cookie_id = user_data.get('cookie_id')

@arena_bp.route('/')
async def arena():
    # Проверяем, зарегистрирован ли персонаж для пользователя
    registered_character = Registrar.query.filter_by(user_id=g.user_id).first()
    if not registered_character:
        return redirect(url_for('viewer.viewer'))

    # Получаем всех зарегистрированных персонажей
    registrations = Registrar.query.all()
    characters = []
    for registration in registrations:
        character = Character.query.get(registration.character_id)
        if character:
            traits = json.loads(character.traits) if character.traits else {}
            traits['Combat'] = character.combat
            traits['Damage'] = character.damage
            traits['Life'] = character.life
            characters.append({
                'user_id': registration.user_id,
                'name': character.name,
                'traits': traits,
                'description': character.description,
                'image_url': character.image_url
            })

    # Получаем последнее состояние арены
    arena = Arena.query.order_by(Arena.date_created.desc()).first()
    arena_image_url = arena.image_url if arena else None


    # Создаем ответ и увеличиваем значение step_read для текущего пользователя
    response = make_response(render_template(
        'arena.html',
        characters=characters,
        arena_image_url=arena_image_url,
        enumerate=enumerate,
        show_start_game_popup=False
    ))

    plm.initial(g.user_id, response)
    
    return response  # Возвращаем ответ с инкрементированным значением в cookies


@arena_bp.route('/get_registered_characters')
async def get_registered_characters():
    try:
        characters = []
        registrations = Registrar.query.all()
        for registration in registrations:
            char = Character.query.filter_by(character_id=registration.character_id).first()
            if char:
                #logger.info(f"Персонаж: {char.name}")
                traits = json.loads(char.traits) if char.traits else {}
                traits.update({
                    "Combat": char.combat,
                    "Damage": char.damage,
                    "Life": char.life
                })
                characters.append({
                    "user_id": registration.user_id,
                    "name": char.name,
                    "traits": traits,
                    "image_url": char.image_url,
                    "description": char.description
                })
        return jsonify(characters)
    except Exception as e:
        logger.error(f"fetching registered characters: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@arena_bp.route('/get_chat_messages/<chat_type>', methods=['GET'])
async def get_chat_messages(chat_type):
    """Универсальная функция для получения сообщений чатов."""
    
    #logger.info(f'==========: {chat_type} ===================')
    # get_message_chatTactics(self, sender, user_id)
    try:
        messages = ""
        # Вызов метода из CoreCommon для получения сообщений
        if chat_type == "arena":
            messages = await mm.get_all_message_chatArena(sender=None, arena_id=None, user_id=None)
            #logger.info(f'==========: {chat_type} messages: {len(messages)} | {messages}')
        elif chat_type == "general":
            messages = await mm.get_all_message_GeneralChat(sender=None, user_id=None)
            #logger.info(f'==========: {chat_type} messages: {len(messages)} | {messages}')
        elif chat_type == "tactics":
            messages = await mm.get_all_message_chatTactics(sender=None, user_id=g.user_id)
           # logger.info(f'==========: {chat_type} messages: {len(messages)} | {messages}')
        else:
            return jsonify({"error": f"Invalid chat type: {chat_type}"}), 400

        #logger.info(f'Chats Update {chat_type}: {len(messages)}')
        
        #test_format = ['test mess1','test mess2','test mess3']
        
        return jsonify(messages)
        
    except Exception as e:
        logger.error(f"Error fetching {chat_type} messages: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@arena_bp.route('/get_arena_image_url/<int:arena_id>', methods=['GET'])
async def get_arena_image_url(arena_id):
    try: 
        arena = Arena.query.get(arena_id)
        if arena and arena.image_url:
            image_url = arena.image_url.replace("\\", "/")
            return jsonify({"image_url": image_url}), 200
        else:
            return jsonify({"error": "Arena image not found"}), 404
    except Exception as e:
        logger.error(f"fetching arena image URL: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@arena_bp.route('/get_latest_arena_image')
async def get_latest_arena_image():
    arena = Arena.query.order_by(Arena.date_created.desc()).first()
    if arena and arena.image_url:
        image_url = arena.image_url.replace("\\", "/")
        return jsonify({"arena_image_url": url_for('static', filename=image_url)})
    return jsonify({"arena_image_url": None})

@arena_bp.route('/get_status', methods=['GET'])
async def get_status():
    
    try:
        battle = plm.battle_status
        timer = plm.timer_status
        game = plm.game_status
        user = plm.user_status        
        #logger.info(f" >>>>>>>> | {game} | {user} | {battle} | {timer}")
        # characters = await sm.get_state('characters')
        # game_status = await sm.get_state('game')
        # arena_status = await sm.get_state('arena')
        # battle_status = await sm.get_state('battle')
        # timer_status = await sm.get_state('timer')

        # if characters:
        #     if game_status or arena_status or battle_status or timer_status:
        #         await plm.battle_start(g.user_id , game_status)
        #         logger.info(f" {characters} | {game_status} | {arena_status} | {battle_status} | {timer_status}")
        await plm.battle_trigger(g.user_id)
        
        return jsonify({
            #'registered_players': registered_players,
            'battle_status': battle,
            'timer_status': timer,
            'game_status': game,
            'user_status': user
        }), 200

    except Exception as e:
        logger.error(f"fetching statuses: {e}")
        return jsonify({"error": "Internal server error"}), 500

@arena_bp.route('/start_async_tasks', methods=['POST'])
async def start_async_tasks():
    return jsonify({'status': 'Tasks started'}), 200

@arena_bp.route('/increment_step')
def increment_step():
    response = make_response()
    response = Cookies.increment_cookie_for_user(response, g.user_id, 'step_read', max_age=86400)
    # Устанавливаем переменную StepRead в значение '1' с временем жизни 1 час (3600 секунд)
    return response

