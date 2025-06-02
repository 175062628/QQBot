import os
import sys
import re
import json
from datetime import date, datetime
import requests

from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core import GroupMessage

sys.path.append(os.path.dirname(__file__))
from .utils.mysql_assistant import MySQLAssistant
from .utils.pick_wife import PickWife

bot = CompatibleEnrollment  # 兼容回调函数注册器

bot_qq = "3909177943"
class DailyWife(BasePlugin):
    name = "DailyWife" # 插件名称
    version = "0.0.1" # 插件版本
    mysql = MySQLAssistant(config_file="./plugins/DailyWife/config.yaml")
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS DailyWife (
        id INT AUTO_INCREMENT PRIMARY KEY,
        qq_number VARCHAR(32) NOT NULL,
        wife_number VARCHAR(32) NOT NULL,
        group_number VARCHAR(32) NOT NULL,
        date DATE,
        UNIQUE KEY unique_qq_date (qq_number, wife_number, group_number)
    )
    """
    query_template = """
        SELECT wife_number FROM DailyWife 
        WHERE qq_number = %s 
        AND date = %s
        AND group_number = %s
        """

    async def daily_wife(self, msg: GroupMessage):
        print(msg)
        if msg.message_type != "group":
            return
        self.mysql.create_table_if_not_exists("DailyWife", create_table_sql=self.create_table_sql)
        qq_number = msg.sender.user_id
        today = date.today()
        group_number = msg.group_id
        records = self.mysql.execute_query(self.query_template, (qq_number, today, group_number))
        if len(records) != 0:
            response = await self.api.get_group_member_info(group_id=msg.group_id, user_id=records[0]["wife_number"], no_cache=False)
            wife = response["data"]
            await msg.reply(text=self.show_wife(wife), at=wife['user_id'])
            return
        married_list = self.mysql.execute_query("""
            SELECT qq_number FROM DailyWife WHERE date = %s AND group_number = %s
        """, (today, group_number))
        response = await self.api.get_group_member_list(group_number)
        member_list = response["data"]
        wife = PickWife(member_list, married_list, [bot_qq, msg.sender.user_id]).pick_wife()
        self.mysql.insert_data("DailyWife", [
            {
                "qq_number": msg.sender.user_id,
                "wife_number": wife["user_id"],
                "date": today,
                "group_number": group_number
            },
            {
                "qq_number": wife["user_id"],
                "wife_number": msg.sender.user_id,
                "date": today,
                "group_number": group_number
            },
        ])
        await msg.reply(text=self.show_wife(wife), at=wife['user_id'])

    @staticmethod
    def show_wife(wife):
        name = wife["nickname"] if not wife["card"] else wife["card"]
        text = f"今天的老婆是：{name} "
        return text

    async def on_load(self):
        # 插件加载时执行的操作, 可缺省
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")
        self.register_user_func(
            "DailyWife",
            handler=self.daily_wife,
            regex="^(?:\[CQ:at,qq=3909177943\]|@Bot)\s+今日老婆$|^今日老婆$",
        )
