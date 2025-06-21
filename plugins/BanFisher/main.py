import os
import sys
from datetime import date

from ncatbot.core import GroupMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment

sys.path.append(os.path.dirname(__file__))

bot = CompatibleEnrollment  # 兼容回调函数注册器

from utils import load_config_from_yaml
config = load_config_from_yaml("config.yaml")
bot_id = config.get("bot_id")
bot_name = config.get("bot_name")

class BanFisher(BasePlugin):
    name = "BanFisher" # 插件名称
    version = "0.0.1" # 插件版本
    author = "Ethan Ye"
    info = "自动功能，屏蔽“唤醒美人鱼”"
    description = "自动功能，屏蔽“唤醒美人鱼”"
    async def ban_fisher(self, msg: GroupMessage):
        await self.api.set_group_ban(group_id=msg.group_id, user_id=msg.sender.user_id, duration=120)

    async def on_load(self):
        # 插件加载时执行的操作, 可缺省
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")
        self.register_user_func(
            "DailyLuck",
            handler=self.ban_fisher,
            regex=f"^.*唤醒美人鱼.*$",
        )