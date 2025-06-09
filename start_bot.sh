#!/bin/bash
# 颜色定义（用于日志提示）
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

QQ_NUMBER=3909177943
SESSION_NAME="qq_bot_session"
LOG_DIR="./logs"
QQ_LOG="$LOG_DIR/qq.log"
BOT_LOG="$LOG_DIR/bot.log"
SESSION_NAME="qq_bot_session"

mkdir -p "$LOG_DIR"
if [ ! -d "QQBot" ]; then
    echo -e "${YELLOW}[提示]${NC} QQBot目录未找到，假设launch.py在当前目录"
fi

echo -e "${GREEN}[信息]${NC} 正在创建tmux会话: $SESSION_NAME"
tmux new-session -d -s "$SESSION_NAME"

tmux send-keys -t "$SESSION_NAME" "echo '===== 启动XVFB+QQ =====' > $QQ_LOG 2>&1" Enter
tmux send-keys -t "$SESSION_NAME" "xvfb-run -a qq --no-sandbox -q $QQ_NUMBER > $QQ_LOG 2>&1 &" Enter
tmux send-keys -t "$SESSION_NAME" "echo 'QQ进程已启动，日志: $QQ_LOG'" Enter
tmux send-keys -t "$SESSION_NAME" "sleep 10" Enter  # 等待QQ启动

tmux send-keys -t "$SESSION_NAME" "echo '===== 启动Python机器人 =====' > $BOT_LOG 2>&1" Enter
tmux send-keys -t "$SESSION_NAME" "python3 launch.py > $BOT_LOG 2>&1" Enter
tmux send-keys -t "$SESSION_NAME" "echo '机器人进程已启动，日志: $BOT_LOG'" Enter

echo -e "${GREEN}[成功]${NC} 已在tmux会话中启动QQ和机器人"
echo -e "${YELLOW}[操作提示]${NC}"
echo "  查看会话: tmux list-sessions"
echo "  连接会话: tmux attach -t $SESSION_NAME"
echo "  QQ日志: tail -f $QQ_LOG"
echo "  机器人日志: tail -f $BOT_LOG"
echo "  退出会话: Ctrl+B + D"