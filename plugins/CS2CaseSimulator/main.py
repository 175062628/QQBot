import sys
import os
import re
from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core import GroupMessage, PrivateMessage

sys.path.append(os.path.dirname(__file__))
from utils.probability import ProbabilityDistributor

bot = CompatibleEnrollment  # 兼容回调函数注册器

class CS2CaseSimulator(BasePlugin):
    name = "CS2CaseSimulator" # 插件名称
    version = "0.0.1" # 插件版本
    case_list = [
        "梦魇武器箱"
    ]
    case_dic = {
        "梦魇武器箱": "Dreams_And_Nightmares",
        "0": "Dreams_And_Nightmares",
    }

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        if msg.raw_message == "?:\[CQ:at,qq=1706773717\]|@Bot)\s开箱":
            await msg.reply(text=f"选择武器箱 / 使用方式：开箱 梦魇武器箱 || 开箱 0 / 0 对应梦魇 / 目前可用武器箱如下：{self.case_list}")
            return
        pattern = r'(?:\[CQ:at,qq=1706773717\]|@Bot)\s+开箱\s*'
        if re.match(pattern, msg.raw_message):
            target_case = msg.raw_message.split(' ')[-1]
            if target_case not in self.case_dic:
                await msg.reply(text=f"暂不支持该武器箱，目前可用武器箱如下：{self.case_list}")
                return
            probability_distributor = ProbabilityDistributor(f"./plugins/CS2CaseSimulator/CaseList/{self.case_dic[target_case]}.json")
            item = probability_distributor.pick_item()

            text = (f"物品：{item['物品']}\n"
                    f"品质：{item['品质']}\n"
                    f"磨损：{item['磨损']}\n"
                    f"磨损值：{item['磨损值']}")
            if item['梯度'] is not None:
                text += f"\n梯度：{item['梯度']}"
            await msg.reply(text=text)
            return

    @bot.private_event()
    async def on_private_event(self, msg: PrivateMessage):
        if msg.raw_message == "开箱":
            await msg.reply(text=f"选择武器箱 / 使用方式：开箱 梦魇武器箱 || 开箱 0 / 0 对应梦魇 / 目前可用武器箱如下：{self.case_list}")
            return
        pattern = r'开箱\s*(.*)'
        if re.match(pattern, msg.raw_message):
            target_case = msg.raw_message.split(' ')[-1]
            if target_case not in self.case_dic:
                await msg.reply(text=f"暂不支持该武器箱，目前可用武器箱如下：{self.case_list}")
                return
            probability_distributor = ProbabilityDistributor(f"./plugins/CS2CaseSimulator/CaseList/{self.case_dic[target_case]}.json")
            item = probability_distributor.pick_item()

            text = (f"物品：{item['物品']}\n"
                    f"品质：{item['品质']}\n"
                    f"磨损：{item['磨损']}\n"
                    f"磨损值：{item['磨损值']}")
            if item['梯度'] is not None:
                text += f"\n梯度：{item['梯度']}"
            await msg.reply(text=text)
            return

    async def on_load(self):
        # 插件加载时执行的操作, 可缺省
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")