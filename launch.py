# ========= 导入必要模块 ==========
from ncatbot.core import BotClient, GroupMessage, PrivateMessage
from ncatbot.utils import get_log

# ========== 创建 BotClient ==========
bot = BotClient()
_log = get_log()

if __name__ == "__main__":
    bot.run(
        bt_uin="3909177943",
        root="1633360356",
        enable_webui_interaction=False
    )