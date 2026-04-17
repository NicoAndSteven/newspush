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
    
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY") or ""

    RSS_SOURCES = [
        # BBC 世界新闻
        "https://api.rss2json.com/v1/api.json?rss_url=https://feeds.bbci.co.uk/news/world/rss.xml",
        # BBC 首页
        "https://api.rss2json.com/v1/api.json?rss_url=https://feeds.bbci.co.uk/news/rss.xml",
        # The Guardian 世界新闻
        "https://api.rss2json.com/v1/api.json?rss_url=https://www.theguardian.com/world/rss",
        # Financial Times 世界新闻
        "https://api.rss2json.com/v1/api.json?rss_url=https://www.ft.com/world?format=rss",
        # Al Jazeera
        "https://api.rss2json.com/v1/api.json?rss_url=https://www.aljazeera.com/xml/rss/all.xml",
    ]
    
    MAX_NEWS_PER_SOURCE = int(os.getenv("MAX_NEWS_PER_SOURCE", "5"))
    MAX_NEWS_TO_ANALYZE = int(os.getenv("MAX_NEWS_TO_ANALYZE", "10"))
    
    # 微信公众号推送配置
    WECHAT_APPID = os.getenv("WECHAT_APPID") or ""
    WECHAT_SECRET = os.getenv("WECHAT_SECRET") or ""
    
    CLEANUP_AFTER_SEND = os.getenv("CLEANUP_AFTER_SEND", "true").lower() == "true"

config = Config()
