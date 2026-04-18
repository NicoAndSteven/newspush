#!/bin/bash
# NewsPush 定时执行脚本

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$PROJECT_DIR/logs/newspush_$(date +\%Y\%m\%d_\%H\%M\%S).log"

echo "[$(date)] 开始执行 NewsPush" >> "$LOG_FILE"

cd "$PROJECT_DIR" || exit 1

# 激活虚拟环境（检查多种可能的名称）
if [ -f "$PROJECT_DIR/venv38/bin/activate" ]; then
    source "$PROJECT_DIR/venv38/bin/activate"
    echo "[$(date)] 已激活虚拟环境: venv38" >> "$LOG_FILE"
elif [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
    echo "[$(date)] 已激活虚拟环境: venv" >> "$LOG_FILE"
elif [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
    source "$PROJECT_DIR/.venv/bin/activate"
    echo "[$(date)] 已激活虚拟环境: .venv" >> "$LOG_FILE"
else
    echo "[$(date)] 警告: 未找到虚拟环境，使用系统 Python" >> "$LOG_FILE"
fi

# 执行主程序
python3 main.py --once >> "$LOG_FILE" 2>&1

# 保留最近 30 天的日志
find "$PROJECT_DIR/logs" -name "newspush_*.log" -mtime +30 -delete

echo "[$(date)] 执行完成" >> "$LOG_FILE"
