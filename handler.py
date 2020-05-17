from app import Game


class GameHandler(object):
    @classmethod
    def get_game_data(cls):
        return cls.game

    @classmethod
    def set_game_data(cls, game):
        cls.game = game

    @classmethod
    def update_data(cls, key, data):
        cls.game[key] = data

    @classmethod
    def get_game_instance(cls):
        game_data = cls.game.get("data")
        if not game_data:
            return game_data
        return Game.from_json(game_data)

class WSHandler():
    @classmethod
    def get_ws(cls):
        return cls.ws

    @classmethod
    def set_ws(cls, ws):
        cls.ws = ws

    @classmethod
    def send_message(cls, message):
        cls.ws.send(message)