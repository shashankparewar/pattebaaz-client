import json
import multiprocessing
import sys
from multiprocessing import Manager
from app import GameState, Game, Card
from handler import GameHandler, WSHandler
import websocket

try:
    import thread
except ImportError:
    import _thread as thread
import time
class SocketHandler():
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method. """

        if SocketHandler.__instance == None:
            SocketHandler()
        return SocketHandler.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if SocketHandler.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            SocketHandler.__instance = self

    def on_message(self, ws, message):
        message = json.loads(message)
        print("message received on socket:", message)
        game_json = message["game"]
        game_json["me"] = message["me"]
        game_json["possible_moves"] = [Card.from_str(card) for card in message["possible_moves"] or []]
        self.update_shared_data("type", message["type"])
        self.update_shared_data("data", game_json)
        print(game_json)
        print(GameHandler.get_game_instance().__dict__)
        if message["type"] == "game_start" and not GameHandler.get_game_data().get("is_started", False):
            GameHandler.update_data("is_started", True)
            ws.close()

    @classmethod
    def update_shared_data(cls, key, data):
        GameHandler.update_data(key, data)


    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
        print("### closed ###")

    def on_open(self, ws):
        WSHandler.set_ws(ws)
        print(WSHandler.get_ws())
        print("waiting for game to start")


if __name__ == "__main__":
    from main import PattebaazApp
    manager = Manager()
    d = manager.dict()
    game = GameHandler.set_game_data(d)
    websocket.enableTrace(True)
    name = sys.argv[1]
    GameHandler.update_data("name", name)
    socket_handler = SocketHandler()
    ws = websocket.WebSocketApp("ws://127.0.0.1:8081/ws/game/patta/{}/".format(name),
                                on_message=lambda ws, msg: socket_handler.on_message(ws, msg),
                                on_error=lambda ws, msg: socket_handler.on_error(ws, msg),
                                on_close=lambda ws: socket_handler.on_close(ws))
    ws.on_open = lambda ws:socket_handler.on_open(ws)

    p1 = multiprocessing.Process(target=ws.run_forever, args=())
    p1.start()
    p1.join()
    app = PattebaazApp()
    app.run()
