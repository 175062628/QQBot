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
        "梦魇武器箱",
        "反冲武器箱",
        "热潮武器箱"
    ]
    case_dic = {
        "梦魇武器箱": "Dreams_And_Nightmares",
        "0": "Dreams_And_Nightmares",
        "反冲武器箱": "Recoil",
        "1": "Recoil",
        "热潮武器箱": "Fever_Weapon",
        "2": "Fever_Weapon"
    }

    async def help_info(self, msg: GroupMessage):
        await msg.reply(text=f"选择武器箱(示例：开箱梦魇武器箱 / 开箱0)\n当前武器箱列表{self.get_available_list()}")

    async def simulator(self, msg: GroupMessage):
        target_case = msg.raw_message.split(' ')[-1]
        if target_case not in self.case_dic:
            await msg.reply(text=f"暂不支持该武器箱，目前可用武器箱如下：{self.get_available_list()}")
            return
        probability_distributor = ProbabilityDistributor(f"./plugins/CS2CaseSimulator/CaseList/{self.case_dic[target_case]}.json")
        item = probability_distributor.pick_item()

        text = (f"物品：{item['物品']}\n"
                f"品质：{item['品质']}\n"
                f"磨损：{item['磨损']}\n"
                f"磨损值：{item['磨损值']}\n"
                f"模板号：{item['模板号']}")
        if item['梯度'] is not None:
            text += f"\n梯度：{item['梯度']}"
        await msg.reply(text=text)

    def get_available_list(self):
        text = ""
        for index, value in enumerate(self.case_list):
            text += f"\n{index} -- {value}"
        return text

    async def on_load(self):
        # 插件加载时执行的操作, 可缺省
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")
        self.register_admin_func(
            "CS2CaseSimulator",
            handler=self.simulator,
            regex="^(?:\[CQ:at,qq=3909177943\]|@Bot)\s+开箱\s+.+|^开箱\s+.+",
            permission_raise=True
        )
        self.register_admin_func(
            "CS2CaseSimulatorHelper",
            handler=self.help_info,
            regex="^(?:\[CQ:at,qq=3909177943\]|@Bot)\s+开箱$|^开箱$",
            permission_raise=True
        )