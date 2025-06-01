import os
import sys
import re
import json
from datetime import date, datetime
import requests

from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core import BotClient, GroupMessage

bot = CompatibleEnrollment  # 兼容回调函数注册器

class GoBang(BasePlugin):
    name = "GoBang" # 插件名称
    version = "0.0.1" # 插件版本

    async def on_load(self):
        # 插件加载时执行的操作, 可缺省
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")
