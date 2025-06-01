import os
import sys
sys.path.append(os.path.dirname(__file__))

from game import Game

class Player:
    def __init__(self, qq_number, chess_id, rival):
        self.game = None
        self.id = qq_number
        self.chess_id = chess_id
        self.rival = rival

    def set_game(self, game: Game):
        self.game = game

    def chess_down(self, x, y):
        return self.game.__setitem__(player=self, x=x, y=y)