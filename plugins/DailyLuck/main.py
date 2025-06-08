import os
import sys
from datetime import date
import requests

from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core import GroupMessage

sys.path.append(os.path.dirname(__file__))
from mysql_assistant import MySQLAssistant
from .explain import Explain

bot = CompatibleEnrollment  # 兼容回调函数注册器

from utils import load_config_from_yaml
config = load_config_from_yaml("config.yaml")
bot_id = config.get("bot_id")
bot_name = config.get("bot_name")

class DailyLuck(BasePlugin):
    name = "DailyLuck" # 插件名称
    version = "0.0.1" # 插件版本
    mysql = MySQLAssistant(config_file="config.yaml")
    api_uri = "https://api.milimoe.com/userdaily/get/"
    image_api = "https://acg.yaohud.cn/dm/acg.php?return=url"
    change_luck_api = "https://api.milimoe.com/userdaily/remove/"
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS DailyLuck (
        id INT AUTO_INCREMENT PRIMARY KEY,
        qq_number VARCHAR(32) NOT NULL,
        luck VARCHAR(8) NOT NULL,
        description VARCHAR(255),
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
        result["changed"] = "False"

        self.mysql.insert_data("DailyLuck", [result])
        await msg.reply(text=f"{result['description']}", image=image)

    async def change_luck(self, msg: GroupMessage):
        self.mysql.create_table_if_not_exists("DailyLuck", create_table_sql=self.create_table_sql)
        qq_number = msg.sender.user_id
        today = date.today()
        records = self.mysql.execute_query(self.query_template, (qq_number, today))
        if len(records) == 0:
            await msg.reply(text=f"今天你还没有测过运势哦")
            return
        if records[0]["changed"] == "True":
            await msg.reply(text=f"今天已经改过运了，人心不足蛇吞象，小心神明大人降下惩罚")
            return
        requests.post(f"{self.change_luck_api}{qq_number}")
        image = requests.post(self.image_api).text
        result = Explain(requests.post(f"{self.api_uri}{qq_number}").json()).get_res()
        result["changed"] = "True"

        self.mysql.update_data(self.update_template, (qq_number, today), [result])
        await msg.reply(text=f"{result['description']}", image=image)

    async def on_load(self):
        # 插件加载时执行的操作, 可缺省
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")
        self.register_user_func(
            "DailyLuck",
            handler=self.daily_luck,
            regex=f"^(?:\[CQ:at,qq={bot_id}\]|@{bot_name})\s+今日运势$|^今日运势$",
        )
        self.register_user_func(
            "ChangeLuck",
            handler=self.change_luck,
            regex=f"^(?:\[CQ:at,qq=={bot_id}\]|@{bot_name})\s+逆天改命$|^逆天改命$",
        )