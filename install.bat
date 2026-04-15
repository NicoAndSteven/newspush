@echo off
echo ==========================================
echo    NewsPush 安装脚本
echo ==========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [1/5] 检测到 Python 版本:
python --version
echo.

REM 创建虚拟环境
echo [2/5] 创建虚拟环境...
if exist venv (
    echo      虚拟环境已存在，跳过创建
) else (
    python -m venv venv
    echo      虚拟环境创建完成
)
echo.

REM 激活虚拟环境
echo [3/5] 激活虚拟环境...
call venv\Scripts\activate
echo      虚拟环境已激活
echo.

REM 升级 pip
echo [4/5] 升级 pip...
python -m pip install --upgrade pip
echo.

REM 安装依赖
echo [5/5] 安装依赖包...
pip install -r requirements.txt
echo.

REM 创建必要目录
echo 创建必要目录...
mkdir data 2>nul
mkdir downloads\videos 2>nul
mkdir downloads\news 2>nul
mkdir results 2>nul
mkdir assets 2>nul
echo.

REM 创建环境变量文件
echo 创建环境变量模板...
if not exist .env (
    copy .env.example .env
    echo      已创建 .env 文件，请编辑配置你的 API 密钥
) else (
    echo      .env 文件已存在
)
echo.

echo ==========================================
echo    安装完成！
echo ==========================================
echo.
echo 使用方法:
echo   1. 编辑 .env 文件，配置你的 API 密钥
echo   2. 运行: python main.py --once
echo   3. 或运行: python main.py --schedule 1
echo.
echo 更多信息请查看 README.md
echo.
pause
