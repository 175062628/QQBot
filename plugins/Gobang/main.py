import os
import sys

from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core import BotClient, GroupMessage

sys.path.append(os.path.dirname(__file__))

from utils.game import Game, Player, ChessCode, Status

bot = CompatibleEnrollment  # 兼容回调函数注册器

class GoBang(BasePlugin):
    name = "GoBang" # 插件名称
    version = "0.0.1" # 插件版本
    game = None
    player = None
    rival = None
    async def new_game(self, msg: GroupMessage):
        if self.player:
            await msg.reply(at=self.player.id, text=f"已经在等待对手，输入：对弈 跟他下棋吧")
            return
        self.player = Player(msg.sender.user_id, 1)
        self.game = Game()
        await msg.reply(text=f"等待对手中.......")

    async def play_game(self, msg: GroupMessage):
        if self.game.status != Status.PENDING:
            await msg.reply(text=f"游戏已经开始")
            return
        if self.player is None:
            await msg.reply(text=f"游戏还没启动，输入：五子棋 启动游戏")
            return
        if self.rival:
            await msg.reply(at=[self.player.id, self.rival.id] ,text=f"在下棋，等一等吧")
            return
        self.rival = Player(msg.sender.user_id, 2)
        await msg.reply(at=self.player.id, text=f"双方就绪，输入：启动 开始对弈")

    async def quit_game(self, msg: GroupMessage):
        if self.game.status == Status.PLAYING:
            await msg.reply(text=f"游戏已经开始，请先 投降")
            return
        if self.player and self.player.id == msg.sender.user_id:
            self.player = self.rival
            self.rival = None
            self.player.chess_id = 1
            await msg.reply(at=self.player.id, text=f"对手落荒而逃，等待对手中.......")
            return
        if self.rival and self.rival.id == msg.sender.user_id:
            self.rival = None
            await msg.reply(at=self.player.id, text=f"对手落荒而逃，等待对手中.......")

    async def start_game(self, msg: GroupMessage):
        if self.game.status != Status.PENDING:
            await msg.reply(text=f"游戏已经开始")
            return
        if self.player is None:
            await msg.reply(text=f"房主呢？房主来一个")
        if msg.sender.user_id != self.player.id:
            await msg.reply(text=f"你无法启动对弈")
        if self.rival is None:
            await msg.reply(text=f"暂时无人敢来对弈")
        self.game.start_game(self.player, self.rival)
        self.player.set_game(self.rival)
        await msg.reply(text=f"[CQ:at,qq={self.player.id}][CQ:at,qq={self.rival.id}] 对弈开始，输入：1 2 落子，现在由[CQ:at,qq={self.player.id}]执手")

    async def chess_down(self, msg: GroupMessage):
        if self.game.status != Status.PLAYING:
            await msg.reply(text=f"游戏还没开始")
            return
        if self.game.current_player.id != msg.sender.user_id:
            await msg.reply(text=f"对手还在思考，不要着急")
            return
        x, y = msg.raw_message.split(' ')[-2:]
        res = self.game.chess_down(int(x), int(y))
        match res:
            case ChessCode.OUT_OF_RANGE:
                await msg.reply(text=f"落子超出棋盘了")
            case ChessCode.EXIST_CHESS:
                await msg.reply(text=f"这里已经下过了")
            case ChessCode.WIN:
                await msg.reply(text=f"[CQ:at,qq={self.player.id}][CQ:at,qq={self.rival.id}] 激情对弈后，[CQ:at,qq={self.game.winner.id}]棋高一招")
            case ChessCode.SUCCESS:
                image = self.game.show_game()
                await msg.reply(at=self.game.current_player.id, text=f"到你了", image=image)

    async def give_up(self, msg: GroupMessage):
        if self.game.status != Status.PLAYING:
            await msg.reply(text=f"游戏还没开始")
            return
        if self.game.current_player.id != msg.sender.user_id:
            await msg.reply(text=f"不要帮对手点投降")
            return
        self.game.give_up()
        await msg.reply(text=f"[CQ:at,qq={self.player.id}][CQ:at,qq={self.rival.id}] 激情对弈后，[CQ:at,qq={self.game.winner.id}]棋高一招")

    async def on_load(self):
        # 插件加载时执行的操作, 可缺省
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")
        self.register_user_func(
            "NewGame",
            handler=self.new_game,
            regex="^(?:\[CQ:at,qq=3909177943\]|@Bot)\s+五子棋$|^五子棋$",
        )
        self.register_user_func(
            "PlayGame",
            handler=self.play_game,
            regex="^(?:\[CQ:at,qq=3909177943\]|@Bot)\s+对弈$|^对弈$",
        )
        self.register_user_func(
            "StartGame",
            handler=self.start_game,
            regex="^(?:\[CQ:at,qq=3909177943\]|@Bot)\s+启动$|^启动$",
        )
        self.register_user_func(
            "ChessDown",
            handler=self.chess_down,
            regex="(?:\[CQ:at,qq=3909177943\]|@Bot)\s+\d+\s+\d+$|^\d+\s+\d+",
        )
        self.register_user_func(
            "GiveUp",
            handler=self.give_up,
            regex="^(?:\[CQ:at,qq=3909177943\]|@Bot)\s+投降$|^投降$",
        )
        self.register_user_func(
            "QuitGame",
            handler=self.quit_game,
            regex="^(?:\[CQ:at,qq=3909177943\]|@Bot)\s+退出$|^退出$",
        )
