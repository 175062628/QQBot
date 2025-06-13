import sys
import os
from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core import GroupMessage
import time

sys.path.append(os.path.dirname(__file__))

bot = CompatibleEnrollment  # 兼容回调函数注册器

from utils import load_config_from_yaml
config = load_config_from_yaml("config.yaml")
bot_id = config.get("bot_id")
bot_name = config.get("bot_name")

from .model import PoemGenerator

class Poem(BasePlugin):
    name = "Poem" # 插件名称
    version = "0.0.1" # 插件版本
    author = "Ethan Ye"
    info = "藏头诗生成模型，使用方式：[@Bot ]藏头诗 藏头内容"
    description = "藏头诗生成模型，适用于私聊和群聊"

    poem_generator = PoemGenerator('./plugins/Poem/models')

    async def generate_poem(self, msg: GroupMessage):
        keywords = msg.raw_message.split(' ')[-1]
        success, poem = self.poem_generator.generate_acrostic(keywords)
        await msg.reply(text=poem)

    async def on_load(self):
        # 插件加载时执行的操作, 可缺省
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")
        self.register_user_func(
            "Poem",
            handler=self.generate_poem,
            regex=f"^(?:(?:\[CQ:at,qq={bot_id}\]|@{bot_name})\s+)?藏头诗\s+.+$",
        )