import logging
import zmq
import threading
import time
from config import Config
# from models import db
# from chats_models import ReadStatus, ArenaChatMessage, TacticsChatMessage, GeneralChatMessage

# --- multiproc.py ---

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StatusManager:
    def __init__(self):
        self.context = zmq.Context()
        self.conf = Config()
        self.states = {}  # Dictionary to store the states

        # Socket for sending requests
        self.req_socket = self.context.socket(zmq.REQ)
        self.req_socket.connect(self.conf.STAT_PORT)

    def set_state(self, name, state, description):
        """Sets a state with the provided name, state, and description."""
        try:
            self.states[name] = {"state": state, "description": description, "timestamp": time.time()}
            self.req_socket.send_json({
                "command": "set_state",
                "name": name,
                "state": state,
                "description": description
            })
            response = self.req_socket.recv_json()
            #logger.info(f"Response from server: {response}")
        except Exception as e:
            logger.error(f"Failed to set state: {e}")

    def get_state(self, name):
        """Gets the state for the given name."""
        try:
            self.req_socket.send_json({"command": "get_state", "name": name})
            response = self.req_socket.recv_json()
            return response.get("state", None)
        except Exception as e:
            #logger.error(f"Failed to get state: {e}")
            return {"not state"}

    def start_server(self):
        """Starts the ZeroMQ server for handling state requests."""
        socket = self.context.socket(zmq.REP)
        socket.bind(self.conf.STAT_PORT)
        
        logger.info(f"Starting ZeroMQ server on {self.conf.STAT_PORT}...")

        while True:
            try:
                message = socket.recv_json()
                #logger.info(f"Received request: {message}")
                response = self.handle_message(message)
                socket.send_json(response)
            except Exception as e:
                logger.error(f"Error in server loop: {e}")

    def handle_message(self, message):
        """Handles incoming messages and manages state accordingly."""
        command = message.get("command")
        if command == "set_state":
            name = message.get("name")
            state = message.get("state")
            description = message.get("description")
            self.states[name] = {"state": state, "description": description, "timestamp": time.time()}
            return {"status": "ok", "message": f"State for {name} set to {state}"}
        elif command == "get_state":
            name = message.get("name")
            state_info = self.states.get(name, None)
            if state_info:
                return {"status": "ok", "state": state_info["state"]}
            else:
                return {"status": "error", "message": f"No state found for {name}"}
        else:
            return {"status": "error", "message": "Unknown command"}

