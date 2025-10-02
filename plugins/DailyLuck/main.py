import os
import sys
from datetime import date, datetime
import random
from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core import GroupMessage
import numpy as np
sys.path.append(os.path.dirname(__file__))
from mysql_assistant import MySQLAssistant

bot = CompatibleEnrollment  # 兼容回调函数注册器

from utils import load_config_from_yaml, send_request
config = load_config_from_yaml("my_config.yaml")
bot_id = config.get("bot_id")
bot_name = config.get("bot_name")

class DailyLuck(BasePlugin):
    name = "DailyLuck" # 插件名称
    version = "0.0.1" # 插件版本
    author = "Ethan Ye"
    info = "今日运势，使用方式：\n查看运势：[@Bot ]今日运势\n修改运势：[@Bot ]逆天改命"
    description = "今日运势，适用于私聊和群聊"

    mysql = MySQLAssistant(config_file="config.yaml")
    image_api = "https://acg.yaohud.cn/dm/acg.php?return=json"
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS DailyLuck (
        id INT AUTO_INCREMENT PRIMARY KEY,
        qq_number VARCHAR(32) NOT NULL,
        luck VARCHAR(32) NOT NULL,
        description VARCHAR(512),
        date DATE,
        changed VARCHAR(5),
        UNIQUE KEY unique_qq_date (qq_number, date)
    )
    """
    query_template = """
    SELECT * FROM DailyLuck 
    WHERE qq_number = %s 
    AND date = %s
    """
    update_template = """
    UPDATE DailyLuck SET luck = %s, description = %s, changed = %s
    WHERE qq_number = %s
    AND date = %s
    """
    query_luck_explain = """
    SELECT * FROM daily_luck_map
    WHERE luck = %s
    """

    async def daily_luck(self, msg: GroupMessage):
        self.mysql.connect()
        self.mysql.create_table_if_not_exists("DailyLuck", create_table_sql=self.create_table_sql)
        qq_number = msg.sender.user_id
        today = date.today()
        image_response = send_request('POST', self.image_api, "Daily_Luck_Image")
        image = None
        if isinstance(image_response, dict):
            image = image_response['acgurl']

        records = self.mysql.execute_query(self.query_template, (qq_number, today))
        if len(records) != 0:
            await msg.reply(
                text=f"{records[0]['luck']}\n{records[0]['description']}\n{image_response if image is None else ''}",
                image=image)
            return

        result = self.get_description(qq_number, today, "False")
        self.mysql.insert_data("DailyLuck", [result])
        self.mysql.disconnect()
        await msg.reply(text=f"{result['luck']}\n{result['description']}\n{image_response if image is None else ''}",
                        image=image)

    async def change_luck(self, msg: GroupMessage):
        self.mysql.connect()
        self.mysql.create_table_if_not_exists("DailyLuck", create_table_sql=self.create_table_sql)
        qq_number = msg.sender.user_id
        today = date.today()
        records = self.mysql.execute_query(self.query_template, (qq_number, today))
        if len(records) == 0:
            await msg.reply(text=f"今天你还没有测过运势哦")
            return
        if records[0]["changed"] == "True":
            await msg.reply(text=f"今天已经改过运了，贪心不足蛇吞象，小心神明大人降下惩罚")
            return

        image_response = send_request('POST', self.image_api, "Daily_Luck_Image")
        image = None
        if isinstance(image_response, dict):
            image = image_response['acgurl']

        result = self.get_description(qq_number, today, "True")
        self.mysql.update_data(self.update_template, (qq_number, today), [result])
        self.mysql.disconnect()
        await msg.reply(text=f"{result['luck']}\n{result['description']}\n{image_response if image is None else ''}",
                        image=image)

    def get_description(self, qq_number, today, changed):
        luck = 0
        while luck < 0.5 or luck >= 10.5:
            luck = np.random.normal(loc=5.5, scale=3)
        luck = int(round(luck))

        luck_list = self.mysql.execute_query(self.query_luck_explain, luck)
        result = random.choice(luck_list)
        return {
            "qq_number": qq_number,
            "date": today,
            "changed": changed,
            "description": "签文：" + result['sign'] + '\n'
                            "签解：" + result['explain'] + '\n'
                            "运势解析：" + result['description'],
            "luck": "★" * luck + "☆" * (10 - luck)
        }

    async def on_load(self):
        # 插件加载时执行的操作, 可缺省
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")
        self.register_user_func(
            "DailyLuck",
            handler=self.daily_luck,
            regex=f"^(?:(?:\[CQ:at,qq={bot_id}\]|@{bot_name})\s+)?今日运势$",
        )
        self.register_user_func(
            "ChangeLuck",
            handler=self.change_luck,
            regex=f"^(?:(?:\[CQ:at,qq={bot_id}\]|@{bot_name})\s+)?逆天改命$",
        )