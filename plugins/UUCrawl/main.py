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
api = BotClient().run_backend(bt_uin=bot_id)


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
        name VARCHAR(32)
        min_price FLOAT(2),
        on_sale_count INT(8),
        on_lease_count INT(8),
        lease_unit_price FLOAT(2),
        long_lease_unit_price FLOAT(2),
        lease_deposit FLOAT(2),
        valid INT(2) NOT NULL,
        group_id VARCHAR(32) NOT NULL,
        date DATE,
        qq_numbers VARCHAR(128) NOT NULL,
        UNIQUE KEY template_id
    )
    """

    async def on_load(self):
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")
        self.register_user_func(
            "UUCrawl",
            handler=self.add_monitor,
            regex=f"^(?:(?:\[CQ:at,qq={bot_id}\]|@{bot_name})\s+)?添加 \d+$",
        )

        self.register_user_func(
            "UUCrawl",
            handler=self.remove_monitor,
            regex=f"^(?:(?:\[CQ:at,qq={bot_id}\]|@{bot_name})\s+)?移除 \d+$",
        )

        self.add_scheduled_task(
            self.crawl,
            "conditional",
            "1h",
            conditions=[self.is_active]
        )

    async def crawl(self):
        self.mysql.connect()
        self.mysql.create_table_if_not_exists("UUCrawl", create_table_sql=self.create_table_sql)

        goods_list = self.mysql.execute_query(f"""
            SELECT DISTINCT template_id FROM UUCrawl WHERE valid = %d
        """, 1)

        group_id_goods = {}
        goods_owner = {}
        for item in goods_list:
            if item['group_id'] in group_id_goods:
                group_id_goods[item['group_id']].append(item['template_id'])
            else:
                group_id_goods[item['group_id']] = [item['template_id']]
            if item['template_id'] not in goods_owner:
                goods_owner[item['template_id']] = item['qq_numbers']

        insert2mysql = []
        for group_id, goods_list in group_id_goods:
            res = crawl_goods(goods_list, interval)

            for item in res:
                item_owners = goods_owner[item.template_id]

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
                    'group_id': group_id,
                    'date': item.time,
                    'qq_numbers': item_owners
                })
                msg = MessageArray()
                for qq_number in item_owners.split(','):
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
                    押金：{item.lease_deposit}
                """).add_at(goods_owner[item.template_id])
                await api.post_group_array_msg(group_id, msg)

        self.mysql.insert_data("UUCrawl", insert2mysql)

    async def add_monitor(self, msg: GroupMessage):
        if msg.message_type != "group":
            return

        qq_number = msg.sender.user_id
        group_number = msg.group_id
        template_id = msg.raw_message.split(' ')[-1:]

        self.mysql.connect()
        self.mysql.create_table_if_not_exists("UUCrawl", create_table_sql=self.create_table_sql)

        res = self.mysql.execute_query("""
            SELECT qq_numbers FROM UUCrawl WHERE template_id = %d AND valid = %d AND group_id = %s limit 1
        """, (template_id, 1, group_number))
        if res is []:
            self.mysql.insert_data("UUCrawl", [
                {
                    'template_id': template_id,
                    'qq_numbers': qq_number,
                    'group_id': group_number,
                    'valid': 1
                }
            ])
        else:
            qq_numbers = ",".join(res["qq_numbers"].split(',').append(qq_number))
            self.mysql.update_data("""
                SELECT qq_numbers FROM UUCrawl WHERE template_id = %d AND valid = %d AND group_id = %s
            """, (template_id, 1, group_number), [qq_numbers])

    async def remove_monitor(self, msg: GroupMessage):
        if msg.message_type != "group":
            return

        qq_number = msg.sender.user_id
        group_number = msg.group_id
        template_id = msg.raw_message.split(' ')[-1:]

        self.mysql.connect()
        self.mysql.create_table_if_not_exists("UUCrawl", create_table_sql=self.create_table_sql)

        res = self.mysql.execute_query("""
            SELECT qq_numbers FROM UUCrawl WHERE template_id = %d AND valid = %d AND group_id = %s limit 1
        """, (template_id, 1, group_number))
        if res is not []:
            qq_numbers = res["qq_numbers"].split(',')
            while qq_number in qq_numbers:
                qq_numbers.remove(qq_number)
            if qq_numbers is []:
                self.mysql.update_data("""
                    SELECT valid FROM UUCrawl WHERE template_id = %d AND valid = %d AND group_id = %s
                """, (template_id, 1, group_number), [0])
            else:
                self.mysql.update_data("""
                    SELECT qq_numbers FROM UUCrawl WHERE template_id = %d AND valid = %d AND group_id = %s
                """, (template_id, 1, group_number), [','.join(qq_numbers)])

    def is_active(self):
        return 0 <= datetime.datetime.now().hour <= 2 or 8 <= datetime.datetime.now().hour <= 24
