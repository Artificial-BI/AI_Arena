import asyncio
from models import Character, ArenaChatMessage, GeneralChatMessage, TacticsChatMessage, Registrar, Arena, PreRegistrar, Player
import logging
import json
from extensions import db
from core import ArenaManager, BattleManager
from load_user import load_user
import sys
from config import Config
import random
import time
# Опускаем инициализацию основного event loop


battle_manager = BattleManager()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArenaInterface:
    def __init__(self, user_id):
        self.assistant = None
        self.user_id = user_id
        
    def get_state(self):
        player = Player.query.filter_by(user_id=self.user_id).first()

        if player and player.last_selected_character_id and player.current_status == 'registered':
            check_id = test_character_id(player.last_selected_character_id)
            character_id = player.last_selected_character_id
    
        
    def test_character_id(self, character_id):
        stat.cur_state = 'Test character ID'
        return Registrar.query.filter_by(character_id=character_id).first() is not None

    def check_battle(self):
        logger.info(f" ---------- BATTLE: {battle_manager.battle_in_progress} -------------- ")
        return battle_manager.battle_in_progress

    async def add_player_to_waiting_list(self, character_id, user_id):
        pre_registration = PreRegistrar(character_id=character_id, user_id=user_id)
        db.session.add(pre_registration)
        db.session.commit()
        logger.info(f"Игрок {user_id} добавлен в лист ожидания новой битвы.")

    def redirect_to_viewer(self):
        return redirect(url_for('viewer_bp.viewer'))

    async def backward_timer(self):
        cur_sec = config.WAIT_COUNT
        while cur_sec > 0:
            logger.info(f"Ожидание дополнительных игроков в течение {config.WAIT_COUNT} осталось: {cur_sec} секунд...")
            stat.cur_state = f"Waiting players:  {config.WAIT_COUNT}  -  {cur_sec} sec..."
            await asyncio.sleep(1)
            cur_sec -= 1

    async def test_function(self):
        logger.info("Test function started")
        
        for i in range(5):
            logger.info(f"Test function iteration {i + 1}")
            await asyncio.sleep(1)  # Асинхронная пауза на 1 секунду
        
        logger.info("Test function completed")


    async def start_waiting_for_players(self):
        count_sec = 0
        logger.info(" ---------- START WAITING PLAYERS -------------- ")
        stat.cur_state = "START WAITING PLAYERS"
        while True:
            registered_players = Registrar.query.count()
            if registered_players >= config.PLAYER_COUNT:
            # logger.info(f"All players have joined: {registered_players}/{config.PLAYER_COUNT}")
                break  # Достаточно игроков, выходим из ожидания

            # Обновление статуса ожидания в переменной состояния
            stat.cur_state = f'Waiting players. {registered_players}/{config.PLAYER_COUNT} | {count_sec} sec.'
        # logger.info(stat.cur_state)

            if count_sec >= 20:
                #logger.info(f"Timeout reached. Players joined: {registered_players}/{config.PLAYER_COUNT}")
                break
            count_sec += 1
            #await asyncio.sleep(0.1)  # Асинхронная пауза на 1 секунду
            time.sleep(1)


    async def generate_arena(self):
        if config.ARENA_MODE == 'random':
            stat.cur_state = 'Arena random'
            logger.info(f" ---------- ARENA RANDOM -------------- ") 
            arena_cnt = Arena.query.count()
            if arena_cnt > 0:
                random_offset = random.randint(0, arena_cnt - 1)
                arena = Arena.query.offset(random_offset).first()
            else:
                arena_manager = ArenaManager()
                arena = arena_manager.generate_arena()
                db.session.add(arena)
                db.session.commit()
        else:
            stat.cur_state = 'Arena generated'
            logger.info(f" ---------- ARENA GENERATE -------------- ")
            arena_manager = ArenaManager()
            arena = arena_manager.generate_arena()
            db.session.add(arena)
            db.session.commit()
        
        # Добавляем небольшую задержку для имитации создания арены
        #await asyncio.sleep(2)

        return arena


    async def registration_to_db(self, user_id, character_id):
        existing_registration = Registrar.query.filter_by(user_id=user_id, arena_id=1).first()
        if existing_registration:
            if existing_registration.character_id != character_id:
                existing_registration.character_id = character_id
                db.session.commit()
        else:
            new_registration = Registrar(
                user_id=user_id, 
                character_id=character_id, 
                arena_id=1
            )
            db.session.add(new_registration)
            db.session.commit()

    async def clear_reg_db(self):
        regs = Registrar.query.all()
        logger.info(f"del Registrar: {regs}")
        if regs:
            for reg in regs:
                db.session.delete(reg)
            db.session.commit()

    async def to_arena(self):
        logger.info(f" ---------- TO ARENA -------------- ")   
        selected_character = None
        player = Player.query.filter_by(user_id=g.user_id).first()
        check_id = None
        character_id = None
        
        if player and player.last_selected_character_id and player.current_status == 'registered':
            check_id = test_character_id(player.last_selected_character_id)
            character_id = player.last_selected_character_id
        
        character = Character.query.get(character_id)
        if character and character.user_id == g.user_id:
            selected_character = character
        
        logger.info(f" ---------- STATE {player.current_status} CHECK: {check_id} -------------- ") 
        
        tasks = []
        if check_id:
            logger.info(f" ---------- PLAYER REG -------------- ")
            check_batl = check_battle()
            if not check_batl:
                if config.PLAYER_COUNT == 0:
                    battle_manager.add_autoFighter()
                else:
                    await start_waiting_for_players() 
                    await generate_arena()
                    # tasks.append(asyncio.create_task(start_waiting_for_players()))
                    # tasks.append(asyncio.create_task(generate_arena()))

                # if config.WAIT_COUNT > 0:
                #     stat.cur_state = 'wait players'
                #     tasks.append(asyncio.create_task(backward_timer()))

            stat.cur_state = 'START BATTLE'
            
            await asyncio.gather(*tasks)
            return None, selected_character
        else:
            logger.info(f" ---------- PLAYER NOT REG -------------- ")
            check_batl = check_battle()
            if check_batl:
                await add_player_to_waiting_list(g.user_id, character_id)
                stat.cur_state = 'add player to waiting list'
                return None, selected_character
            else:
                pers = PreRegistrar.query.filter_by(character_id=character_id).first()
                logger.info(f"PreRegistrar: {pers}")
                if pers:
                    new_registration = Registrar(character_id=pers.character_id, user_id=g.user_id, arena_id=1)
                    db.session.add(new_registration)
                    db.session.delete(pers)
                    db.session.commit()
                else:
                    logger.info(f" ---------- PLAYER NEW REGISTRATION -------------- ")
                    new_registration = Registrar(character_id=character_id, user_id=g.user_id, arena_id=1)
                    db.session.add(new_registration)   
                    db.session.commit()
        
                if config.PLAYER_COUNT == 0:
                    battle_manager.add_autoFighter()
                else:
                    logger.info(f" ---------- START WAITING PLAYERS | -------------- ")
                    # task = asyncio.create_task(start_waiting_for_players())
                    # tasks.append(asyncio.create_task(generate_arena()))
                    await start_waiting_for_players()  # Напрямую вызываем асинхронную функцию
                    await generate_arena()
                    
                #if config.WAIT_COUNT > 0:
                    #stat.cur_state = 'wait players'
                    #tasks.append(asyncio.create_task(backward_timer()))
                stat.cur_state = 'Start '
                await asyncio.gather(*tasks)
                return None, selected_character

    def start_battle(self):
        stat.cur_state = 'Start battle'
        battle_manager.start_battle()     