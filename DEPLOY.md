# NewsPush 服务器部署指南

## 1. 去重机制说明

系统已实现自动去重功能：

- **分析去重**：已分析过的新闻不会重复分析
- **数据保留**：已分析的新闻保留 7 天，之后自动清理
- **去重标识**：基于新闻链接（URL）进行去重

### 去重日志示例
```
开始深度分析新闻（deep模式）...
  将分析 3 条新闻（总共 25 条，跳过已分析 22 条）
```

## 2. 定时任务配置

### 方法一：使用自动配置脚本（推荐）

```bash
# 进入项目目录
cd /path/to/newspush

# 运行配置脚本
bash setup_cron.sh
```

按提示选择执行频率即可。

### 方法二：手动配置 crontab

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每小时执行一次）
0 * * * * cd /path/to/newspush && python3 main.py --once >> /path/to/newspush/logs/cron.log 2>&1
```

### 常用定时任务示例

| 频率 | Cron 表达式 |
|------|------------|
| 每小时 | `0 * * * *` |
| 每 2 小时 | `0 */2 * * *` |
| 每 4 小时 | `0 */4 * * *` |
| 每天 8 点 | `0 8 * * *` |
| 每天 8 点和 20 点 | `0 8,20 * * *` |

### 查看定时任务

```bash
# 查看当前用户的定时任务
crontab -l

# 查看执行日志
tail -f /path/to/newspush/logs/cron.log
```

## 3. 手动运行测试

```bash
# 进入项目目录
cd /path/to/newspush

# 运行一次完整流程
python3 main.py --once

# 运行并指定分析数量
python3 main.py --once --analyze 5

# 查看帮助
python3 main.py --help
```

## 4. 日志管理

日志文件位置：`./logs/`

- 执行日志：`newspush_YYYYMMDD_HHMMSS.log`
- 定时任务日志：`cron.log`

自动清理：保留最近 30 天的日志

## 5. 数据文件

数据文件位置：`./data/news.json`

包含字段：
- `analyzed`: 是否已分析
- `analyzed_at`: 分析时间
- `analysis_summary`: 分析摘要
- `content_type`: 内容类型

## 6. 环境要求

- Python 3.8+
- Linux 服务器（推荐 Ubuntu/CentOS）
- 稳定的网络连接（可访问阿里云 API）

## 7. 常见问题

### Q: 如何清空已分析记录？
```bash
# 删除数据文件
rm ./data/news.json
```

### Q: 如何修改去重保留时间？
编辑 `main.py`，修改 `clear_old_analyzed_news(keep_days=7)` 中的数字。

### Q: 定时任务没有执行？
1. 检查 crontab 是否正确安装：`crontab -l`
2. 检查日志文件权限：`chmod 755 logs/`
3. 检查 Python 路径是否正确

### Q: 如何临时暂停定时任务？
```bash
# 注释掉定时任务
crontab -e
# 在行首添加 # 注释
```
