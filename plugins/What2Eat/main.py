import os
import random
import sys
from datetime import date
import requests
import re

from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core import GroupMessage
from ncatbot.core.event.message_segment import MessageArray, Text, At, Image

sys.path.append(os.path.dirname(__file__))

bot = CompatibleEnrollment  # 兼容回调函数注册器

from utils import load_config_from_yaml
config = load_config_from_yaml("config.yaml")
bot_id = config.get("bot_id")
bot_name = config.get("bot_name")

class What2Eat(BasePlugin):
    name = "What2Eat" # 插件名称
    version = "0.0.1" # 插件版本
    author = "Ethan Ye"
    info = "今天吃什么，使用方式：[@Bot ]今天吃什么[ 位置][ (中餐|西餐|快餐|下午茶)][ 城市(默认上海)]"
    description = "今天吃什么，适用于私聊和群聊"

    api_uri = "https://restapi.amap.com/v5/place/text"
    api_key = config.get("gaode_map_key")
    page_size = 25
    service_type = '050000'
    restaurant_map = {
        '中餐': '050100|050101|050102|050103|050104|050105|050106|050107|050108|050109|050110|050111|050112|050113|050114|050115|050116|050117|050118|050119|050120|050121|050122|050123',
        '西餐': '050200|050201|050202|050203|050204|050205|050206|050207|050208|050209|050210|050211|050212|050213|050214|050215|050216|050217',
        '快餐': '050300|050301|050302|050303|050304|050305|050306|050307|050308|050309|050310|050311',
        '下午茶': '050500|050501|050502|050503|050504|050600|050700|050800|050900',
    }
    random_size = 3
    praser_map = {
        'address': '地址：',
        'name': '店铺名：',
        'rate': '评分：',
        'open_time': '营业时间：',
        'tag': '特色：',
        'cost': '人均消费：',
        'images': ''
    }

    async def what2eat(self, msg: GroupMessage):
        pattern = re.compile(
            fr'^(?:(?:\[CQ:at,qq={bot_id}\]|@{bot_name})\s+)?今天吃什么\s+([^ \n]+)(?:\s+([^ \n]+))?(?:\s+([^ \n]+))?$'
        )
        match = pattern.match(msg.raw_message)
        if match:
            location = match.group(1)
            cuisine = match.group(2)
            city = match.group(3)
        else:
            return

        if cuisine is not None and cuisine not in self.restaurant_map:
            await msg.reply(text="当前餐厅类型不支持查询")
            return

        cuisine = self.restaurant_map[cuisine] if cuisine is not None else '|'.join(self.restaurant_map.values())
        response = requests.get(self.api_uri, params={
            'key': self.api_key,
            'keywords': location,
            'types': cuisine,
            'region': city if city is not None else '上海市',
            'city_limit': 'true',
            'show_fields': 'business,photos',
            'page_size': self.page_size
        }).json()
        if response['status'] == '0':
            await msg.reply(text="API错误，请稍后重试")
            return
        restaurant_list = response['pois']
        res_list = restaurant_list
        if len(restaurant_list) > self.random_size:
            res_list = random.sample(restaurant_list, self.random_size)

        text = f"\n\n为你推荐{len(res_list)}家餐厅："

        for item in res_list:
            text += self.restaurant_praser(item)

        await msg.reply(text=text)

    def restaurant_praser(self, item):
        detail = item.get('business')
        text = {
            'name': item.get('name'),
            'rate': detail.get('rating') if detail is not None else None,
            'cost': detail.get('cost') if detail is not None else None,
            'tag': detail.get('tag') if detail is not None else None,
            'address': item.get('address'),
            'open_time': detail.get('opentime_week') if detail is not None else None
        }
        images = [t.get('url') for t in item.get('photos', [])]

        formatted = [
            f"{self.praser_map[key]}{value}"
            for key, value in text.items()
            if value is not None
        ]
        msg = MessageArray(Text('\n\n'+'\n'.join(formatted)))

        for img in images:
            msg.add_image(img)

        return msg

    async def on_load(self):
        # 插件加载时执行的操作, 可缺省
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")
        self.register_user_func(
            "DailyLuck",
            handler=self.what2eat,
            regex=f"^(?:(?:\[CQ:at,qq={bot_id}\]|@{bot_name})\s+)?今天吃什么\s+([^ \n]+)(?:\s+([^ \n]+))?(?:\s+([^ \n]+))?$",
        )