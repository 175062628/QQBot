import os
import sys
import requests
import random

from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core import GroupMessage, Music, MessageChain, Text, Image

sys.path.append(os.path.dirname(__file__))
from mysql_assistant import MySQLAssistant

bot = CompatibleEnrollment  # 兼容回调函数注册器

from utils import load_config_from_yaml
config = load_config_from_yaml("config.yaml")
bot_id = config.get("bot_id")
bot_name = config.get("bot_name")

class DailyMusic(BasePlugin):
    name = "DailyMusic" # 插件名称
    version = "0.0.1" # 插件版本
    author = "Ethan Ye"
    info = "今日歌曲，使用方式：[@Bot ]今日(热歌|新歌|原创|飙升)榜"
    description = "今日歌曲，适用于私聊和群聊"

    api_url = "https://api.vvhan.com/api/wyMusic/"
    mysql = MySQLAssistant(config_file="config.yaml")
    create_table_sql = """
        CREATE TABLE IF NOT EXISTS DailyMusic (
            id INT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            author VARCHAR(255) NOT NULL,
            type VARCHAR(8),
            image VARCHAR(255),
            music VARCHAR(255)
        )
        """
    query_template = """
        SELECT * FROM DailyMusic
        AND type = %s
        """

    def music(self, word):
        try:
            response = requests.get(f"{self.api_url}{word[-3:]}?type=json").json()["info"]
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            return {
                "status": "fail"
            }

        result = {
            "id": response["id"],
            "name": response["name"],
            "author": response["auther"],
            "image": response["pic_url"],
            "music": response["url"],
            "type": word,
            "status": "success"
        }
        return result

    async def get_top_music(self, msg: GroupMessage):
        self.mysql.create_table_if_not_exists("DailyMusic", create_table_sql=self.create_table_sql)
        word = msg.raw_message.split(' ')[-1]
        music = self.music(word)
        if music["status"] == "fail":
            records = self.mysql.execute_query(self.query_template, word)
            if len(records) == 0:
                await msg.reply(text="接口出错，请稍后重试")
                return
            music = random.choice(records)
            message = MessageChain([
                Text(f"{word}\n歌名：{music['name']}\n歌手：{music['author']}"),
                Image(music['image']),
                Music("163", music['id'])
            ])
            await msg.reply(rtf=message)
            return

        message = MessageChain([
            Text(f"{word}\n歌名：{music['name']}\n歌手：{music['author']}"),
            Image(music['image']),
            Music("163", music['id'])
        ])

        self.mysql.insert_data("DailyMusic", [music])
        await msg.reply(rtf=message)

    async def on_load(self):
        # 插件加载时执行的操作, 可缺省
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")
        self.register_user_func(
            "DailyMusic",
            handler=self.get_top_music,
            regex=f"^(?:(?:\[CQ:at,qq={bot_id}\]|@{bot_name})\s+)?(今日(?:热歌|新歌|原创|飙升)榜)$"
        )
