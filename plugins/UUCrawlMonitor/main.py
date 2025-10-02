import datetime

from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core import GroupMessage, MessageArray
import sys
import os

sys.path.append(os.path.dirname(__file__))
from mysql_assistant import MySQLAssistant
from utils import load_config_from_yaml

bot = CompatibleEnrollment  # 兼容回调函数注册器
config = load_config_from_yaml("config.yaml")
bot_id = config.get("bot_id")
bot_name = config.get("bot_name")
interval = config.get("crawl_interval")
group_id_list = config.get("crawl_group_id_list")

class UUCrawlMonitor(BasePlugin):
    name = "UUCrawlMonitor"  # 插件名称
    version = "0.0.1"  # 插件版本
    author = "Ethan Ye"
    info = "悠悠爬虫监控，用于控制爬虫@对象信息"
    description = "悠悠爬虫监控，用于控制爬虫@对象信息"

    plugin_dir = "./plugins"
    mysql = MySQLAssistant(config_file="config.yaml")

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS UUCrawl (
        id INT AUTO_INCREMENT PRIMARY KEY,
        template_id VARCHAR(32) NOT NULL,
        name VARCHAR(32),
        min_price FLOAT(16,2),
        on_sale_count INT(8),
        on_lease_count INT(8),
        lease_unit_price FLOAT(16,2),
        long_lease_unit_price FLOAT(16,2),
        lease_deposit FLOAT(16,2),
        valid INT(2) NOT NULL,
        group_id VARCHAR(32) NOT NULL,
        date DATE,
        qq_numbers VARCHAR(128) NOT NULL,
        INDEX uukey (template_id)
    )
    """

    async def on_load(self):
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")
        self.register_user_func(
            "UUCrawlMonitorAdd",
            handler=self.add_monitor,
            regex=f"^(?:(?:\[CQ:at,qq={bot_id}\]|@{bot_name})\s+)?添加 \d+$"
        )

        self.register_user_func(
            "UUCrawlMonitorRemove",
            handler=self.remove_monitor,
            regex=f"^(?:(?:\[CQ:at,qq={bot_id}\]|@{bot_name})\s+)?移除 \d+$"
        )

    async def add_monitor(self, msg: GroupMessage):
        if msg.message_type != "group":
            return

        qq_number = msg.sender.user_id
        group_number = msg.group_id
        template_id = msg.raw_message.split(' ')[-1:]

        self.mysql.connect()
        self.mysql.create_table_if_not_exists("UUCrawl", create_table_sql=self.create_table_sql)

        res = self.mysql.execute_query("""
            SELECT qq_numbers FROM UUCrawl WHERE template_id = %s AND valid = %s AND group_id = %s limit 1
        """, (template_id, 1, group_number))
        if len(res) is 0:
            self.mysql.insert_data("UUCrawl", [
                {
                    'template_id': template_id,
                    'qq_numbers': qq_number,
                    'group_id': group_number,
                    'valid': 1
                }
            ])
        else:
            qq_numbers = ",".join(res[0]["qq_numbers"].split(',').append(qq_number))
            self.mysql.update_data("""
                UPDATE UUCrawl SET qq_numbers = %s WHERE template_id = %s AND valid = %s AND group_id = %s
            """, (template_id, 1, group_number), [{'qq_numbers': qq_numbers}])

    async def remove_monitor(self, msg: GroupMessage):
        if msg.message_type != "group":
            return

        qq_number = msg.sender.user_id
        group_number = msg.group_id
        template_id = msg.raw_message.split(' ')[-1:]

        self.mysql.connect()
        self.mysql.create_table_if_not_exists("UUCrawl", create_table_sql=self.create_table_sql)

        res = self.mysql.execute_query("""
            SELECT qq_numbers FROM UUCrawl WHERE template_id = %s AND valid = %s AND group_id = %s limit 1
        """, (template_id, 1, group_number))

        if len(res) == 1:
            qq_numbers = res[0]["qq_numbers"].split(',')
            while qq_number in qq_numbers:
                qq_numbers.remove(qq_number)
            if len(qq_numbers) == 0:
                self.mysql.update_data("""
                    UPDATE UUCrawl SET valid = %s WHERE template_id = %s AND valid = %s AND group_id = %s
                """, (template_id, 1, group_number), [{'valid': 0}])
            else:
                self.mysql.update_data("""
                    UPDATE UUCrawl SET qq_numbers = %s WHERE template_id = %s AND valid = %s AND group_id = %s
                """, (template_id, 1, group_number), [{'qq_numbers': ','.join(qq_numbers)}])
