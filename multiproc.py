import logging
import zmq
from config import Config

# --- multiproc.py ---

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StatusManager:
    def __init__(self):
        self.context = zmq.Context()
        self.conf = Config()

        # Сокет для отправки запросов
        self.req_socket = self.context.socket(zmq.REQ)
        self.req_socket.connect(self.conf.STAT_PORT)

    def set_state(self, name, state, description):
        try:
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
        try:
            self.req_socket.send_json({
                "command": "get_state",
                "name": name
            })
            response = self.req_socket.recv_json()
            #logger.info(f"Response from server: {response}")
            return response.get("state")
        except Exception as e:
            logger.error(f"Failed to get state: {e}")
            return None

    @staticmethod
    def start_server():
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind(Config().STAT_PORT)
        
        logger.info("Starting ZeroMQ server...")

        while True:
            try:
                message = socket.recv_json()
                #logger.info(f"Received request: {message}")
                response = StatusManager.handle_message(message)
                socket.send_json(response)
            except Exception as e:
                logger.error(f"Error in server loop: {e}")

    @staticmethod
    def handle_message(message):
        command = message.get("command")
        if command == "set_state":
            name = message.get("name")
            state = message.get("state")
            description = message.get("description")
            # Логика обработки сохранения состояния
            return {"status": "ok", "message": f"State for {name} set to {state}"}
        elif command == "get_state":
            name = message.get("name")
            # Логика обработки получения состояния
            return {"status": "ok", "state": "some_state_value"}
        else:
            return {"status": "error", "message": "Unknown command"}
