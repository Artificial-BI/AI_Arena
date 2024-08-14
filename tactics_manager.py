import logging
import asyncio
from flask import current_app
from models import Character, TacticsChatMessage, Registrar, Arena, ArenaChatMessage, GeneralChatMessage
from extensions import db
from gemini import GeminiAssistant

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def message_to_Arena(_message, _sender=None, _user_id=None, _name=None, _arena_id=None):
    if _name is None or _arena_id is None:
        logger.error("Cannot add message to arena chat: 'name' and 'arena_id' must not be None.")
        return

    set_message = ArenaChatMessage(
        content=f'{_message}\n', 
        sender=_sender, 
        user_id=_user_id, 
        name=_name, 
        arena_id=_arena_id, 
        read_status=0
    )
    db.session.add(set_message)
    db.session.commit()


class TacticsManager:
    def __init__(self, loop=None):
        self.assistant = None
        self.running = False
        self.tactic = {}
        self.loop = loop or asyncio.get_event_loop()

    def add_tactic(self, user_id):
        self.tactic[user_id] = None  # Initialize without character data

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
        self.running = True

        with current_app.app_context():
            registration = Registrar.query.filter_by(user_id=user_id).first()
            if not registration:
                logger.error(f"Character for user {user_id} not found")
                return

            arena, character, opponent_moves_text = await self.gather_arena_info(registration.arena_id, user_id)
            
            if not arena or not character:
                return

            prompt = f"Arena atmosphere: {arena.description}\nArena parameters: {arena.parameters}\n\n"
            prompt += f"Character name: {character.name}\ntraits: {character.traits}, Life: {character.life}\n\n"
            if opponent_moves_text:
                prompt += f"Opponents' recent moves:\n{opponent_moves_text}\n\n"
            prompt += "Generate tactical recommendations for the character's next move."

            try:
                assistant = GeminiAssistant("tactician")
                response = await assistant.send_message(prompt)
            except Exception as e:
                logger.error(f"Error sending message for {character.name}: {e}")

            if not response.strip():
                logger.error("Received empty response from assistant")
                await asyncio.sleep(10)
            
            tactics_message = TacticsChatMessage(content=response, sender="tactician", user_id=user_id)
            db.session.add(tactics_message)
            db.session.commit()

            logger.info(f"Tactical recommendation for {character.name} saved.")
    
        return response, character
    

class FighterManager:
    def __init__(self, loop=None):
        self.assistant = None
        self.running = False
        self.fighters = {}
        self.moves_count = {}
        self.loop = loop or asyncio.get_event_loop()

    # def message_to_Arena(self, _message, _sender, _user_id):
    #     set_message = ArenaChatMessage(content=_message, sender=_sender, user_id=_user_id, read_status=0)
    #     db.session.add(set_message)
    #     db.session.commit()

    def add_fighter(self, user_id):
        self.fighters[user_id] = None  # Initialize without character data
        self.moves_count[user_id] = 0  # Initialize the move counter for the fighter
# char['user_id'], character ,tactical_recommendation, user_expectation, step_move, arena
    async def generate_fighter(self, user_id, character, tactical_recommendation, user_expectation, step_move, arena):
        """Generates the fighter's move based on the tactician's instructions and player's input."""
        assistant = GeminiAssistant("fighter")

        prompt = f"Character name: {character.name}\nCharacter traits: {character.traits} Life: {character.life}\n\n"
        prompt += f"Tactician's advice: {tactical_recommendation}\n"
        player_content = self.get_player_input(user_id)
        if player_content:
            prompt += f"Player's wishes: {player_content}\n\n"
        prompt += "Generate the character's next move based on the information above."

        await asyncio.sleep(user_expectation)

        try:
            response = await assistant.send_message(prompt)
        except Exception as e:
            logger.error(f"Error sending message for {character.name}: {e}")
            return "Error sending message"

        if not response.strip():
            logger.error("Received empty response from assistant")
            return "Received empty response from assistant"

        logger.info(f"step: {step_move}  Generated fighter move: {response}")

        with current_app.app_context():
            message_to_Arena(f"fighter: {character.name} step: {step_move} |/n {response}", _sender="fighter", _user_id = character.user_id, _name=character.name, _arena_id=arena.id)
            # Check that the record is saved
            saved_move = ArenaChatMessage.query.filter_by(content=response, user_id=character.user_id, arena_id=arena.id).first()
            if saved_move:
                logger.info(f"Fighter's move for {character.name} successfully saved to the database.")
            else:
                logger.error(f"Error: Fighter's move for {character.name} was not found in the database after commit!")

        return "Fighter move successfully created"

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

    
