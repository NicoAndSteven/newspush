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
        "https://rss.ovh/bbc/world",  # 社区实例 - BBC
        "https://rss.ovh/guardian/world",  # Guardian
        "https://rss.ovh/aljazeera/english/news",  # Al Jazeera
        "https://rss.ovh/ft/world",  # FT

        # 备选（如果上面不行）
        "https://rsshub.rssforever.com/bbc/world",
        "https://rsshub.netlify.app/bbc/world",
]
    
    MAX_NEWS_PER_SOURCE = int(os.getenv("MAX_NEWS_PER_SOURCE", "5"))
    MAX_NEWS_TO_ANALYZE = int(os.getenv("MAX_NEWS_TO_ANALYZE", "10"))
    
    # 微信公众号推送配置
    WECHAT_APPID = os.getenv("WECHAT_APPID") or ""
    WECHAT_SECRET = os.getenv("WECHAT_SECRET") or ""
    
    CLEANUP_AFTER_SEND = os.getenv("CLEANUP_AFTER_SEND", "true").lower() == "true"

config = Config()
