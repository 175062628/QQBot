import os
import sys
import re
import json
from datetime import date, datetime
import requests

from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core import GroupMessage, PrivateMessage

sys.path.append(os.path.dirname(__file__))
from utils.mysql_assistant import MySQLAssistant

bot = CompatibleEnrollment  # 兼容回调函数注册器

class DailyWife(BasePlugin):
    name = "DailyWife" # 插件名称
    version = "0.0.1" # 插件版本
    mysql = MySQLAssistant(config_file="./plugins/DailyLuck/config.yaml")
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS DailyWife (
        id INT AUTO_INCREMENT PRIMARY KEY,
        qq_number VARCHAR(32) NOT NULL,
        wife_number VARCHAR(32) NOT NULL,
        date DATE,
        UNIQUE KEY unique_qq_date (qq_number, wife_number)
    )
    """
    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        pattern = r"(?:\[CQ:at,qq=1706773717\]|@Bot)\s+今日老婆"
        if not re.match(pattern, msg.raw_message):
            return
        self.mysql.create_table_if_not_exists("DailyWife", create_table_sql=self.create_table_sql)

        await msg.reply(text=f"{result['description']}", image=image)

    async def on_load(self):
        # 插件加载时执行的操作, 可缺省
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")