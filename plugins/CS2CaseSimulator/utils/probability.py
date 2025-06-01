import json
import random
from typing import Dict, List, Any, Optional

class ProbabilityDistributor:
    def __init__(self, json_path: str):
        """初始化概率分布器，从JSON文件加载配置"""
        self.json_path = json_path
        self.config = self._load_config()
        self.star_track_prob = self.config.get("StarTrack", 0)
        self.item_list = self._parse_item_list()
        self.base_distribution = self._parse_base_distribution()

    def _load_config(self) -> Dict[str, float]:
        """加载并验证JSON配置"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件 '{self.json_path}' 不存在")
        except json.JSONDecodeError:
            raise ValueError(f"配置文件 '{self.json_path}' 不是有效的JSON格式")

    def _parse_base_distribution(self) -> Dict[str, float]:
        """解析基础概率分布（排除条件概率项）"""
        return {
            item: prob for item, prob in self.config.items()
            if item in {"Consumer","Industrial","Mil-Spec","Restricted","Classified","Covert","Contraband"} and prob > 0
        }

    def _parse_item_list(self) -> Dict[str, List[Dict[str, Any]]]:
        """解析基础概率分布（排除条件概率项）"""
        items = self.config.get("List", [])
        grouped_items = {}
        for item in items:
            quality = item.get("Quality")
            if quality:
                # 如果品质键不存在，创建一个空列表
                if quality not in grouped_items:
                    grouped_items[quality] = []
                # 将物品添加到对应品质的列表中
                grouped_items[quality].append(item)
        return grouped_items

    def select_quality(self) -> str:
        # 处理基础概率分布
        rand_val = random.random()
        cumulative = 0
        for item, prob in self.base_distribution.items():
            cumulative += prob
            if rand_val < cumulative:
                return item

        # 默认返回（理论上不会执行到这里）
        return next(iter(self.base_distribution))

    def uniform_choice(self, quality) -> Any:
        """对列表进行等概率随机选择"""
        if not self.item_list[quality]:
            raise ValueError("列表不能为空")
        return random.choice(self.item_list[quality])

    @staticmethod
    def select_tier_from_item(item: Dict[str, Any]) -> Optional[str]:
        tier_list = item.get("TierList")
        if not tier_list or not isinstance(tier_list, dict):
            return None
        tiers = list(tier_list.keys())
        probabilities = list(tier_list.values())
        rand = random.random()
        cumulative = 0
        for i, tier in enumerate(tiers):
            cumulative += probabilities[i]
            if rand < cumulative:
                return tier
        return tiers[-1] if tiers else None

    @staticmethod
    def generate_random_decimal(min_val: float, max_val: float) -> float:
        if min_val > max_val:
            raise ValueError("最小值不能大于最大值")
        return round(random.uniform(min_val, max_val), 10)

    @staticmethod
    def _float_value_name(value: float) -> str:
        if value < 0.07:
            return "崭新出厂"
        if value < 0.15:
            return "略有磨损"
        if value < 0.38:
            return "久经沙场"
        if value < 0.45:
            return "破损不堪"
        return "战痕累累"

    @staticmethod
    def rename_star_track(original_name):
        if "（★）" in original_name:
            modified_name = original_name.replace("（★）", "（★ StarTrak™）")
        else:
            parts = original_name.split(" | ", 1)
            if len(parts) == 2:
                prefix, suffix = parts
                modified_name = f"{prefix} (StarTrak™) | {suffix}"
            else:
                modified_name = f"{original_name} (StarTrak™)"
        return modified_name

    def pick_item(self):
        quality = self.select_quality()
        item = self.uniform_choice(quality)
        float_value = self.generate_random_decimal(item["FloatValueMin"], item["FloatValueMax"])
        float_value_name = self._float_value_name(float_value)
        tier = self.select_tier_from_item(item) if "TierList" in item else None
        star_track = True if item["StarTrack"] == "True" and self.generate_random_decimal(0, 1) < self.config.get("StarTrack", 0) else False
        name = item["Name"] if not star_track else self.rename_star_track(item["Name"])

        return {
            "物品": name,
            "品质": quality,
            "磨损": float_value_name,
            "磨损值": float_value,
            "梯度": tier
        }