# NewsPush - 智能新闻分析与内容生成系统

一个全自动的新闻素材捕捉、深度分析、智能点评和 Markdown 生成系统。

## 功能特性

### 核心功能
- **新闻素材捕捉**: RSS 订阅实时抓取，支持国内外多个新闻源
- **完整内容抓取**: 自动抓取新闻正文，保存为 Markdown/TXT/JSON 格式
- **深度 AI 分析**: 不限题材，自动分析新闻价值、背景、影响
- **智能点评生成**: 基于分析结果生成专业的新闻点评文章
- **Markdown 输出**: 生成结构化的 Markdown 分析报告
- **Web 管理界面**: 直观的仪表盘和操作界面
- **自动任务调度**: 定时自动抓取、分析

### 技术亮点
- **新闻流展示**: 滚动式新闻列表，点击即选
- **FastAPI 后端**: 提供完整的 REST API 接口
- **多 AI 支持**: 支持 OpenAI/Claude/DeepSeek
- **Grok 集成**: 专门支持 Grok 的新闻抓取和展示

## 项目结构

```
newspush/
├── src/
│   ├── news_capture/              # 新闻捕捉模块
│   │   ├── rss_fetcher.py         # RSS/API 抓取
│   │   ├── content_fetcher.py     # 内容抓取
│   │   └── source_evaluator.py    # 源评估
│   ├── video_downloader/          # 视频下载模块
│   │   └── ytdlp_downloader.py    # yt-dlp 封装
│   ├── ai_processor/              # AI 处理模块
│   │   ├── content_analyzer.py    # 基础分析
│   │   └── deep_analyzer.py       # 深度分析 + 点评生成
│   ├── platform_publisher/        # 多平台发布模块
│   │   ├── base.py
│   │   ├── wechat_publisher.py
│   │   ├── xiaohongshu_publisher.py
│   │   └── publisher_manager.py
│   ├── storage/                   # 存储模块
│   │   └── json_storage.py        # JSON 存储
│   ├── capcut_automation/         # CapCut 自动化
│   │   └── capcut_api.py
│   └── infrastructure/            # 基础设施
│       ├── monitoring.py
│       ├── deduplication.py
│       └── task_queue.py
├── templates/                     # Web 界面模板
│   ├── base.html
│   ├── index.html
│   ├── news.html
│   ├── news_flow.html             # 新闻流页面
│   ├── analysis.html
│   ├── publish.html
│   ├── autotask.html              # 自动任务配置
│   └── dashboard.html
├── n8n_workflows/                 # n8n 工作流配置
│   ├── news_capture_workflow.json
│   ├── video_generation_workflow.json
│   └── multi_platform_publish_workflow.json
├── markdown_output/               # Markdown 输出目录
├── data/                          # 数据存储
│   ├── news.db                    # SQLite 数据库
│   └── news.json                  # JSON 数据
├── docs/                          # 文档
│   ├── architecture_redesign.md
│   └── product_strategy.md
├── api_server.py                  # FastAPI 主服务
├── main.py                        # 命令行入口
├── generate_markdown.py           # Markdown 生成器
├── fetch_for_grok.py              # Grok 新闻抓取
├── show_top5_content.py           # 显示优质源内容
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
# AI API Keys (三选一，也可都配置)
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
DEEPSEEK_API_KEY=your_deepseek_key

# AI 联网搜索（默认开启，让AI获取最新信息进行分析）
ENABLE_SEARCH=true  # true=开启联网搜索，false=关闭

# 微信公众号（可选）
WECHAT_APP_ID=your_wechat_app_id
WECHAT_APP_SECRET=your_wechat_app_secret
WECHAT_SIMULATED=true  # true=模拟模式，false=真实发布

# 小红书（可选）
XIAOHONGSHU_COOKIE=your_xiaohongshu_cookie
```

### 3. 启动 Web 服务

```bash
python api_server.py
```

访问 http://localhost:8000 打开管理界面

### 4. 命令行方式

```bash
# 执行一次完整流程（使用配置文件的默认值）
python main.py --once

# 分析 5 条新闻，生成 5 篇点评（一对一关系）
python main.py --once --analyze 5

# 分析 10 条新闻，但只生成 3 篇点评
python main.py --once --analyze 10 --generate 3

# 快速测试：分析 2 条，生成 2 篇
python main.py --once --analyze 2

# 仅抓取新闻
python main.py --fetch-only

# 仅分析已有新闻
python main.py --deep-analyze

# 定时运行（每小时）
python main.py --schedule 1
```

**说明：**
- 分析和生成是一对一关系：分析 N 条 → 生成 N 篇
- 如果只指定 `--analyze`，则生成数量 = 分析数量
- 如果同时指定 `--analyze` 和 `--generate`，则生成数量 = `--generate`
- 紧急度仅供参考，不再作为筛选条件

## 核心功能使用

### 1. 生成 Markdown 分析报告

```bash
python generate_markdown.py
```

功能：
- 分析新闻标题和内容
- 生成 AI 深度分析（摘要、背景、影响、展望）
- 生成专家点评文章
- 输出结构化 Markdown 文件到 `markdown_output/` 目录

### 2. 抓取新闻供 Grok 分析

```bash
python fetch_for_grok.py
```

功能：
- 从多个 RSS 源抓取新闻
- 生成 `news_for_grok.txt` 文件
- 按分类整理（国际、科技、商业、科学）
- 包含标题、摘要、链接

### 3. 显示优质源内容

```bash
python show_top5_content.py
```

功能：
- 测试 5 个优质 RSS 源
- 显示标题、链接、RSS 摘要
- 抓取并显示完整文章内容

## Web 界面使用指南

### 1. 仪表盘
访问 http://localhost:8000/dashboard
- 查看系统状态（AI配置、发布器配置）
- 查看24小时新闻数量
- 查看待处理任务数

### 2. 新闻列表
访问 http://localhost:8000/news
- 查看已抓取的新闻
- 点击"抓取新闻"按钮手动抓取
- 选择时间范围筛选
- 点击"分析"跳转分析页面

### 3. 新闻流
访问 http://localhost:8000/news-flow
- 自动滚动展示最新新闻
- 可暂停/继续滚动
- 调节滚动速度
- 点击任意新闻选择
- 一键生成点评

### 4. 分析页面
访问 http://localhost:8000/analysis
- 输入新闻标题和内容
- 选择点评风格（客观/批判/乐观/鲜明）
- AI 深度分析
- 生成专业点评文章

### 5. 发布页面
访问 http://localhost:8000/publish
- 快速发布：输入新闻 → 分析 → 点评 → 发布（一键完成）
- 查看发布任务状态

### 6. 自动任务
访问 http://localhost:8000/autotask
- 配置定时任务参数
- 设置每次处理的新闻数量
- 选择点评风格
- 手动触发测试

## API 接口文档

启动服务后访问 http://localhost:8000/docs 查看完整 API 文档

### 主要接口

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | /api/news/recent | 获取最近新闻 |
| POST | /api/news/fetch | 手动抓取新闻 |
| GET | /api/news/random | 随机获取一条新闻 |
| POST | /api/news/analyze | 分析新闻 |
| POST | /api/news/commentary | 生成点评 |
| POST | /api/news/publish | 发布到多平台 |
| POST | /api/workflow/full | 完整流程（分析+点评+发布） |
| GET | /api/autotask/config | 获取自动任务配置 |
| POST | /api/autotask/config | 保存自动任务配置 |
| POST | /api/autotask/run | 手动触发自动任务 |

## AI 配置方案

### 方案一：云端 API（推荐，效果最好）

**OpenAI GPT-4**
```env
OPENAI_API_KEY=sk-your-key
```

**Anthropic Claude**
```env
ANTHROPIC_API_KEY=sk-ant-your-key
```

**DeepSeek（便宜，中文好）**
```env
DEEPSEEK_API_KEY=your-key
```

### 联网搜索功能（推荐开启）

为了解决大模型知识库时效性问题，系统支持联网搜索功能：

**功能说明：**
- 开启后，AI 在分析新闻时会自动搜索最新信息
- 避免因知识库过时导致的分析错误（如"特朗普2024大选"这类问题）
- 特别适合分析时事热点、政治、科技等快速变化的领域

**配置方式：**

在 `.env` 文件中设置：
```env
ENABLE_SEARCH=true  # 默认开启
```

**支持的 API：**
- ✅ DeepSeek - 完整支持联网搜索
- ⚠️ OpenAI - 暂不支持（使用内置知识库）
- ⚠️ Anthropic - 暂不支持（使用内置知识库）

**效果对比：**
| 功能 | 关闭联网搜索 | 开启联网搜索 |
|------|-------------|-------------|
| 知识时效性 | 依赖训练数据截止日期 | 实时获取最新信息 |
| 分析准确性 | 可能有过时信息 | 基于最新事实分析 |
| API 调用速度 | 较快 | 稍慢（需要搜索时间） |
| 成本 | 标准费用 | 可能有额外搜索费用 |

## RSS 新闻源

### 国际源
- BBC：https://feeds.bbci.co.uk/news/world/rss.xml
- The Guardian：https://www.theguardian.com/world/rss
- Reuters：http://feeds.reuters.com/reuters/worldnews
- CNN：http://rss.cnn.com/rss/edition_world.rss
- WSJ：https://feeds.a.dj.com/rss/RSSWorldNews.xml

### 科技源
- TechCrunch：https://techcrunch.com/feed/
- Ars Technica：http://feeds.arstechnica.com/arstechnica/index
- The Verge：https://www.theverge.com/rss/index.xml
- MIT Technology Review：https://www.technologyreview.com/feed/

### 科学源
- Nature News：https://www.nature.com/nature.rss

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        NewsPush System                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│   │   RSS 抓取    │─────▶│   内容提取    │─────▶│  JSON Storage│ │
│   └──────────────┘      └──────────────┘      └──────────────┘ │
│          │                                               │      │
│          ▼                                               ▼      │
│   ┌──────────────┐                              ┌──────────────┐│
│   │  Grok 抓取    │                              │   AI 分析    ││
│   │  (专用脚本)   │                              │  (DeepSeek)  ││
│   └──────────────┘                              └──────────────┘│
│          │                                               │      │
│          ▼                                               ▼      │
│   ┌──────────────┐                              ┌──────────────┐│
│   │  Markdown    │                              │  点评生成    ││
│   │  生成器      │                              │  专家点评    ││
│   └──────────────┘                              └──────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 配置说明

### 修改 RSS 新闻源

编辑 `config.py` 中的 `RSS_SOURCES` 列表：

```python
RSS_SOURCES = [
    "https://news.google.com/rss",
    "https://www.reuters.com/rssFeed/worldNews",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    # 添加你的 RSS 源
]
```

### 修改生成内容

- **Markdown 格式**：编辑 `generate_markdown.py` 中的 `_create_markdown` 方法
- **点评风格**：在分析时选择 `balanced`/`critical`/`optimistic`/`provocative`

## 故障排除

### 新闻抓取失败
- 检查网络连接
- 验证 RSS URL 是否可用
- 查看服务器日志

### AI 分析失败
- 检查 API Key 是否有效
- 确认 API 额度是否充足
- 检查网络连接

### 网页无法访问
- 确认服务器已启动
- 检查端口 8000 是否被占用
- 刷新浏览器缓存

## 注意事项

1. **API 限制**: 注意各 AI API 的调用频率和额度限制
2. **内容版权**: 抓取的新闻内容仅供学习研究，请注意版权
3. **平台规则**: 发布内容需遵守各平台社区规范
4. **数据备份**: 定期备份数据文件

## 许可证

MIT License

## 更新日志

### v1.3.0
- **新增 AI 联网搜索功能** - 解决知识库时效性问题
- **移除视频脚本生成功能** - 简化流程，专注文字分析
- **修复 RSS 抓取返回值处理 bug**
- **优化新闻分析准确性**

### v1.2.0
- 新增 Markdown 生成器
- 新增 Grok 专用新闻抓取
- 新增优质源内容展示
- 优化新闻抓取稳定性

### v1.1.0
- 新增新闻流页面（滚动展示）
- 新增自动任务系统
- 新增多平台发布（微信/小红书/微博/知乎）
- 新增深度分析和点评生成功能
- 新增完整内容抓取
- 新增 FastAPI Web 界面

### v1.0.0
- 基础新闻抓取功能
- RSS 源支持
- 基础 AI 分析
- CapCut 自动化
- n8n 工作流
