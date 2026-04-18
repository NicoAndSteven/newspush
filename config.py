import os
from pathlib import Path
from dotenv import load_dotenv

# 获取当前文件所在目录
BASE_DIR = Path(__file__).parent

# 加载 .env 文件（从当前目录和父目录查找）
env_file = BASE_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file, override=True)
else:
    load_dotenv(override=True)

class Config:
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    RESULTS_DIR = BASE_DIR / "results"
    
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 从环境变量获取 API Key（支持 DASHSCOPE_API_KEY 和 OPENAI_API_KEY）
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY") or ""

    # RSS 源配置（带分类）
    # 格式: (RSS_URL, 分类名称)
    # 分类: tech, finance, sports, entertainment, world
    RSS_SOURCES = [
        # ============== 国际新闻 ==============
        ("https://api.rss2json.com/v1/api.json?rss_url=https://feeds.bbci.co.uk/news/world/rss.xml", "world"),
        ("https://api.rss2json.com/v1/api.json?rss_url=https://feeds.bbci.co.uk/news/rss.xml", "world"),
        ("https://api.rss2json.com/v1/api.json?rss_url=https://www.theguardian.com/world/rss", "world"),
        ("https://api.rss2json.com/v1/api.json?rss_url=https://www.ft.com/world?format=rss", "finance"),
        ("https://api.rss2json.com/v1/api.json?rss_url=https://www.aljazeera.com/xml/rss/all.xml", "world"),
        ("https://feeds.npr.org/1001/rss.xml", "world"),
        
        # ============== 科技新闻 ==============
        ("https://36kr.com/feed", "tech"),
        ("https://techcrunch.com/feed/", "tech"),
        ("https://www.theverge.com/rss/index.xml", "tech"),
        ("https://feeds.arstechnica.com/arstechnica/index", "tech"),
        
        # ============== 财经新闻 ==============
        ("https://a.jiemian.com/index.php?m=article&a=rss", "finance"),
        
        # ============== 体育新闻 ==============
        ("https://www.espn.com/espn/rss/news", "sports"),
        ("https://www.cbssports.com/rss/headlines/", "sports"),
        
        # ============== 娱乐新闻 ==============
        ("https://www.tmz.com/rss.xml", "entertainment"),
        ("https://www.billboard.com/feed/", "entertainment"),
    ]
    
    # 每个板块每次最多抓取的新闻数量
    MAX_NEWS_PER_CATEGORY = int(os.getenv("MAX_NEWS_PER_CATEGORY", "2"))
    
    # 兼容旧配置
    MAX_NEWS_PER_SOURCE = int(os.getenv("MAX_NEWS_PER_SOURCE", "3"))
    MAX_NEWS_TO_ANALYZE = int(os.getenv("MAX_NEWS_TO_ANALYZE", "10"))
    
    # 微信公众号推送配置
    WECHAT_APPID = os.getenv("WECHAT_APPID") or ""
    WECHAT_SECRET = os.getenv("WECHAT_SECRET") or ""
    
    CLEANUP_AFTER_SEND = os.getenv("CLEANUP_AFTER_SEND", "true").lower() == "true"
    
    # 输出文件配置（可控制生成哪些文件）
    GENERATE_MARKDOWN = os.getenv("GENERATE_MARKDOWN", "true").lower() == "true"
    GENERATE_WORD = os.getenv("GENERATE_WORD", "false").lower() == "true"
    GENERATE_INTERNAL_VERSION = os.getenv("GENERATE_INTERNAL_VERSION", "false").lower() == "true"

config = Config()
