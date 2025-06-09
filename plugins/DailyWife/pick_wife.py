import random

class PickWife:
    def __init__(self, member_list, married_list, blacklist):
        self.member_list = member_list
        self.married_list = married_list
        self.blacklist_qqs = blacklist
        self.married_qqs = self._extract_married_qqs()

    def _extract_married_qqs(self):
        return {
            str(item['qq_number'])
            for item in self.married_list
            if 'qq_number' in item and item['qq_number']
        }

    def remove_duplicates(self):
        return [
            member for member in self.member_list
            if (str(member.get('user_id', '')) not in self.married_qqs and
                str(member.get('user_id', '')) not in self.blacklist_qqs)
        ]

    def pick_wife(self):
        available_list = self.remove_duplicates()
        if not available_list:
            return None
        random_index = random.randint(0, len(available_list) - 1)
        return available_list[random_index]