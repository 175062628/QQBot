import sys
import os
from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core import GroupMessage
import time
import re

sys.path.append(os.path.dirname(__file__))
from .probability import ProbabilityDistributor

bot = CompatibleEnrollment  # 兼容回调函数注册器

from utils import load_config_from_yaml
config = load_config_from_yaml("config.yaml")
bot_id = config.get("bot_id")
bot_name = config.get("bot_name")

class CS2CaseSimulator(BasePlugin):
    name = "CS2CaseSimulator" # 插件名称
    version = "0.0.2" # 插件版本
    author = "Ethan Ye"
    info = "CS:GO开箱模拟器，使用方式：[@Bot ]开箱 (梦魇武器箱|0) [开箱数]"
    description = "CS:GO开箱模拟器，适用于私聊和群聊"

    case_list = [
        "梦魇武器箱",
        "反冲武器箱",
        "热潮武器箱",
        "手套武器箱",
        "千瓦武器箱",
        "突围大行动武器箱"
    ]
    case_dic = {
        "梦魇武器箱": "Dreams_And_Nightmares",
        "0": "Dreams_And_Nightmares",
        "反冲武器箱": "Recoil",
        "1": "Recoil",
        "热潮武器箱": "Fever_Weapon",
        "2": "Fever_Weapon",
        "手套武器箱": "Glove",
        "3": "Glove",
        "千瓦武器箱": "Kilowatt",
        "4": "Kilowatt",
        "突围大行动武器箱": "Operation_Breakout_Weapon",
        "5": "Operation_Breakout_Weapon",
    }
    user_list = {}
    banned_list = {}
    value_map = {
        "Consumer": 0,
        "Industrial": 1,
        "Mil-Spec": 2,
        "Restricted": 3,
        "Classified": 4,
        "Covert": 5,
        "Contraband": 6,
    }
    interval = 1000 * 60 * 60
    banned_interval = 1000 * 60 * 60 * 24
    show_size = 5
    user_interval_map = {}
    case_limit = 1000

    async def help_info(self, msg: GroupMessage):
        await msg.reply(text=f"选择武器箱(示例：[@Bot ]开箱 (梦魇武器箱|0) [开箱数])\n当前武器箱列表{self.get_available_list()}")

    async def simulator(self, msg: GroupMessage):
        param_list = msg.raw_message.split(' ')
        target_case = param_list[-1] if param_list[-2] == "开箱" else param_list[-2]
        case_size = min(1 if param_list[-2] == "开箱" else int(param_list[-1]), self.case_limit)
        timestamp = int(time.time() * 1000)

        if (msg.sender.user_id in self.user_interval_map
                and msg.sender.user_id not in self.banned_list
                and timestamp - self.user_interval_map[msg.sender.user_id] < self.interval):
            self.banned_list[msg.sender.user_id] = timestamp
            await msg.reply(text=f"触发截流限制，请在{self.format_seconds(int((self.user_interval_map[msg.sender.user_id] + self.interval - timestamp) / 1000))}后重试，若在此次截流期间再次触发截流，该账户将被屏蔽一天；屏蔽期间每触发一次截流，额外追加一天")
            return

        if msg.sender.user_id in self.banned_list:
            if (timestamp - self.user_interval_map[msg.sender.user_id] < self.interval
                    or self.banned_list[msg.sender.user_id] > timestamp):
                self.banned_list[msg.sender.user_id] += self.banned_interval
                return
            else:
                self.banned_list.pop(msg.sender.user_id)

        if target_case not in self.case_dic:
            await msg.reply(text=f"暂不支持该武器箱，目前可用武器箱如下：{self.get_available_list()}")
            return

        probability_distributor = ProbabilityDistributor(f"./plugins/CS2CaseSimulator/CaseList/{self.case_dic[target_case]}.json")
        self.user_interval_map[msg.sender.user_id] = timestamp
        items = []

        for i in range(case_size):
            items.append(probability_distributor.pick_item())

        sorted_items = sorted(items, key=lambda x: -self.value_map[x['品质']])
        red_items = sum(1 for x in sorted_items if self.value_map[x['品质']] >= 5)

        _iter = max(min(case_size, self.show_size), red_items)
        if min(case_size, self.show_size) >= red_items:
            text = f"本轮开箱{case_size}个，最好的{_iter}个物品是："
        else:
            text = f"本轮开箱{case_size}个，运气爆棚，有{red_items}个红色及以上物品："

        for i in range(_iter):
            text += (f"\n物品：{sorted_items[i]['物品']}"
                    f"\n品质：{sorted_items[i]['品质']}"
                    f"\n磨损：{sorted_items[i]['磨损']}"
                    f"\n磨损值：{sorted_items[i]['磨损值']}"
                    f"\n模板号：{sorted_items[i]['模板号']}")
            if sorted_items[i]['梯度'] is not None:
                text += f"\n梯度：{sorted_items[i]['梯度']}"
            if i != _iter - 1:
                text += f"\n"

        await msg.reply(text=text)

    async def free_list(self, msg: GroupMessage):
        pattern = r'qq=(\d+)'
        qq_numbers = re.findall(pattern, msg.raw_message)
        for qq in qq_numbers:
            self.banned_list.pop(int(qq), None)
            self.user_interval_map.pop(int(qq), None)

    def get_available_list(self):
        text = ""
        for index, value in enumerate(self.case_list):
            text += f"\n{index} -- {value}"
        return text

    @staticmethod
    def format_seconds(seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}小时{minutes:02d}分钟{seconds:02d}秒"
        elif minutes > 0:
            return f"{minutes}分钟{seconds:02d}秒"
        else:
            return f"{seconds}秒"

    async def on_load(self):
        # 插件加载时执行的操作, 可缺省
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")
        self.register_user_func(
            "CS2CaseSimulator",
            handler=self.simulator,
            regex=f"^(?:\[CQ:at,qq={bot_id}\]|@{bot_name})\s+开箱\s+.+(?:\s+\d+)?$|^开箱\s+.+(?:\s+\d+)?$",
        )
        self.register_user_func(
            "CS2CaseSimulatorHelper",
            handler=self.help_info,
            regex=f"^(?:\[CQ:at,qq={bot_id}\]|@{bot_name})\s+开箱$|^开箱$",
        )
        self.register_admin_func(
            "CS2CaseSimulatorAdmin",
            handler=self.free_list,
            regex=f"^(?:\[CQ:at,qq={bot_id}\]|@{bot_name})\s+开箱赦免(?:\[CQ:at,qq=.+\])+$|^开箱赦免(?:\[CQ:at,qq=.+\])+$",
        )