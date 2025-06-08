from typing import Dict, Any


class Explain:
    def __init__(self, response):
        self.luck = self._get_luck(response["type"])
        self.description = response["daily"]
    @staticmethod
    def _get_luck(_type):
        if _type == 0:
            return "无类型"
        if _type == 1:
            return "大吉"
        if _type == 2:
            return "中吉"
        if _type == 3:
            return "吉"
        if _type == 4:
            return "末吉"
        if _type == 5:
            return "凶"
        return "大凶"
    def get_res(self) -> Dict[str, Any]:
        return {
            "luck" : self.luck,
            "description" : self.description
        }