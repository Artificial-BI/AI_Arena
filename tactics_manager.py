import logging
import asyncio
from flask import current_app
from models import Character, TacticsChatMessage, Registrar, Arena, ArenaChatMessage, GeneralChatMessage
from extensions import db
from gemini import GeminiAssistant

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TacticsManager:
    def __init__(self, fighter_instance, loop=None):
        self.assistant = None
        self.running = False
        self.fighters = {}
        self.fighter = fighter_instance
        self.loop = loop or asyncio.get_event_loop()

    def add_fighter(self, user_id):
        self.fighters[user_id] = None  # Initialize without character data

    def _initialize_assistant(self):
        if self.assistant is None:
            self.assistant = GeminiAssistant("tactician")

    async def gather_arena_info(self, arena_id, user_id):
        """Gathers information about arena characteristics, opponents' recent moves, and character characteristics."""
        with current_app.app_context():
            arena = Arena.query.get(arena_id)
            if not arena:
                logger.error(f"Arena with ID {arena_id} not found")
                return None, None

            registration = Registrar.query.filter_by(user_id=user_id).first()
            if not registration:
                logger.error(f"Character for user {user_id} not found")
                return None, None

            character = Character.query.get(registration.character_id)
            if not character:
                logger.error(f"Character with ID {registration.character_id} not found")
                return None, None

            opponent_moves = ArenaChatMessage.query.filter(
                ArenaChatMessage.user_id != user_id, 
                ArenaChatMessage.arena_id == arena_id
            ).order_by(ArenaChatMessage.timestamp.desc()).all()

            opponent_moves_text = "\n".join([f"{move.sender}: {move.content}" for move in opponent_moves])
            return arena, character, opponent_moves_text

    async def generate_tactics(self, user_id):
        """Generates tactical recommendations for a character."""
        logger.info(f"Starting tactical recommendations generation process for user {user_id}")

        self._initialize_assistant()
        self.running = True

        while self.running:
            with current_app.app_context():
                registration = Registrar.query.filter_by(user_id=user_id).first()
                if not registration:
                    logger.error(f"Character for user {user_id} not found")
                    return

                arena, character, opponent_moves_text = await self.gather_arena_info(registration.arena_id, user_id)
                
                if not arena or not character:
                    return

                prompt = f"Arena atmosphere: {arena.description}\nArena parameters: {arena.parameters}\n\n"
                prompt += f"Character name: {character.name}\nCombat: {character.combat}, Damage: {character.damage}, Life: {character.life}\n\n"
                if opponent_moves_text:
                    prompt += f"Opponents' recent moves:\n{opponent_moves_text}\n\n"
                prompt += "Generate tactical recommendations for the character's next move."

                try:
                    response = await self.assistant.send_message(prompt)
                except Exception as e:
                    logger.error(f"Error sending message for {character.name}: {e}")
                    await asyncio.sleep(10)
                    continue

                if not response.strip():
                    logger.error("Received empty response from assistant")
                    await asyncio.sleep(10)
                    continue
               
                tactics_message = TacticsChatMessage(content=response, sender="tactician", user_id=user_id)
                db.session.add(tactics_message)
                db.session.commit()

                logger.info(f"Tactical recommendation for {character.name} saved.")

                while True:
                    await asyncio.sleep(1)
                    latest_tactics_message = TacticsChatMessage.query.filter_by(
                        user_id=user_id, sender="tactician"
                    ).order_by(TacticsChatMessage.timestamp.desc()).first()
                    if latest_tactics_message and latest_tactics_message.read_status == 1:
                        logger.info(f"Recommendation for {character.name} read by the fighter, generating new one")
                        break
                    await asyncio.sleep(10)

            await asyncio.sleep(10)  # Periodic execution

    def stop(self):
        self.running = False
        logger.info("Tactical recommendations generation process stopped")
        
    async def generate_tactics_and_moves(self, user_id, num_moves, arena):
        logger.info(f"Starting tactics and moves generation for user {user_id}")

        self._initialize_assistant()
        self.running = True

        for _ in range(num_moves):
            if not self.running:
                break
            
            # Gathering information about the arena and character
            arena, character, opponent_moves_text = await self.gather_arena_info(arena.id, user_id)
            if not arena or not character:
                return

            # Generating tactics
            prompt = f"Arena atmosphere: {arena.description}\nArena parameters: {arena.parameters}\n\n"
            prompt += f"Character name: {character.name}\nCombat: {character.combat}, Damage: {character.damage}, Life: {character.life}\n\n"
            if opponent_moves_text:
                prompt += f"Opponents' recent moves:\n{opponent_moves_text}\n\n"
            prompt += "Generate tactical recommendations for the character's next move."

            try:
                response = await self.assistant.send_message(prompt)
            except Exception as e:
                logger.error(f"Error sending message for {character.name}: {e}")
                await asyncio.sleep(10)
                continue

            if not response.strip():
                logger.error("Received empty response from assistant")
                await asyncio.sleep(10)
                continue
            
            # Saving tactical message
            tactics_message = TacticsChatMessage(content=response, sender="tactician", user_id=user_id)
            db.session.add(tactics_message)
            db.session.commit()

            # Getting player input
            player_message = await self.get_player_input(user_id)
            player_content = player_message.content if player_message else ""

            # Generating fighter's move using the Fighter instance
            await self.fighter.generate_fighter_move(character, arena, response, player_content)

            # Marking messages as read
            tactics_message.read_status = 1
            if player_message:
                player_message.read_status = 1
            db.session.commit()

        logger.info(f"Fighter {character.name} has completed their moves.")
    
    async def get_player_input(self, user_id):
        """Gets player input if available."""
        with current_app.app_context():
            player_message = TacticsChatMessage.query.filter_by(
                user_id=user_id, sender='user', read_status=0
            ).order_by(TacticsChatMessage.timestamp.desc()).first()
            if player_message:
                logger.info(f"Player input received for user {user_id}: {player_message.content}")
                return player_message
            return None

class Fighter:
    def __init__(self, loop=None):
        self.assistant = None
        self.running = False
        self.fighters = {}
        self.moves_count = {}
        self.loop = loop or asyncio.get_event_loop()

    def message_to_Arena(self, _message):
        set_message = ArenaChatMessage(content=_message, sender='system', user_id=None, read_status=0)
        db.session.add(set_message)
        db.session.commit()

    def add_fighter(self, user_id):
        self.fighters[user_id] = None  # Initialize without character data
        self.moves_count[user_id] = 0  # Initialize the move counter for the fighter

    def _initialize_assistant(self):
        if self.assistant is None:
            self.assistant = GeminiAssistant("fighter")

    async def generate_fighter_move(self, character, arena, tactics_content, player_content):
        """Generates the fighter's move based on the tactician's instructions and player's input."""
        self._initialize_assistant()

        prompt = f"Arena atmosphere: {arena.description}\nArena parameters: {arena.parameters}\n\n"
        prompt += f"Character name: {character.name}\nCharacter traits: {character.traits}\n\n"
        prompt += f"Tactician's advice: {tactics_content}\n"
        if player_content:
            prompt += f"Player's wishes: {player_content}\n\n"
        prompt += "Generate the character's next move based on the information above."

        try:
            response = await self.assistant.send_message(prompt)
        except Exception as e:
            logger.error(f"Error sending message for {character.name}: {e}")
            return "Error sending message"

        if not response.strip():
            logger.error("Received empty response from assistant")
            return "Received empty response from assistant"

        logger.info(f"Generated fighter move: {response}")

        with current_app.app_context():
            self.message_to_Arena(f"--- Step fighter: {character.name} ---")
            fighter_move = ArenaChatMessage(content=response, sender="fighter", user_id=character.user_id, arena_id=arena.id)
            db.session.add(fighter_move)
            db.session.commit()

            # Check that the record is saved
            saved_move = ArenaChatMessage.query.filter_by(content=response, user_id=character.user_id, arena_id=arena.id).first()
            if saved_move:
                logger.info(f"Fighter's move for {character.name} successfully saved to the database.")
            else:
                logger.error(f"Error: Fighter's move for {character.name} was not found in the database after commit!")

        return "Fighter move successfully created"

    async def wait_for_instructions(self, user_id):
        """Waits for tactical instructions from the tactician."""
        while self.running:
            with current_app.app_context():
                tactics_message = TacticsChatMessage.query.filter_by(
                    user_id=user_id, sender='tactician', read_status=0
                ).order_by(TacticsChatMessage.timestamp.desc()).first()
                if tactics_message:
                    logger.info(f"Tactical recommendation received for Fighter: {user_id}")
                    return tactics_message

            await asyncio.sleep(1)

    async def get_player_input(self, user_id):
        """Gets player input if available."""
        with current_app.app_context():
            player_message = TacticsChatMessage.query.filter_by(
                user_id=user_id, sender='user', read_status=0
            ).order_by(TacticsChatMessage.timestamp.desc()).first()
            if player_message:
                logger.info(f"Player input received for fighter {user_id}: {player_message.content}")
                return player_message
            return None

    async def generate_tactics_and_moves(self, user_id, num_moves, arena):
        logger.info(f"Starting tactics and moves generation for user {user_id}")

        self._initialize_assistant()
        self.running = True

        for _ in range(num_moves):
            if not self.running:
                break

            # Gathering information about the arena and character
            arena, character, opponent_moves_text = await self.gather_arena_info(arena.id, user_id)
            if not arena or not character:
                return

            # Generating tactics
            prompt = f"Arena atmosphere: {arena.description}\nArena parameters: {arena.parameters}\n\n"
            prompt += f"Character name: {character.name}\nCharacter traits: {character.traits}\n\n"
            if opponent_moves_text:
                prompt += f"Opponents' recent moves:\n{opponent_moves_text}\n\n"
            prompt += "Generate tactical recommendations for the character's next move."

            try:
                response = await self.assistant.send_message(prompt)
            except Exception as e:
                logger.error(f"Error sending message for {character.name}: {e}")
                await asyncio.sleep(10)
                continue

            if not response.strip():
                logger.error("Received empty response from assistant")
                await asyncio.sleep(10)
                continue

            # Saving tactical message
            tactics_message = TacticsChatMessage(content=response, sender="tactician", user_id=user_id)
            db.session.add(tactics_message)
            db.session.commit()

            # Getting player input
            player_message = await self.get_player_input(user_id)
            player_content = player_message.content if player_message else ""

            # Generating fighter's move using the Fighter instance
            await self.generate_fighter_move(character, arena, response, player_content)

            # Marking messages as read
            tactics_message.read_status = 1
            if player_message:
                player_message.read_status = 1
            db.session.commit()

        logger.info(f"Fighter {character.name} has completed their moves.")

    def stop(self):
        """Stops the fighter's actions."""
        self.running = False
        logger.info("Fighter's actions have been stopped.")
