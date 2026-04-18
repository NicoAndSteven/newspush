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
        # ============== 原有源（国际新闻） ==============
        ("https://api.rss2json.com/v1/api.json?rss_url=https://feeds.bbci.co.uk/news/world/rss.xml", "world"),
        ("https://api.rss2json.com/v1/api.json?rss_url=https://feeds.bbci.co.uk/news/rss.xml", "world"),
        ("https://api.rss2json.com/v1/api.json?rss_url=https://www.theguardian.com/world/rss", "world"),
        ("https://api.rss2json.com/v1/api.json?rss_url=https://www.ft.com/world?format=rss", "finance"),
        ("https://api.rss2json.com/v1/api.json?rss_url=https://www.aljazeera.com/xml/rss/all.xml", "world"),
        
        # ============== 国内科技 ==============
        ("https://36kr.com/feed", "tech"),
        ("https://www.pingwest.com/feed/all", "tech"),
        ("https://techcrunch.com/feed/", "tech"),
        
        # ============== 国内财经 ==============
        ("https://a.jiemian.com/index.php?m=article&a=rss", "finance"),
        
        # ============== 国内体育 ==============
        ("https://www.dongqiudi.com/rss/feed", "sports"),
        
        # ============== 国内娱乐 ==============
        ("https://www.mgtv.com/rss/news/index.xml", "entertainment"),
        
        # ============== 国外体育（中转） ==============
        ("https://rsstranslator.com/rss?url=https://feeds.bbci.co.uk/sport/rss.xml", "sports"),
        ("https://rsstranslator.com/rss?url=https://feeds.bbci.co.uk/sport/nba/rss.xml", "sports"),
        ("https://rsstranslator.com/rss?url=https://feeds.bbci.co.uk/sport/football/rss.xml", "sports"),
        
        # ============== 国外财经（中转） ==============
        ("https://rsstranslator.com/rss?url=https://www.reuters.com/business/rss/", "finance"),
        ("https://rssbrain.com/feed?url=https://www.bloomberg.com/markets/rss", "finance"),
        
        # ============== 好莱坞/国际娱乐（中转） ==============
        ("https://rsstranslator.com/rss?url=https://variety.com/feed/", "entertainment"),
        ("https://rssbrain.com/feed?url=https://www.hollywoodreporter.com/feed/", "entertainment"),
        
        # ============== 韩国娱乐（中转） ==============
        ("https://rsstranslator.com/rss?url=https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=14&plink=RSSREADER", "entertainment"),
        ("https://rsstranslator.com/rss?url=http://imnews.imbc.com/rss/news/news_06.xml", "entertainment"),
        ("https://rsstranslator.com/rss?url=https://www.yonhapnewstv.co.kr/category/news/culture/feed/", "entertainment"),
        ("https://rsstranslator.com/rss?url=https://www.soompi.com/feed", "entertainment"),
        ("https://rsstranslator.com/rss?url=https://www.kpopdigest.com/feed", "entertainment"),
        ("https://rsstranslator.com/rss?url=https://www.hancinema.net/rss.xml", "entertainment"),
        ("https://rssbrain.com/feed?url=https://www.bntnews.co.kr/rss/feed", "entertainment"),
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
