# ========= 导入必要模块 ==========
from ncatbot.core import BotClient, GroupMessage, PrivateMessage
from ncatbot.utils import get_log
from utils import load_config_from_yaml

# ========== 创建 BotClient ==========
bot = BotClient()
_log = get_log()
config = load_config_from_yaml("config.yaml")
bot_id = config.get("bot_id")
bot_name = config.get("bot_name")
root_id = config.get("root_id")

if __name__ == "__main__":
    bot.run(
        bt_uin=bot_id,
        root=root_id,
        enable_webui_interaction=False
    )
