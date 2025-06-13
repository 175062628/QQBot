import os
import sys
import re
from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core import GroupMessage
from .utils import get_plugin_info

sys.path.append(os.path.dirname(__file__))

bot = CompatibleEnrollment  # 兼容回调函数注册器

from utils import load_config_from_yaml
config = load_config_from_yaml("config.yaml")
bot_id = config.get("bot_id")
bot_name = config.get("bot_name")

class Menu(BasePlugin):
    name = "Menu" # 插件名称
    version = "0.0.1" # 插件版本
    author = "Ethan Ye"
    info = "菜单，获取所有插件信息，使用方式：[@Bot ]菜单"
    description = "菜单，适用于私聊和群聊"

    plugin_dir = "./plugins"

    async def menu(self, msg: GroupMessage):
        subfolders = []
        with os.scandir(self.plugin_dir) as entries:
            for entry in entries:
                if entry.is_dir():
                    subfolders.append(entry.name)

        allowed_pattern = re.compile(r'^[a-zA-Z0-9\u4e00-\u9fa5]')
        plugins = [
            folder
            for folder in subfolders
            if folder != "Menu" and allowed_pattern.match(folder)
        ]

        text = f"以下是本Bot支持的所有功能："
        for index, plugin in enumerate(plugins):
            plugin_name, plugin_version, plugin_meta = get_plugin_info(f"{self.plugin_dir}/{plugin}")
            text += f'\n{index+1}. {plugin_meta["info"] if plugin_meta["info"] is not None else "未知插件"}'

        await msg.reply(text=text)

    async def on_load(self):
        # 插件加载时执行的操作, 可缺省
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")
        self.register_user_func(
            name="Menu",
            description=self.description,
            usage=self.info,
            metadata={
                "description": self.description,
                "info": self.info,
            },
            handler = self.menu,
            regex = f"^(?:(?:\[CQ:at,qq={bot_id}\]|@{bot_name})\s+)?\s+菜单$",
        )
