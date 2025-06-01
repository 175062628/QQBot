import os
import sys
import re
import json
from datetime import date, datetime
import requests

from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core import BotClient, GroupMessage

sys.path.append(os.path.dirname(__file__))


bot = CompatibleEnrollment  # 兼容回调函数注册器

class GoBang(BasePlugin):
    name = "GoBang" # 插件名称
    version = "0.0.1" # 插件版本

    async def new_game(self):
        pass
    async def on_load(self):
        # 插件加载时执行的操作, 可缺省
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")
        self.register_user_func(
            "StartGame",
            handler=self.daily_wife,
            regex="^(?:\[CQ:at,qq=3909177943\]|@Bot)\s+五子棋$|^五子棋$",
        )
