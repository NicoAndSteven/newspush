#!/bin/bash
# NewsPush 定时执行脚本

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$PROJECT_DIR/logs/newspush_$(date +\%Y\%m\%d_\%H\%M\%S).log"
LOCK_FILE="$PROJECT_DIR/.newspush.lock"

# 检查是否已有进程在运行
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "[$(date)] 已有 NewsPush 进程在运行 (PID: $PID)，跳过本次执行" >> "$LOG_FILE"
        exit 0
    else
        echo "[$(date)] 发现残留锁文件，清理中..." >> "$LOG_FILE"
        rm -f "$LOCK_FILE"
    fi
fi

# 创建锁文件
echo $$ > "$LOCK_FILE"
echo "[$(date)] 开始执行 NewsPush (PID: $$)" >> "$LOG_FILE"

# 确保退出时清理锁文件
trap 'rm -f "$LOCK_FILE"; echo "[$(date)] 锁文件已清理" >> "$LOG_FILE"' EXIT

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

# 执行主程序（-u 禁用输出缓冲，确保日志实时写入）
echo "[$(date)] 开始执行 main.py..." >> "$LOG_FILE"
PYTHONUNBUFFERED=1 python3 -u main.py --once >> "$LOG_FILE" 2>&1
EXIT_CODE=$?
echo "[$(date)] main.py 执行完成，退出码: $EXIT_CODE" >> "$LOG_FILE"

# 保留最近 30 天的日志
find "$PROJECT_DIR/logs" -name "newspush_*.log" -mtime +30 -delete

echo "[$(date)] 执行完成" >> "$LOG_FILE"
