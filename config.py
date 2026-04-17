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
    # BBC World News（图片抓取效果很好）
    "https://rsshub.app/bbc/world",

    # The Guardian World News（图片抓取效果很好）
    "https://rsshub.app/guardian/world",

    # Al Jazeera（半岛电视台，全英文或阿拉伯文，图片效果不错）
    "https://rsshub.app/aljazeera/english/news",

    # Financial Times（金融时报，图片抓取效果较好）
    # FT 官方 RSS 限制较多，RSSHub 提供 myFT 个人版或通用路由，这里用通用世界新闻路由
    "https://rsshub.app/ft/world",
]
    
    MAX_NEWS_PER_SOURCE = int(os.getenv("MAX_NEWS_PER_SOURCE", "5"))
    MAX_NEWS_TO_ANALYZE = int(os.getenv("MAX_NEWS_TO_ANALYZE", "10"))
    
    # 微信公众号推送配置
    WECHAT_APPID = os.getenv("WECHAT_APPID") or ""
    WECHAT_SECRET = os.getenv("WECHAT_SECRET") or ""
    
    CLEANUP_AFTER_SEND = os.getenv("CLEANUP_AFTER_SEND", "true").lower() == "true"

config = Config()
