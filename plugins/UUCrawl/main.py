import datetime

from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core import GroupMessage, MessageArray, BotClient
from ncatbot.plugin_system import NcatBotPlugin
import sys
import os
from .utils import *

sys.path.append(os.path.dirname(__file__))
from mysql_assistant import MySQLAssistant
from utils import load_config_from_yaml

bot = CompatibleEnrollment  # 兼容回调函数注册器
config = load_config_from_yaml("config.yaml")
bot_id = config.get("bot_id")
bot_name = config.get("bot_name")
interval = config.get("crawl_interval")
group_id_list = config.get("crawl_group_id_list")

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
        UNIQUE KEY (id),
        INDEX uukey (template_id)
    )
    """

    async def on_load(self):
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")

        self.add_scheduled_task(
            self.crawl,
            "conditional",
            "1h",
            conditions=[self.is_active]
        )

    async def crawl(self):
        self.mysql.connect()
        self.mysql.create_table_if_not_exists("UUCrawl", create_table_sql=self.create_table_sql)

        records = self.mysql.execute_query(f"""
            SELECT DISTINCT template_id, group_id, qq_numbers FROM UUCrawl WHERE valid = %s
        """, 1)

        goods_list = []
        goods_owner = {}
        for item in records:
            if item['template_id'] not in goods_list:
                goods_list.append(item['template_id'])
            if item['template_id'] not in goods_owner:
                goods_owner[(item['template_id'], item['group_id'])] = item['qq_numbers']

        insert2mysql = []
        res = crawl_goods(goods_list, interval)

        for item in res:
            group_list = []
            print(group_list)
            for record in records:
                if record['group_id'] in group_list:
                    continue
                if (item.template_id, record['group_id']) in goods_owner:
                    group_list.append(record['group_id'])
                    insert2mysql.append({
                        'template_id': item.template_id,
                        'name': item.name,
                        'min_price': item.min_price,
                        'on_sale_count': item.on_sale_count,
                        'on_lease_count': item.on_lease_count,
                        'lease_unit_price': item.lease_unit_price,
                        'long_lease_unit_price': item.long_lease_unit_price,
                        'lease_deposit': item.lease_deposit,
                        'valid': 1,
                        'group_id': record['group_id'],
                        'date': item.time,
                        'qq_numbers': goods_owner[(item.template_id, record['group_id'])]
                    })
                    msg = MessageArray()

                    for qq_number in goods_owner[(item.template_id, record['group_id'])].split(','):
                        msg.add_at(qq_number)

                    msg.add_text(f"""
爬取时间：{item.time}
物品：{item.name}
悠悠id：{item.template_id}
在售底价：{item.min_price}
在售数：{item.on_sale_count}
在租数：{item.on_lease_count}
短租价/天：{item.lease_unit_price}
长租价/天：{item.long_lease_unit_price}
押金：{item.lease_deposit}""")
                    await self.api.post_group_array_msg(record['group_id'], msg)

        self.mysql.insert_data("UUCrawl", insert2mysql)

    def is_active(self):
        return 0 <= datetime.datetime.now().hour <= 2 or 8 <= datetime.datetime.now().hour <= 24
