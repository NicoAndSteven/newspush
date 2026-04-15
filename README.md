# NewsPush - 智能新闻分析与邮箱推送系统

一个全自动的新闻抓取、深度分析、智能点评和邮箱推送系统。专为 GitHub Actions 设计，零本地存储，分析完成后自动清理。

## 功能特性

### 核心功能
- **新闻抓取**: RSS 订阅实时抓取，支持多个国际新闻源
- **AI 深度分析**: 不限题材，自动分析新闻价值、背景、影响
- **智能点评生成**: 基于分析结果生成专业的新闻点评文章
- **邮箱自动推送**: 将生成的文章自动发送到指定邮箱
- **零本地存储**: 原始新闻不保存，只保留分析结果，推送后自动清理
- **GitHub Actions 支持**: 完全自动化运行，无需服务器

### 技术亮点
- **newspaper3k 图片抓取**: 自动抓取新闻中的所有图片
- **阿里云百炼 Qwen**: 支持联网搜索，获取最新信息
- **邮件附件支持**: 同时发送 Markdown 和 Word 文档
- **敏感度检查**: 自动识别敏感内容，使用两阶段分析

## 项目结构

```
newspush/
├── src/
│   ├── news_capture/              # 新闻捕捉模块
│   │   └── rss_fetcher.py         # RSS 抓取
│   ├── ai_processor/              # AI 处理模块
│   │   ├── deep_analyzer.py       # 深度分析 + 点评生成
│   │   └── two_stage_analyzer.py  # 两阶段分析（事实核查）
│   ├── storage/                   # 存储模块
│   │   └── json_storage.py        # JSON 存储（可选）
│   └── utils/                     # 工具模块
│       ├── email_sender.py        # 邮箱推送
│       ├── cleanup.py             # 存储清理
│       ├── image_fetcher.py       # 图片获取
│       ├── output_formatter.py    # 输出格式化
│       ├── sensitivity_checker.py # 敏感度检查
│       └── translator.py          # 标题翻译
├── .github/
│   └── workflows/
│       └── newspush.yml           # GitHub Actions 工作流
├── main.py                        # 命令行入口
├── config.py                      # 配置文件
├── requirements.txt               # Python 依赖
├── .env.example                   # 环境变量示例
└── README.md                      # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd newspush

# 创建虚拟环境
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# AI API Keys（阿里云百炼）
DASHSCOPE_API_KEY=your_dashscope_api_key

# AI 联网搜索（推荐开启）
ENABLE_SEARCH=true

# 新闻数量控制
MAX_NEWS_PER_SOURCE=5
MAX_NEWS_TO_ANALYZE=10

# 邮箱推送配置（以 Gmail 为例）
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_TO=recipient@example.com

# 存储清理（发送邮件后自动清理）
CLEANUP_AFTER_SEND=true
```

**注意**：Gmail 需要使用应用专用密码，不是登录密码。

### 3. 本地运行测试

```bash
# 执行一次完整流程（抓取 → 分析 → 生成 → 发送邮件 → 清理）
python main.py --once

# 分析 5 条新闻
python main.py --once --analyze 5

# 快速测试：分析 2 条
python main.py --once --analyze 2

# 仅抓取新闻（不保存）
python main.py --fetch-only

# 仅发送邮件（发送已有结果）
python main.py --send-email

# 仅清理存储
python main.py --cleanup

# 不发送邮件，不清理存储（调试用）
python main.py --once --no-email --no-cleanup
```

## GitHub Actions 部署

### 1. 配置 Secrets

在 GitHub 仓库的 **Settings → Secrets and variables → Actions** 中添加以下 secrets：

| Secret 名称 | 说明 |
|------------|------|
| `DASHSCOPE_API_KEY` | 阿里云百炼 API Key |
| `SMTP_SERVER` | SMTP 服务器（如 smtp.gmail.com） |
| `SMTP_PORT` | SMTP 端口（如 587） |
| `SMTP_USER` | 发件人邮箱地址 |
| `SMTP_PASSWORD` | SMTP 应用专用密码 |
| `EMAIL_TO` | 收件人邮箱地址 |

### 2. 运行时间

工作流默认每天运行 4 次（UTC 时间）：
- 00:00
- 06:00
- 12:00
- 18:00

如需修改，编辑 `.github/workflows/newspush.yml` 中的 cron 表达式：

```yaml
on:
  schedule:
    - cron: '0 0,6,12,18 * * *'  # 每天 0,6,12,18 点运行
```

### 3. 手动触发

可以在 GitHub 仓库的 **Actions → NewsPush Daily → Run workflow** 中手动触发，支持参数：
- **max_analyze**: 最多分析多少条新闻（默认 5）
- **no_cleanup**: 不清理存储（调试用）

## 存储策略

### 零本地存储设计

1. **原始新闻**: 抓取后只在内存中处理，**不保存到本地**
2. **分析结果**: 临时保存到 `results/` 目录，用于生成邮件附件
3. **自动清理**: 
   - 程序运行结束后自动清理 `results/` 和 `data/` 目录
   - GitHub Actions 工作流最后强制清理所有生成文件

### 文件说明

- `results/commentary_*.md` - 生成的 Markdown 文章
- `results/commentary_*.docx` - 生成的 Word 文档
- `data/news.json` - 原始新闻数据（**不再保存**）

## RSS 新闻源

默认配置的国际新闻源：

```python
RSS_SOURCES = [
    "https://news.google.com/rss",
    "https://www.reuters.com/rssFeed/worldNews",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
]
```

如需修改，编辑 `config.py` 中的 `RSS_SOURCES` 列表。

## AI 配置

### 阿里云百炼（推荐）

```env
DASHSCOPE_API_KEY=sk-your-key
ENABLE_SEARCH=true  # 开启联网搜索
```

**优势**：
- 支持联网搜索，获取最新信息
- 中文效果好
- 价格相对便宜

### 联网搜索功能

开启后，AI 在分析新闻时会自动搜索最新信息，避免因知识库过时导致的分析错误。

## 图片获取

系统使用分层策略获取新闻配图：

1. **newspaper3k** - 抓取文章中的所有图片（最多5张）
2. **OG 图** - 从网页 meta 标签提取
3. **Wikipedia** - 人物/地点图片
4. **Pexels** - 关键词搜索兜底

## 故障排除

### 新闻抓取失败
- 检查网络连接
- 验证 RSS URL 是否可用
- 某些源可能需要代理

### AI 分析失败
- 检查 API Key 是否有效
- 确认 API 额度是否充足
- 检查网络连接

### 邮件发送失败
- 确认 SMTP 配置正确
- Gmail 需要使用应用专用密码
- 检查邮箱是否开启 SMTP 访问

### GitHub Actions 运行失败
- 检查 Secrets 是否配置正确
- 查看 Actions 日志排查错误
- 确认 API Key 额度充足

## 注意事项

1. **API 限制**: 注意各 API 的调用频率和额度限制
2. **内容版权**: 抓取的新闻内容仅供学习研究，请注意版权
3. **存储限制**: GitHub Actions 免费版有存储限制，系统已设计为零存储模式
4. **邮件频率**: 注意邮件发送频率，避免被标记为垃圾邮件

## 许可证

MIT License

## 更新日志

### v2.0.0
- **移除 Web 界面** - 专注命令行和 GitHub Actions
- **新增邮箱推送** - 自动发送文章到邮箱
- **新增零存储模式** - 原始新闻不保存，推送后自动清理
- **新增 newspaper3k 图片抓取** - 自动抓取新闻中的所有图片
- **优化 GitHub Actions 工作流** - 完全自动化运行

### v1.3.0
- 新增 AI 联网搜索功能
- 移除视频脚本生成功能
- 优化新闻分析准确性

### v1.0.0
- 基础新闻抓取功能
- RSS 源支持
- 基础 AI 分析
