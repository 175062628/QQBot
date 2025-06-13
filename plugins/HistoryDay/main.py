import os
import sys
from datetime import date
import re
from datetime import datetime

from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core import GroupMessage

sys.path.append(os.path.dirname(__file__))
from mysql_assistant import MySQLAssistant

bot = CompatibleEnrollment  # 兼容回调函数注册器

from utils import load_config_from_yaml
config = load_config_from_yaml("config.yaml")
bot_id = config.get("bot_id")
bot_name = config.get("bot_name")

class HistoryDay(BasePlugin):
    name = "HistoryDay" # 插件名称
    version = "0.0.1" # 插件版本
    author = "Ethan Ye"
    info = ("""那年今日，使用方式：
查看历史上的今天：[@Bot ]那年今日[ 起始年份][ 结束年份]
改写今天的历史：[@Bot ]载入历史 (大事记|出生|逝世|节假日) 事件""")
    description = "那年今日，适用于私聊和群聊"
    mysql = MySQLAssistant(config_file="config.yaml")
    query_template = """
    SELECT year, month, day, affair, type FROM history_affair
    WHERE (
        year >= %s AND year <= %s
        OR type = 'festival'
    ) 
    AND month = %s
    AND day = %s 
    order by year
    LIMIT 20
    """
    keyword_map = {
        'affair': "大事记",
        'birth': "出生",
        'death': "逝世",
        'festival': "节假日"
    }
    insert_map = {
        "大事记": 'affair',
        "出生": 'birth',
        "逝世": 'death',
        "节假日": 'festival'
    }

    async def get_today_on_history(self, msg: GroupMessage):
        pattern = f"^(?:(?:\[CQ:at,qq={bot_id}\]|@{bot_name})\s+)?那年今日(?:\s+(-?\d+)(?:\s+(-?\d+))?)?$"
        match = re.match(pattern, msg.raw_message)
        now = datetime.now()
        last_year = now.year
        month = now.month
        day = now.day
        start_year = 0
        end_year = 0
        affair_map = {
            'affair': [],
            'birth': [],
            'death': [],
            'festival': []
        }
        text = "那年今日，发生了以下大事"
        if match:
            year1 = match.group(1)
            year2 = match.group(2)
            if year1 is None:
                start_year = last_year-5
                end_year = last_year
            elif year2 is None:
                start_year = int(year1)
                end_year = last_year
            else:
                start_year = int(year1)
                end_year = int(year2)

        records = self.mysql.execute_query(self.query_template, (start_year, end_year, month, day))
        for record in records:
            affair_map[record['type']].append(f"{str(record['year'])+'：' if record['year'] != 0 else ''}{record['affair']}")
        for k, v in affair_map.items():
            if len(v):
                text += f"\n{self.keyword_map[k]}"
            for affair in v:
                text += f"\n{affair}"

        await msg.reply(text=text)

    async def insert_history(self, msg: GroupMessage):
        args = msg.raw_message.split(' ', 2)
        story = args[-1]
        if args[-2] not in self.insert_map:
            return
        affair_type = self.insert_map[args[-2]]
        now = datetime.now()
        data = {
            'year': now.year,
            'month': now.month,
            'day': now.day,
            'affair': story,
            'type': affair_type
        }
        self.mysql.insert_data('history_affair', [data])
        print('success')

    async def on_load(self):
        # 插件加载时执行的操作, 可缺省
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")
        self.register_user_func(
            "HistoryDay",
            handler=self.get_today_on_history,
            regex=f"^(?:(?:\[CQ:at,qq={bot_id}\]|@{bot_name})\s+)?那年今日(?:\s+(-?\d+)(?:\s+(-?\d+))?)?$",
        )
        self.register_user_func(
            "InsertHistory",
            handler=self.insert_history,
            regex=f"^(?:(?:\[CQ:at,qq={bot_id}\]|@{bot_name})\s+)?载入历史\s+(?:大事记|出生|逝世|节假日)\s+.+$",
        )
