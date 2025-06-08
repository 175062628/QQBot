import os
import sys
from enum import Enum
import matplotlib.pyplot as plt
import numpy as np
import io

sys.path.append(os.path.dirname(__file__))

class Status(Enum):
    PENDING = 1
    PLAYING = 2
    ENDED = 3

class ChessCode:
    OUT_OF_RANGE = 1
    EXIST_CHESS = 2
    SUCCESS = 3
    WIN = 4

class Player:
    def __init__(self, qq_number, chess_id):
        self.id = qq_number
        self.chess_id = chess_id
        self.rival = None

    def set_game(self, other: 'Player'):
        self.rival = other
        other.rival = self

class Game:
    def __init__(self):
        self.current_player: Player
        self.player_2: Player
        self.player_1: Player
        self.winner: Player

        self.size = 15
        self.win_condition = 5
        self.winner = None
        self.current_player = None
        self.player_2 = None
        self.player_1 = None
        self.matrix = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.callback = self.check_winner
        self.status = Status.PENDING

    def start_game(self, player_1: Player, player_2: Player):
        self.player_1 = player_1
        self.player_2 = player_2
        self.current_player = player_1
        self.status = Status.PLAYING

    def chess_down(self, x, y):
        if x not in range(0, self.size+1) or y not in range(0, self.size+1):
            return ChessCode.OUT_OF_RANGE
        if self.matrix[x][y] != 0:
            return ChessCode.EXIST_CHESS
        if self.callback(self.current_player, x, y):
            self.status = Status.ENDED
            self.winner = self.current_player
            return ChessCode.WIN
        self.matrix[x][y] = self.current_player.chess_id
        self.current_player = self.current_player.rival
        return ChessCode.SUCCESS

    def check_winner(self, player, x, y):
        directions = [
            (1, 0),
            (0, 1),
            (1, 1),
            (1, -1)
        ]
        for dx, dy in directions:
            count = 1
            for i in range(1, 5):
                nx, ny = x + dx * i, y + dy * i
                if nx in range(0, self.size+1) and ny in range(0, self.size+1) and self.matrix[nx][ny] == player.chess_id:
                    count += 1
                else:
                    break
            for i in range(1, 5):
                nx, ny = x - dx * i, y - dy * i
                if nx in range(0, self.size+1) and ny in range(0, self.size+1) and self.matrix[nx][ny] == player.chess_id:
                    count += 1
                else:
                    break
            if count >= 5:
                return True
        return False

    def give_up(self):
        self.winner = self.current_player.rival

    def show_game(self):
        """展示当前五子棋棋盘并返回图片"""
        fig, ax = plt.subplots(figsize=(8, 8))

        board_size = self.size
        for i in range(board_size):
            ax.plot([0, board_size - 1], [i, i], 'k-')
            ax.plot([i, i], [0, board_size - 1], 'k-')

        ax.set_xlim(-0.5, board_size - 0.5)
        ax.set_ylim(-0.5, board_size - 0.5)
        ax.set_xticks(range(board_size))
        ax.set_yticks(range(board_size))

        for i in range(board_size):
            for j in range(board_size):
                if self.matrix[i][j] == self.player_1.chess_id:  # 玩家1的棋子（黑）
                    ax.plot(i, j, 'ko', markersize=12)
                elif self.matrix[i][j] == self.player_2.chess_id:  # 玩家2的棋子（白）
                    ax.plot(i, j, 'wo', markersize=12, markeredgecolor='k')

        if board_size == 15:
            star_points = [(3, 3), (3, 11), (7, 7), (11, 3), (11, 11)]
            for x, y in star_points:
                ax.plot(x, y, 'ko', markersize=4)

        ax.set_axis_off()

        try:
            image_path = "./plugins/Gobang/chess.jpg"
            plt.savefig(image_path, format='jpg', bbox_inches='tight')
        except Exception as e:
            img_bytes = io.BytesIO()
            plt.savefig(img_bytes, format='jpg', bbox_inches='tight')
            img_bytes.seek(0)
            plt.close(fig)
            return img_bytes
        finally:
            plt.close(fig)

        return image_path
