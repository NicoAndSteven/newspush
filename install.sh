#!/bin/bash

echo "=========================================="
echo "   NewsPush 安装脚本"
echo "=========================================="
echo

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3，请先安装 Python 3.8+"
    exit 1
fi

echo "[1/5] 检测到 Python 版本:"
python3 --version
echo

# 创建虚拟环境
echo "[2/5] 创建虚拟环境..."
if [ -d "venv" ]; then
    echo "     虚拟环境已存在，跳过创建"
else
    python3 -m venv venv
    echo "     虚拟环境创建完成"
fi
echo

# 激活虚拟环境
echo "[3/5] 激活虚拟环境..."
source venv/bin/activate
echo "     虚拟环境已激活"
echo

# 升级 pip
echo "[4/5] 升级 pip..."
pip install --upgrade pip
echo

# 安装依赖
echo "[5/5] 安装依赖包..."
pip install -r requirements.txt
echo

# 创建必要目录
echo "创建必要目录..."
mkdir -p data
mkdir -p downloads/videos
mkdir -p downloads/news
mkdir -p results
mkdir -p assets
echo

# 创建环境变量文件
echo "创建环境变量模板..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "     已创建 .env 文件，请编辑配置你的 API 密钥"
else
    echo "     .env 文件已存在"
fi
echo

echo "=========================================="
echo "   安装完成！"
echo "=========================================="
echo
echo "使用方法:"
echo "  1. 编辑 .env 文件，配置你的 API 密钥"
echo "  2. 激活虚拟环境: source venv/bin/activate"
echo "  3. 运行: python main.py --once"
echo "  4. 或运行: python main.py --schedule 1"
echo
echo "更多信息请查看 README.md"
echo
