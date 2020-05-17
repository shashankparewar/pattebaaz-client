import json
import multiprocessing
import random
from functools import partial

import kivy
import websocket
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty, BooleanProperty, ObjectProperty
from kivy.utils import get_color_from_hex

from app import Card, Suit, Number, CardIterator, Game, GamePlayer, GameState
from socket_client import SocketHandler
from handler import GameHandler, WSHandler

kivy.require('1.0.7')

from kivy.config import Config

# 0 being off 1 being on as in true / false
# you can use 0 or 1 && True or False
# Config.set('graphics', 'resizable', True)


red = [1, 0, 0, 1]
green = [0, 1, 0, 1]
blue = [0, 0, 1, 1]
purple = [1, 0, 1, 1]

class CardWidget(BoxLayout):
    is_selected = BooleanProperty()
    is_highlighted = BooleanProperty()

    def __init__(self, card, is_selected, is_clickable, **kwargs):
        super(CardWidget, self).__init__(**kwargs)
        self.colors = [red, green, blue, purple]
        self.card = card
        # self.id = str(uuid.uuid4())
        button = Button(background_normal='cards/{}.png'.format(card.image_name))
        if is_clickable:
            button.bind(on_press=self.button_click)
        self.add_widget(button)
        self.button = button
        self.is_selected = is_selected
        self.is_highlighted = False

    def button_click(self, instance):
        game = GameHandler.get_game_instance()
        card = self.card
        if self.is_selected:
            print("invalid move")
            return
        if self.is_highlighted:
            self.is_highlighted = False
            return
        flag = game.is_valid_move(card)
        if flag:
            self.is_highlighted = True
            print("Current Player", game.current_player_index)
        else:
            print("invalid move")

    def select(self):
        self.is_selected = True

    def unselect(self):
        self.is_selected = False

    def unhighlight(self):
        self.is_highlighted = False


class SuitWidget(FloatLayout):
    def __init__(self, suit, selected_cards, **kwargs):
        super(SuitWidget, self).__init__(**kwargs)
        self.suit = suit
        # self.id = str(uuid.uuid4())
        pos_y = 0
        for i, card in enumerate(CardIterator(Card(suit, Number.ACE), Card(suit, Number.KING))):
            card_widget = CardWidget(card=card, is_selected=True, is_clickable=False,
                                     padding=[0, -100, 0, 0], size_hint=(0.8, 0.1), pos_hint={'x': 0, 'y': pos_y})
            card_widget.bind(is_selected=self.on_is_selected)
            self.add_widget(card_widget, index=i + 1)
            if card in selected_cards:
                card_widget.is_selected = False
            pos_y += 0.05

    def on_is_selected(self, instance: CardWidget, pos):
        if not instance.is_selected:
            instance.button.background_color = instance.card.suit.get_color()

    def select_card(self, card):
        for card_widget in self.children:
            if card_widget.card == card:
                card_widget.unselect()


class GamePlayerWidget(FloatLayout):
    selected_card = ObjectProperty(None)

    def __init__(self, player: GamePlayer, **kwargs):
        super(GamePlayerWidget, self).__init__(**kwargs)
        self.player = player
        game = GameHandler.get_game_instance()
        possible_moves = game.get_possible_moves()
        print(possible_moves)
        pos_y = 0
        for i, card in enumerate(player.get_cards()):
            card_widget = CardWidget(card=card, is_selected=True, is_clickable=True, padding=[0, -100, 20, 0],
                                     size_hint=(1, 0.1), pos_hint={'x': 0, 'y': pos_y})
            card_widget.bind(is_selected=self.on_is_selected)
            card_widget.bind(is_highlighted=self.on_is_highlighted)
            if card in possible_moves:
                card_widget.is_selected = False
            pos_y += 0.06
            self.add_widget(card_widget, index=i + 1)

    def on_is_selected(self, instance, pos):
        if not instance.is_selected:
            instance.button.background_color = get_color_from_hex("#808080")

    def on_is_highlighted(self, instance, pos):
        if instance.is_highlighted:
            instance.button.background_color = instance.card.suit.get_color()
            for child in self.children:
                if isinstance(child, CardWidget) and child.uid != instance.uid and not child.is_selected:
                    child.unhighlight()
            index = 0
        else:
            index = self.player.find_card_index(instance.card)
            if not instance.is_selected:
                instance.button.background_color = get_color_from_hex("#808080")
        self.remove_widget(instance)
        self.add_widget(instance, index=index)

    def select_card(self):
        card = self.selected_card
        for child in self.children:
            if isinstance(child, CardWidget) and child.card == card:
                self.remove_widget(child)


class RootWidget(FloatLayout):
    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)
        socket_handler = SocketHandler()
        ws = websocket.WebSocketApp("ws://127.0.0.1:8081/ws/game/patta/{}/".format(GameHandler.get_game_data()["name"]),
                                    on_message=lambda ws, msg: socket_handler.on_message(ws, msg),
                                    on_error=lambda ws, msg: socket_handler.on_error(ws, msg),
                                    on_close=lambda ws: socket_handler.on_close(ws))
        ws.on_open = lambda ws:socket_handler.on_open(ws)
        self.ws = ws
        p1 = multiprocessing.Process(target=ws.run_forever, args=())
        p1.start()
        Clock.schedule_interval(self.update_game, 5)

    def create_game_widgets(self):
        pos_x = 0.2
        tp = Tab(size_hint=(0.8, 0.75), pos_hint={'x': pos_x, 'y': 0.25})
        th = TabbedPanelHeader(text='Game State')
        tp.add_widget(th)
        layout = FloatLayout()
        pos_x = 0.1
        game = GameHandler.get_game_instance()
        print(game.__dict__)
        for index, suit in enumerate(Suit):
            card_map = game.card_map[index]
            selected_cards = []
            if len(card_map)> 0:
                min_card = Card.from_str(card_map[0])
                max_card = Card.from_str(card_map[1])
                selected_cards = list(CardIterator(min_card, max_card))

            second = SuitWidget(suit, selected_cards, size_hint=(0.2, 1),
                                pos_hint={'x': pos_x, 'y': 0.15})
            pos_x += 0.2
            layout.add_widget(second)
        th.content = layout
        self.add_widget(tp)
        self.state_layout = layout
        game = GameHandler.get_game_instance()
        self.create_player_widget(game.me)
        background_color = get_color_from_hex("#FFFFFF" if game.is_your_turn() else "#808080")
        disabled_color = get_color_from_hex("#FFFFFF")
        self.pass_button = pass_button = Button(text="PASS", pos_hint={'x': 0.4, 'y': 0.05}, size_hint=(0.25, 0.05),
                                                disabled=not game.is_your_turn(),
                                                background_disabled_normal='')
        pass_button.background_color = background_color
        pass_button.disabled_color = disabled_color
        pass_button.bind(on_press=self.pass_move)
        self.add_widget(pass_button, index=0)
        self.move_button = move_button = Button(text="Make Move", size_hint=(0.25, 0.05),
                                                pos_hint={'x': 0.4, 'y': 0.15},
                                                disabled=not game.is_your_turn(),
                                                background_disabled_normal='')
        move_button.background_color = background_color
        move_button.disabled_color = disabled_color
        move_button.bind(on_press=self.on_click)
        self.add_widget(move_button, index=0)

    def update_game_widgets(self):
        game = GameHandler.get_game_instance()
        self.create_player_widget(game.me)
        background_color = get_color_from_hex("#FFFFFF" if game.is_your_turn() else "#808080")
        self.pass_button.disabled = game.is_your_turn()
        self.move_button.disabled = game.is_your_turn()
        self.pass_button.background_color = background_color
        self.move_button.background_color = background_color

    def create_player_widget(self, player):
        pos_x = 0
        tp = Tab(size_hint=(0.2, 0.75), pos_hint={'x': pos_x, 'y': 0.25})
        th = TabbedPanelHeader(text=player.player["name"])
        tp.add_widget(th)
        player_widget = GamePlayerWidget(player=player)
        player_widget.bind(selected_card=self.on_selected)
        th.content = player_widget
        self.add_widget(tp)
        self.player_widget = player_widget

    def on_selected(self, instance, card):
        suit = card.suit
        self.make_move(card)

    def on_click(self, instance):
        game_widget = self.player_widget
        for child in game_widget.children:
            if getattr(child, "is_highlighted", False):
                game_widget.selected_card = child.card

    def make_move(self, card=None, pass_move=False):
        ws = self.ws
        game = GameHandler.get_game_instance()
        if pass_move:
            card = "pass"
        else:
            card = card.str
        ws.send(json.dumps({
            'message': card
        }))
        def my_callback(instance):
            print('Popup', instance, 'is being dismissed but is prevented!')
            ws.close()
            exit(1)
        if game.is_ended:
            popup = Popup(content=Label(text='Player {} wins'.format(game.current_player_index)))
            popup.bind(on_dismiss=my_callback)
            popup.open()

    def pass_move(self, instance):
        self.make_move(pass_move=True)

    def delete_all_widgets(self):
        for widget in self.children:
            self.remove_widget(widget)

    def update_game(self, dt):
        print(GameHandler.get_game_data())
        game = GameHandler.get_game_instance()
        if not game:
            return
        self.delete_all_widgets()
        if not game.is_ended:
            self.create_game_widgets()


class Tab(TabbedPanel):
    def __init__(self, **kwargs):
        super(Tab, self).__init__(**kwargs)


class PattebaazApp(App):
    def __init__(self, **kwargs):
        super(PattebaazApp, self).__init__(**kwargs)

    def build(self):
        widget = RootWidget(size=(400, 400))
        return widget
