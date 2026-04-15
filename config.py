import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    RESULTS_DIR = BASE_DIR / "results"
    
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
    
    RSS_SOURCES = [
        # 图片抓取效果好的新闻源（基于测试结果）
        "https://feeds.bbci.co.uk/news/world/rss.xml",      # BBC - 图片抓取效果好
        "https://www.theguardian.com/world/rss",             # The Guardian - 图片抓取效果好
        "https://www.aljazeera.com/xml/rss/all.xml",         # Al Jazeera - 图片抓取效果好
        "https://www.ft.com/?format=rss",                    # Financial Times - 图片抓取效果好
    ]
    
    MAX_NEWS_PER_SOURCE = int(os.getenv("MAX_NEWS_PER_SOURCE", "5"))
    MAX_NEWS_TO_ANALYZE = int(os.getenv("MAX_NEWS_TO_ANALYZE", "10"))
    
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    EMAIL_TO = os.getenv("EMAIL_TO", "")
    
    CLEANUP_AFTER_SEND = os.getenv("CLEANUP_AFTER_SEND", "true").lower() == "true"

config = Config()
