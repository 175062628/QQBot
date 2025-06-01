import os
import sys
sys.path.append(os.path.dirname(__file__))

from player import Player

class Game:
    def __init__(self, player_1: Player, player_2: Player):
        self.size = 15
        self.player_1 = player_1
        self.player_2 = player_2
        self.current_player = player_1
        self.matrix = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.callback = self.check_winner

    def chess_down(self, player, x, y):
        if x not in range(0, self.size+1) or self.matrix[x][y] != "0":
            return False
        if self.callback(player, x, y):
            return player
        self.current_player = player.rival
        self.matrix[x][y] = player.chess_id
        return None

    def check_winner(self, player, x, y):
        pass
