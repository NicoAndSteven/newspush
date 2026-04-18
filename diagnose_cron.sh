#!/bin/bash
# NewsPush 定时任务诊断脚本

echo "======================================"
echo "NewsPush 定时任务诊断"
echo "======================================"

# 1. 检查 crontab
echo ""
echo "[1] 检查 crontab 配置:"
echo "--------------------------------------"
crontab -l 2>/dev/null || echo "未配置 crontab"

# 2. 检查脚本文件
echo ""
echo "[2] 检查执行脚本:"
echo "--------------------------------------"
if [ -f "run_scheduled.sh" ]; then
    echo "✅ run_scheduled.sh 存在"
    ls -la run_scheduled.sh
else
    echo "❌ run_scheduled.sh 不存在"
fi

# 3. 检查日志目录
echo ""
echo "[3] 检查日志目录:"
echo "--------------------------------------"
if [ -d "logs" ]; then
    echo "✅ logs 目录存在"
    echo "日志文件列表:"
    ls -la logs/ 2>/dev/null || echo "  (空)"
else
    echo "❌ logs 目录不存在"
fi

# 4. 检查 cron 日志
echo ""
echo "[4] 检查 cron 日志:"
echo "--------------------------------------"
if [ -f "logs/cron.log" ]; then
    echo "cron.log 最后 20 行:"
    tail -20 logs/cron.log
else
    echo "❌ logs/cron.log 不存在"
fi

# 5. 检查最新的执行日志
echo ""
echo "[5] 检查最新执行日志:"
echo "--------------------------------------"
LATEST_LOG=$(ls -t logs/newspush_*.log 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
    echo "最新日志: $LATEST_LOG"
    echo "最后 30 行:"
    tail -30 "$LATEST_LOG"
else
    echo "❌ 没有找到执行日志"
fi

# 6. 检查 Python 环境
echo ""
echo "[6] 检查 Python 环境:"
echo "--------------------------------------"
echo "Python 版本:"
python3 --version 2>/dev/null || echo "❌ python3 未找到"

# 7. 检查虚拟环境
echo ""
echo "[7] 检查虚拟环境:"
echo "--------------------------------------"
if [ -d "venv" ]; then
    echo "✅ venv 目录存在"
elif [ -d ".venv" ]; then
    echo "✅ .venv 目录存在"
else
    echo "⚠️  虚拟环境不存在（可能使用系统 Python）"
fi

# 8. 检查 .env 文件
echo ""
echo "[8] 检查 .env 配置:"
echo "--------------------------------------"
if [ -f ".env" ]; then
    echo "✅ .env 文件存在"
    echo "配置项:"
    grep -E "^(DASHSCOPE|WECHAT|MAX_)" .env | sed 's/=.*/=***/'
else
    echo "❌ .env 文件不存在"
fi

# 9. 检查 cron 服务状态
echo ""
echo "[9] 检查 cron 服务状态:"
echo "--------------------------------------"
systemctl status crond 2>/dev/null || service cron status 2>/dev/null || echo "无法检查 cron 状态"

# 10. 手动测试执行
echo ""
echo "======================================"
echo "诊断完成"
echo "======================================"
echo ""
echo "如需手动测试，请运行:"
echo "  bash run_scheduled.sh"
echo ""
echo "如需查看完整日志，请运行:"
echo "  cat logs/cron.log"
echo "  cat logs/newspush_*.log"
