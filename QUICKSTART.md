# NewsPush 快速开始指南

## 5 分钟快速启动

### 1. 一键安装（Windows）

双击运行 `install.bat` 文件，或打开命令行执行：

```bash
install.bat
```

### 2. 配置 API 密钥

编辑 `.env` 文件，填入至少一个 AI API 密钥：

```env
OPENAI_API_KEY=sk-your-key-here
# 或
ANTHROPIC_API_KEY=sk-ant-your-key-here
# 或
DEEPSEEK_API_KEY=your-deepseek-key
```

### 3. 运行系统

```bash
# 执行一次完整流程
python main.py --once

# 或启动定时任务（每小时运行）
python main.py --schedule 1
```

---

## 功能演示

### 演示 1: 抓取新闻

```bash
python main.py --fetch-only
```

输出示例：
```
[2024-01-15 10:30:00] 开始抓取新闻...
  从 https://news.google.com/rss 获取 20 条新闻
  从 https://feeds.bbci.co.uk/news/world/rss.xml 获取 18 条新闻
  保存 12 条过滤后的新闻到数据库
```

### 演示 2: AI 分析新闻

```bash
python main.py --analyze-only
```

输出示例：
```
[2024-01-15 10:35:00] 开始 AI 分析新闻...
  分析: 香港股市今日大涨，科技股领涨...
    ✓ 值得制作视频 (分数: 85)
  分析: 国际原油价格持续下跌...
    ✓ 值得制作视频 (分数: 72)
```

### 演示 3: 完整流程

```bash
python main.py --once
```

输出示例：
```
============================================================
[2024-01-15 10:40:00] 开始执行新闻推送流水线
============================================================
[2024-01-15 10:40:01] 开始抓取新闻...
  从 https://news.google.com/rss 获取 20 条新闻
  保存 12 条过滤后的新闻到数据库
[2024-01-15 10:40:05] 开始 AI 分析新闻...
  分析: 香港股市今日大涨...
    ✓ 值得制作视频 (分数: 85)
[2024-01-15 10:40:10] 开始生成视频脚本...
  生成脚本: 香港股市今日大涨...
[2024-01-15 10:40:15] 搜索相关视频素材...
  搜索: 香港 股市 大涨
[2024-01-15 10:40:30] 创建 CapCut 草稿...
  创建草稿: C:\Users\...\CapCut\Projects\香港股市大涨

完成！
  - 新闻: 12 条
  - 分析: 12 条
  - 脚本: 2 个
  - 视频: 2 个
  - 草稿: 2 个
============================================================
```

---

## 使用 n8n 可视化工作流

### 1. 安装 n8n

```bash
npx n8n
```

### 2. 导入工作流

1. 打开浏览器访问 http://localhost:5678
2. 点击左侧菜单 "Workflows"
3. 点击 "Import from File"
4. 选择 `n8n_workflows/news_capture_workflow.json`
5. 同样导入 `video_generation_workflow.json`

### 3. 配置凭证

1. 点击左侧 "Credentials"
2. 添加 OpenAI API Key
3. 添加 Telegram Bot Token（可选，用于通知）
4. 添加数据库连接（SQLite）

### 4. 激活工作流

1. 打开新闻捕捉工作流
2. 点击右上角 "Active" 开关
3. 工作流将每小时自动运行

---

## 项目结构说明

```
newspush/
├── src/
│   ├── news_capture/          # 📰 新闻捕捉
│   │   └── rss_fetcher.py     # RSS/API 抓取
│   ├── video_downloader/      # 📹 视频下载
│   │   └── ytdlp_downloader.py # yt-dlp 封装
│   ├── ai_processor/          # 🤖 AI 处理
│   │   └── content_analyzer.py # 分析 + 脚本生成
│   └── capcut_automation/     # ✂️ CapCut 自动化
│       └── capcut_api.py      # 草稿创建
├── n8n_workflows/             # 🔄 n8n 工作流
├── data/                      # 💾 SQLite 数据库
├── downloads/                 # 📁 下载文件
│   ├── videos/               # 视频素材
│   └── news/                 # 新闻内容
├── results/                   # 📝 生成的脚本
├── main.py                    # 🚀 主程序
└── config.py                  # ⚙️ 配置文件
```

---

## 常见问题

### Q: 如何修改关键词？

编辑 `.env` 文件：

```env
KEYWORDS_HONGKONG=香港,港府,港股,恒生指数
KEYWORDS_INTERNATIONAL=国际,美国,欧洲,日本
KEYWORDS_HOT=热点,热搜,爆款, viral
```

### Q: 如何添加新的 RSS 源？

编辑 `config.py`：

```python
RSS_SOURCES = [
    "https://news.google.com/rss",
    "https://www.reuters.com/rssFeed/worldNews",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://your-custom-rss.com/feed",  # 添加新源
]
```

### Q: 如何更换 AI 模型？

编辑 `.env`，配置你想使用的 API：

```env
# OpenAI GPT-4
OPENAI_API_KEY=sk-...

# 或 Claude
ANTHROPIC_API_KEY=sk-ant-...

# 或 DeepSeek（更便宜）
DEEPSEEK_API_KEY=...
```

系统会自动检测并使用第一个可用的 API。

### Q: 视频下载失败怎么办？

1. 确保 yt-dlp 已安装：
   ```bash
   pip install yt-dlp
   ```

2. 某些平台（如 B站）需要 cookies，可以使用：
   ```python
   options = {'cookiesfrombrowser': ('chrome',)}
   downloader.download_video(url, options)
   ```

### Q: CapCut 草稿在哪里？

默认位置：
- Windows: `%LOCALAPPDATA%\CapCut\User Data\Projects`
- macOS: `~/Movies/CapCut/User Data/Projects`

---

## 下一步

1. **查看详细文档**: [README.md](README.md)
2. **自定义模板**: 编辑 `src/capcut_automation/capcut_api.py`
3. **扩展数据源**: 在 `src/news_capture/` 添加新的抓取器
4. **部署到服务器**: 使用 Docker 或 systemd 定时任务

---

## 获取帮助

- 查看日志：`data/news.db` 数据库文件
- 调试模式：在代码中添加 `print()` 语句
- 提交 Issue：描述问题和复现步骤

---

**祝你使用愉快！** 🎉
