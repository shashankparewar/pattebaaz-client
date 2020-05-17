from enum import Enum, IntEnum
import random


class Suit(Enum):
    HEART = "Hearts"
    DIAMOND = "Diamonds"
    SPADE = "Spades"
    CLUB = "Clubs"

    def __str__(self):
        return self.name

    @property
    def val(self):
        return {
            Suit.HEART: 0,
            Suit.DIAMOND: 1,
            Suit.SPADE: 2,
            Suit.CLUB: 3
        }.get(self, 0)

    @property
    def char(self):
        return {
            Suit.HEART: 'H',
            Suit.DIAMOND: 'D',
            Suit.SPADE: 'S',
            Suit.CLUB: 'C'
        }.get(self, 'H')

    @staticmethod
    def from_str(string):
        return {
            'H': Suit.HEART,
            'D': Suit.DIAMOND,
            'S': Suit.SPADE,
            'C': Suit.CLUB
        }.get(string, Suit.HEART)

    @staticmethod
    def from_val(val):
        return {
            0: Suit.HEART,
            1: Suit.DIAMOND,
            2: Suit.SPADE,
            3: Suit.CLUB
        }.get(val, Suit.HEART)

    def get_color(self):
        return {
            Suit.HEART: [1, 0, 0, 1],
            Suit.DIAMOND: [0, 1, 0, 1],
            Suit.SPADE: [0, 0, 1, 1],
            Suit.CLUB: [1, 0, 1, 1]
        }.get(self, [1, 1, 1, 0])


class Number(IntEnum):
    ACE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13

    def __str__(self):
        return self.name

    @property
    def char(self):
        if self not in [Number.ACE, Number.JACK, Number.QUEEN, Number.KING]:
            return str(self.value)
        return {
            Number.ACE: 'A',
            Number.JACK: 'J',
            Number.QUEEN: 'Q',
            Number.KING: 'K'
        }.get(self, '')

    @staticmethod
    def from_str(string):
        if string not in ['A', 'J', 'Q', 'K']:
            val = int(string)
            return Number(val)

        return {
            'A': Number.ACE,
            'J': Number.JACK,
            'Q': Number.QUEEN,
            'K': Number.KING
        }.get(string, Number.ACE)


class Card(object):
    def __init__(self, suit, number):
        self.suit = suit
        self.number = number

    def __repr__(self):
        return "{}:{}".format(str(self.suit), str(self.number))

    def __eq__(self, other):
        return other and (self.suit == other.suit) and \
               (self.number == other.number)

    def __le__(self, other):
        return other and (self.suit == other.suit) and \
               (self.number <= other.number)

    # def __cmp__(self, other):
    #     if not other:
    #         return 1
    #     if self.suit != other.suit:
    #         return self.suit.val - other.suit.val
    #     return self.number.value - other.number.value

    def get_next_card(self):
        if self.number.value == 13:
            return None
        else:
            return self.__class__(self.suit, Number(self.number + 1))

    def get_prev_card(self):
        if self.number.value == 1:
            return None
        else:
            return self.__class__(self.suit, Number(self.number - 1))

    @property
    def str(self):
        return "{}:{}".format(self.number.char, self.suit.char)

    @property
    def image_name(self):
        return "{}{}".format(self.number.char, self.suit.char)


    def __hash__(self):
        return self.suit.val * 13 + self.number.value - 1

    @staticmethod
    def from_str(string):
        parts = string.split(":")
        number = Number.from_str(parts[0])
        suit = Suit.from_str(parts[1])
        return Card(suit, number)


class CardIterator:
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.cur = start

    def __iter__(self):
        return self

    def __next__(self):
        if self.cur and self.cur <= self.end:
            next = self.cur.get_next_card()
            cur = self.cur
            self.cur = next
            return cur
        raise StopIteration


class Deck(object):
    def __init__(self):
        self.cards = []
        for suit in Suit:
            for num in Number:
                card = Card(suit, num)
                self.cards.append(card)

    def shuffle(self):
        random.shuffle(self.cards)

    def get_cards(self, start, length):
        return self.cards[start: start + length]

    @property
    def length(self):
        return len(self.cards)

    @property
    def num_suits(self):
        return 4

    @property
    def num_cards_per_suit(self):
        return 13


class Player:
    def __init__(self, player):
        self.player = player


class GamePlayer:
    def __init__(self, player, cards):
        self.player = player
        self.cards = cards

    @classmethod
    def from_json(cls, json):
        cards = json.get("cards",[])
        cards = [Card.from_str(card) for card in cards]
        self = cls(json, cards)
        return self

    def update_cards(self, cards):
        self.cards = cards

    def find_card_index(self, card):
        return self.cards.index(card)

    def get_cards(self):
        return self.cards


class GameState(Enum):
    NOT_STARTED = "NOT STARTED"
    STARTED = "STARTED"
    ENDED = "ENDED"


class GameMove(IntEnum):
    MOVE_FIRST = 0
    MOVE_FIRST_SUIT = 1
    MOVE_MIN = 2
    MOVE_MAX = 3
    MOVE_PASS = 4


class Game:
    def __init__(self, players, me, current_player_id, state, card_map, card_count=0, possible_moves=[]):
        self.game_players = sorted([Player(player) for player in players], key=lambda x: x.player["index"])
        self.me = GamePlayer.from_json(me)
        self.current_player_index = current_player_id
        self.state = GameState(state)
        self.card_map = card_map
        self.card_count = card_count
        self.possible_moves = possible_moves

    @property
    def players(self):
        return self.game_players

    def set_possible_moves(self, possible_moves):
        self.possible_moves = possible_moves

    def get_possible_moves(self):
        return self.possible_moves

    @property
    def current_player(self):
        return self.game_players[self.current_player_index]

    def set_current_player(self, current_player_index):
        self.current_player_index = current_player_index

    def make_move(self, card=None, pass_move=False):
        pass

    def is_valid_move(self, card):
        return self.me.player["index"] == self.current_player_index

    @property
    def is_ended(self):
        self.state == GameState.ENDED

    def is_your_turn(self):
        return self.me.player["index"] == self.current_player_index

    @classmethod
    def from_json(cls, json):
        return cls(**json)

    def update(self, json):
        self.me = GamePlayer.from_json(json["me"])
        self.current_player_index = json["current_player_id"]
        self.state = GameState(json["state"])
        self.card_map = json["card_map"]
        self.card_count = json["card_count"]
        self.possible_moves = json["possible_moves"]
        return self

