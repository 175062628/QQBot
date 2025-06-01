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
from utils.explain import Explain

bot = CompatibleEnrollment  # 兼容回调函数注册器

class DailyLuck(BasePlugin):
    name = "DailyLuck" # 插件名称
    version = "0.0.1" # 插件版本
    mysql = MySQLAssistant(config_file="./plugins/DailyLuck/config.yaml")
    api_uri = "https://api.milimoe.com/userdaily/get/"
    image_api = "https://acg.yaohud.cn/dm/acg.php?return=url"
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS DailyLuck (
        id INT AUTO_INCREMENT PRIMARY KEY,
        qq_number VARCHAR(32) NOT NULL,
        luck VARCHAR(8) NOT NULL,
        description VARCHAR(255),
        date DATE,
        UNIQUE KEY unique_qq_date (qq_number, date)
    )
    """
    query_template = """
    SELECT * FROM DailyLuck 
    WHERE qq_number = %s 
    AND date = %s
    """

    async def daily_luck(self, msg: GroupMessage):
        self.mysql.create_table_if_not_exists("DailyLuck", create_table_sql=self.create_table_sql)
        qq_number = msg.sender.user_id
        today = date.today()
        image = requests.post(self.image_api).text
        records = self.mysql.execute_query(self.query_template, (qq_number, today))
        if len(records) != 0:
            await msg.reply(text=f"{records[0]['description']}", image=image)
            return

        result = Explain(requests.post(f"{self.api_uri}{qq_number}").json()).get_res()
        result["qq_number"] = qq_number
        result["date"] = today

        self.mysql.insert_data("DailyLuck", result)
        await msg.reply(text=f"{result['description']}", image=image)

    async def on_load(self):
        # 插件加载时执行的操作, 可缺省
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")
        self.register_admin_func(
            "DailyLuck",
            handler=self.daily_luck,
            regex="^(?:\[CQ:at,qq=3909177943\]|@Bot)\s+今日运势$|^今日运势$",
            permission_raise=True
        )