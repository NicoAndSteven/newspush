#!/bin/bash
# NewsPush 定时任务配置脚本
# 用于在 Linux 服务器上配置定时任务

echo "======================================"
echo "NewsPush 定时任务配置"
echo "======================================"

# 获取当前目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "项目目录: $PROJECT_DIR"

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3，请先安装 Python"
    exit 1
fi

echo "Python 版本: $(python3 --version)"

# 创建日志目录
mkdir -p "$PROJECT_DIR/logs"

# 创建定时任务脚本
CRON_SCRIPT="$PROJECT_DIR/run_scheduled.sh"
cat > "$CRON_SCRIPT" << 'EOF'
#!/bin/bash
# NewsPush 定时执行脚本

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$PROJECT_DIR/logs/newspush_$(date +\%Y\%m\%d_\%H\%M\%S).log"

echo "[$(date)] 开始执行 NewsPush" >> "$LOG_FILE"

cd "$PROJECT_DIR" || exit 1

# 激活虚拟环境（如果存在）
if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
elif [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
    source "$PROJECT_DIR/.venv/bin/activate"
fi

# 执行主程序
python3 main.py --once >> "$LOG_FILE" 2>&1

# 保留最近 30 天的日志
find "$PROJECT_DIR/logs" -name "newspush_*.log" -mtime +30 -delete

echo "[$(date)] 执行完成" >> "$LOG_FILE"
EOF

chmod +x "$CRON_SCRIPT"
echo "创建执行脚本: $CRON_SCRIPT"

# 显示当前的 crontab
echo ""
echo "当前的定时任务:"
crontab -l 2>/dev/null || echo "(暂无定时任务)"

echo ""
echo "======================================"
echo "配置选项:"
echo "======================================"
echo "1. 每小时执行一次 (推荐)"
echo "2. 每 2 小时执行一次"
echo "3. 每 4 小时执行一次"
echo "4. 每天执行一次 (早上 8 点)"
echo "5. 自定义配置"
echo "0. 退出"
echo ""

read -p "请选择 [0-5]: " choice

case $choice in
    1)
        CRON_EXPR="0 * * * *"
        DESC="每小时执行一次"
        ;;
    2)
        CRON_EXPR="0 */2 * * *"
        DESC="每 2 小时执行一次"
        ;;
    3)
        CRON_EXPR="0 */4 * * *"
        DESC="每 4 小时执行一次"
        ;;
    4)
        CRON_EXPR="0 8 * * *"
        DESC="每天早上 8 点执行"
        ;;
    5)
        echo ""
        echo "请输入 cron 表达式 (例如: 0 */3 * * * 表示每 3 小时)"
        echo "格式: 分 时 日 月 星期"
        read -p "Cron 表达式: " CRON_EXPR
        DESC="自定义: $CRON_EXPR"
        ;;
    0)
        echo "退出配置"
        exit 0
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

echo ""
echo "======================================"
echo "配置确认:"
echo "======================================"
echo "执行频率: $DESC"
echo "Cron 表达式: $CRON_EXPR"
echo "项目目录: $PROJECT_DIR"
echo "执行脚本: $CRON_SCRIPT"
echo ""

read -p "确认添加定时任务? [y/N]: " confirm

if [[ $confirm =~ ^[Yy]$ ]]; then
    # 创建新的 crontab 内容
    TEMP_CRON=$(mktemp)
    
    # 保留现有的非 NewsPush 任务
    crontab -l 2>/dev/null | grep -v "NewsPush" | grep -v "newspush" > "$TEMP_CRON" || true
    
    # 添加 NewsPush 任务
    echo "" >> "$TEMP_CRON"
    echo "# NewsPush 定时任务 - $(date)" >> "$TEMP_CRON"
    echo "$CRON_EXPR $CRON_SCRIPT >> $PROJECT_DIR/logs/cron.log 2>&1" >> "$TEMP_CRON"
    
    # 安装新的 crontab
    crontab "$TEMP_CRON"
    rm "$TEMP_CRON"
    
    echo ""
    echo "✅ 定时任务已添加!"
    echo ""
    echo "当前的定时任务:"
    crontab -l
    echo ""
    echo "日志文件位置: $PROJECT_DIR/logs/"
    echo ""
    echo "手动测试执行: $CRON_SCRIPT"
    
    # 询问是否立即执行一次
    echo ""
    read -p "是否立即执行一次测试? [y/N]: " run_now
    
    if [[ $run_now =~ ^[Yy]$ ]]; then
        echo ""
        echo "======================================"
        echo "立即执行一次..."
        echo "======================================"
        bash "$CRON_SCRIPT"
        echo ""
        echo "执行完成! 查看最新日志:"
        echo "tail -50 $PROJECT_DIR/logs/newspush_*.log | tail -50"
    fi
else
    echo "已取消"
    exit 0
fi
