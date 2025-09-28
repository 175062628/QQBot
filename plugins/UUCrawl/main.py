import datetime
from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core import GroupMessage
from ncatbot.plugin_system import NcatBotPlugin
import sys
import os
from .utils import *

sys.path.append(os.path.dirname(__file__))
from mysql_assistant import MySQLAssistant

bot = CompatibleEnrollment  # 兼容回调函数注册器

from utils import load_config_from_yaml

config = load_config_from_yaml("config.yaml")
bot_id = config.get("bot_id")
bot_name = config.get("bot_name")
interval = config.get("crawl_interval")

class UUCrawl(NcatBotPlugin):
    name = "UUCrawl"  # 插件名称
    version = "0.0.1"  # 插件版本
    author = "Ethan Ye"
    info = "悠悠爬虫，每小时爬取市场行情"
    description = "悠悠爬虫，每小时爬取市场行情"

    plugin_dir = "./plugins"
    mysql = MySQLAssistant(config_file="config.yaml")

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS UUCrawl (
        id INT AUTO_INCREMENT PRIMARY KEY,
        template_id VARCHAR(32) NOT NULL,
        name VARCHAR(32) NOT NULL,
        min_price FLOAT(2) NOT NULL,
        on_sale_count INT(8) NOT NULL,
        on_lease_count INT(8) NOT NULL,
        lease_unit_price FLOAT(2) NOT NULL,
        long_lease_unit_price FLOAT(2) NOT NULL,
        lease_deposit FLOAT(2) NOT NULL,
        date DATE,
        UNIQUE KEY template_id
    )
    """

    query_table_sql = """
    SELECT
        DISTINCT template_id
    FROM
        UUCrawl
    """

    async def on_load(self):
        self.add_scheduled_task(
            self.crawl,
            "conditional",
            "1h",
            conditions=[self.is_active]
        )

    async def crawl(self):
        self.mysql.connect()
        self.mysql.create_table_if_not_exists("UUCrawl", create_table_sql=self.create_table_sql)

        goods_list = self.mysql.execute_query(self.query_table_sql)
        res = crawl_goods(goods_list, interval)


    def is_active(self):
        return 0 <= datetime.datetime.now().hour <= 2 or 8 <= datetime.datetime.now().hour <= 24
