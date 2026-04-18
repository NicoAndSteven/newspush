"""
RSS 新闻抓取器 - 使用 JSON 存储
"""
import feedparser
import requests
import json
import re
import socket
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import sys
from html import unescape
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from storage.json_storage import JSONStorage


def light_clean_description(text: str) -> str:
    """
    轻度清理 RSS description
    只处理最常见的问题，保持内容完整性
    """
    if not text:
        return ""
    
    # 解码 HTML 实体
    text = unescape(text)
    
    # 移除 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    
    # 移除常见的 RSS 噪音前缀
    noise_prefixes = [
        r'^Continue reading.*$',
        r'^Read more.*$',
        r'^Click here.*$',
        r'^Learn more.*$',
    ]
    for pattern in noise_prefixes:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
    
    # 清理多余空白
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    return text.strip()


def calculate_content_quality(text: str) -> dict:
    """
    计算内容质量指标
    
    Returns:
        {
            'avg_line_length': 平均行长,
            'short_line_ratio': 短行比例 (<20字符),
            'total_lines': 总行数,
            'quality_score': 质量分数 (0-10)
        }
    """
    if not text:
        return {'avg_line_length': 0, 'short_line_ratio': 1.0, 'total_lines': 0, 'quality_score': 0}
    
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines:
        return {'avg_line_length': 0, 'short_line_ratio': 1.0, 'total_lines': 0, 'quality_score': 0}
    
    total_lines = len(lines)
    short_lines = len([l for l in lines if len(l) < 20])
    short_line_ratio = short_lines / total_lines if total_lines > 0 else 1.0
    avg_line_length = sum(len(l) for l in lines) / total_lines if total_lines > 0 else 0
    
    # 质量评分：短行比例越低越好，平均行长适中为好
    if short_line_ratio > 0.3:
        quality_score = 3  # 质量差
    elif short_line_ratio > 0.2:
        quality_score = 6  # 质量一般
    else:
        quality_score = 9  # 质量好
    
    return {
        'avg_line_length': round(avg_line_length, 1),
        'short_line_ratio': round(short_line_ratio, 2),
        'total_lines': total_lines,
        'quality_score': quality_score
    }


def fetch_full_content_sync(url: str, timeout: int = 10) -> str:
    """同步获取完整内容（带超时）"""
    try:
        import requests
        from bs4 import BeautifulSoup
        
        response = requests.get(url, timeout=timeout, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 移除不需要的元素（包括社交媒体按钮、分享按钮等）
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 
                         'button', 'svg', 'iframe', 'form', 'input', 
                         '[class*="share"]', '[class*="social"]', '[class*="button"]',
                         '[class*="toolbar"]', '[class*="menu"]', '[class*="nav"]']):
            tag.decompose()
        
        # 尝试提取正文
        content = None
        
        # 1. 尝试 article 标签
        article = soup.find('article')
        if article:
            content = article.get_text(separator='\n', strip=True)
        
        # 2. 尝试常见选择器
        if not content:
            selectors = [
                'div[data-component="text-block"]',  # BBC
                'div.content__body',  # The Guardian
                'div.article-body',
                'div.post-content',
                'div.entry-content',
                'main',
                '[class*="article-body"]',
                '[class*="story-body"]',
            ]
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(separator='\n', strip=True)
                    if len(text) > 200:
                        content = text
                        break
        
        # 3. 使用段落密度
        if not content:
            paragraphs = []
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if len(text) > 50:
                    paragraphs.append(text)
            if paragraphs:
                content = '\n\n'.join(paragraphs)
        
        if content:
            # 清理内容
            content = clean_article_content(content)
            return content
        
        return ""
        
    except Exception as e:
        print(f"[ContentFetch] Error: {e}")
        return ""


def clean_article_content(content: str) -> str:
    """清理文章内容"""
    if not content:
        return ""
    
    # 移除常见的无用文本（社交媒体、分享按钮、作者信息等）
    noise_patterns = [
        r'Share\s*$',
        r'Save\s*$',
        r'Add as preferred on Google\s*$',
        r'Getty Images?\s*$',
        r'Reuters?\s*$',
        r'AP Photo\s*$',
        r'EPA\s*$',
        r'Image source,\s*\S+\s*$',
        r'Image caption,\s*\S+\s*$',
        r'\d+\s*(minutes?|hours?|days?|weeks?)\s*ago\s*$',
        r'Published\s*:?\s*\d+.*$',
        r'Updated\s*:?\s*\d+.*$',
        r'Follow\s+us\s+on.*$',
        r'More\s+on\s+this\s+story.*$',
        r'Related\s+topics.*$',
        r'Related\s+articles?.*$',
        r'See\s+also.*$',
        r'Watch\s+.*$',
        r'Listen\s+.*$',
        r'Read\s+more.*$',
        r'Full\s+story.*$',
        r'Continue\s+reading.*$',
        r'Show\s+more.*$',
        r'Expand.*$',
        r'Collapse.*$',
        # 作者信息模式
        r'By\s+[A-Z][a-z]+\s+[A-Z][a-z]+.*$',  # By John Smith
        r'[A-Z][a-z]+\s+[A-Z][a-z]+\s+&\s+[A-Z][a-z]+\s+[A-Z][a-z]+.*$',  # John Smith & Jane Doe
        r'at\s+(the\s+)?[A-Z][a-z]+.*$',  # at the White House, at BBC
        r'[A-Z][a-z]+\s+correspondent.*$',  # BBC correspondent
        r'Reporting\s+by.*$',
        r'Writing\s+by.*$',
        r'Editing\s+by.*$',
        r'Additional\s+reporting\s+by.*$',
    ]
    
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 跳过太短的行（可能是按钮文本）
        if len(line) < 15 and not line.endswith('.'):
            continue
        
        # 跳过匹配噪声模式的行
        is_noise = False
        for pattern in noise_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                is_noise = True
                break
        
        if not is_noise:
            cleaned_lines.append(line)
    
    # 重新组合内容
    content = '\n\n'.join(cleaned_lines)
    
    # 清理多余空白
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = re.sub(r'[ \t]+', ' ', content)
    content = re.sub(r' +\n', '\n', content)
    content = re.sub(r'\n +', '\n', content)
    
    return content.strip()


# 设置全局超时
socket.setdefaulttimeout(10)


def clean_html(html_text: str) -> str:
    """清理 HTML 标签和实体"""
    if not html_text:
        return ""
    
    # 解码 HTML 实体 (&amp; -> &, &lt; -> <)
    text = unescape(html_text)
    
    # 移除 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    
    # 移除多余空白
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    # 移除特殊字符
    text = re.sub(r'\xa0', ' ', text)  # 不间断空格
    text = re.sub(r'\u200b', '', text)  # 零宽空格
    
    return text.strip()


@dataclass
class NewsItem:
    title: str
    link: str
    description: str
    published: str
    source: str
    category: str = ""
    keywords: List[str] = None
    ai_score: float = 0.0
    ai_summary: str = ""
    is_video_worthy: bool = False
    full_content: str = ""
    thumbnail: str = ""  # RSS 提供的缩略图 URL
    images: List[str] = None  # 图片列表
    
    def __post_init__(self):
        if self.images is None:
            self.images = []
        if self.keywords is None:
            self.keywords = []
    
    def to_dict(self):
        return asdict(self)
    
    def get_content_for_analysis(self) -> str:
        """获取用于分析的内容（优先使用完整内容）"""
        if self.full_content and len(self.full_content) > 100:
            return self.full_content
        return self.description


class RSSNewsFetcher:
    def __init__(self, storage: JSONStorage = None):
        self.storage = storage or JSONStorage()
    
    def fetch_rss_feed(self, url: str, category: str = "general", timeout: int = 10, max_items: int = 5, skip_analyzed: bool = True) -> Tuple[List[NewsItem], str]:
        """
        抓取 RSS 订阅源
        支持两种格式:
        1. rss2json.com API 返回的 JSON 格式
        2. 标准 RSS XML 格式
        
        Args:
            url: RSS 地址
            category: 分类
            timeout: 超时时间
            max_items: 最多抓取多少条新闻（默认5条）
            skip_analyzed: 是否跳过已分析的文章（默认True）
        
        Returns:
            (新闻列表, 状态信息)
        """
        try:
            print(f"[RSS] Fetching: {url} (max {max_items} items)")
            
            # 使用 requests 先检查是否能访问（带超时）
            try:
                response = requests.get(url, timeout=timeout, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
            except requests.exceptions.Timeout:
                print(f"[RSS] Timeout fetching {url}")
                return [], "timeout"
            except requests.exceptions.ConnectionError:
                print(f"[RSS] Connection error for {url} (可能需要VPN)")
                return [], "connection_error"
            except Exception as e:
                print(f"[RSS] Request error for {url}: {e}")
                return [], f"request_error: {e}"
            
            news_items = []
            skipped_count = 0
            
            # 判断是 rss2json.com 的 JSON 格式还是标准 RSS XML
            if 'rss2json.com' in url:
                # 解析 JSON 格式
                try:
                    data = response.json()
                    items = data.get('items', [])
                    feed_title = data.get('feed', {}).get('title', url)
                    
                    for entry in items:
                        link = entry.get('link', '')
                        
                        # 去重检查：跳过已分析的文章
                        if skip_analyzed and self.storage.is_news_analyzed(link):
                            skipped_count += 1
                            continue
                        
                        if len(news_items) >= max_items:
                            break
                        
                        title = clean_html(entry.get('title', ''))
                        description = clean_html(entry.get('description', ''))
                        
                        # 获取图片（thumbnail 或 enclosure）
                        thumbnail = entry.get('thumbnail', '')
                        enclosure = entry.get('enclosure', {})
                        images = []
                        
                        if thumbnail:
                            images.append(thumbnail)
                        elif enclosure and enclosure.get('thumbnail'):
                            images.append(enclosure['thumbnail'])
                        elif enclosure and enclosure.get('link'):
                            images.append(enclosure['link'])
                        
                        news_item = NewsItem(
                            title=title,
                            link=link,
                            description=description,
                            published=entry.get('pubDate', datetime.now().isoformat()),
                            source=feed_title,
                            category=category,
                            thumbnail=thumbnail,
                            images=images
                        )
                        news_items.append(news_item)
                        
                except json.JSONDecodeError as e:
                    print(f"[RSS] JSON parse error for {url}: {e}")
                    return [], f"json_parse_error: {e}"
            else:
                # 解析标准 RSS XML 格式
                feed = feedparser.parse(response.content)
                
                if feed.bozo and hasattr(feed, 'bozo_exception'):
                    print(f"[RSS] Parse warning for {url}: {feed.bozo_exception}")
                
                for entry in feed.entries:
                    link = entry.get('link', '')
                    
                    # 去重检查：跳过已分析的文章
                    if skip_analyzed and self.storage.is_news_analyzed(link):
                        skipped_count += 1
                        continue
                    
                    if len(news_items) >= max_items:
                        break
                    
                    title = clean_html(entry.get('title', ''))
                    description = clean_html(entry.get('summary', entry.get('description', '')))
                    
                    # 获取图片（media_thumbnail 或 enclosure）
                    thumbnail = ''
                    images = []
                    
                    # 尝试获取 media:thumbnail
                    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                        thumbnail = entry.media_thumbnail[0].get('url', '')
                        if thumbnail:
                            images.append(thumbnail)
                    
                    # 尝试获取 enclosure
                    if hasattr(entry, 'enclosures') and entry.enclosures:
                        for enc in entry.enclosures:
                            if enc.get('type', '').startswith('image/'):
                                images.append(enc.get('href', ''))
                                if not thumbnail:
                                    thumbnail = enc.get('href', '')
                                break
                    
                    news_item = NewsItem(
                        title=title,
                        link=link,
                        description=description,
                        published=entry.get('published', datetime.now().isoformat()),
                        source=feed.feed.get('title', url),
                        category=category,
                        thumbnail=thumbnail,
                        images=images
                    )
                    news_items.append(news_item)
            
            if skipped_count > 0:
                print(f"[RSS] Fetched {len(news_items)} items from {url} (skipped {skipped_count} already analyzed)")
            else:
                print(f"[RSS] Fetched {len(news_items)} items from {url}")
            return news_items, "success"
            
        except Exception as e:
            print(f"[RSS] Error fetching {url}: {e}")
            return [], f"error: {e}"
    
    def fetch_multiple_feeds(self, rss_sources: List[Tuple[str, str]], max_workers: int = 3, 
                            timeout: int = 10, fetch_full_content: bool = True,
                            max_items_per_source: int = 5, max_total_news: int = 20,
                            skip_analyzed: bool = True) -> Dict:
        """
        并发抓取多个 RSS 源
        
        Args:
            rss_sources: [(url, category), ...]
            max_workers: 并发数（默认3）
            timeout: 每个源的超时时间
            fetch_full_content: 是否抓取完整内容
            max_items_per_source: 每个源最多抓取多少条（默认5）
            max_total_news: 总共最多抓取多少条（默认20）
            skip_analyzed: 是否跳过已分析的文章（默认True）
            
        Returns:
            {
                "total": 总源数,
                "success": 成功数,
                "failed": 失败数,
                "timeout": 超时数,
                "news_count": 新闻总数,
                "details": [(url, status, count), ...]
            }
        """
        results = {
            "total": len(rss_sources),
            "success": 0,
            "failed": 0,
            "timeout": 0,
            "connection_error": 0,
            "news_count": 0,
            "details": [],
            "all_news": []
        }
        
        print(f"[RSS] Starting to fetch {len(rss_sources)} feeds with {max_workers} workers...")
        print(f"[RSS] Max {max_items_per_source} items per source, max {max_total_news} total")
        if skip_analyzed:
            print(f"[RSS] Will skip already analyzed articles")
        if fetch_full_content:
            print(f"[RSS] Will also fetch full content for each article")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_url = {
                executor.submit(self.fetch_rss_feed, url, category, timeout, max_items_per_source, skip_analyzed): (url, category)
                for url, category in rss_sources
            }
            
            # 收集结果
            for future in as_completed(future_to_url):
                url, category = future_to_url[future]
                try:
                    news_items, status = future.result()
                    count = len(news_items)
                    
                    results["details"].append({
                        "url": url,
                        "category": category,
                        "status": status,
                        "count": count
                    })
                    
                    if status == "success":
                        results["success"] += 1
                        results["news_count"] += count
                        
                        # 智能内容选择策略
                        for item in news_items:
                            # 1. 轻度清理 description
                            cleaned_desc = light_clean_description(item.description)
                            
                            # 2. 评估 description 质量
                            desc_quality = calculate_content_quality(cleaned_desc)
                            
                            # 3. 如果 description 质量足够好，直接使用
                            if desc_quality['quality_score'] >= 7 and len(cleaned_desc) > 200:
                                item.full_content = cleaned_desc
                                item.description = cleaned_desc
                                print(f"[RSS] Using high-quality description ({len(cleaned_desc)} chars, score {desc_quality['quality_score']}) for {item.title[:30]}...")
                            elif fetch_full_content:
                                # 4. 否则尝试抓取完整内容
                                try:
                                    print(f"[RSS] Description quality {desc_quality['quality_score']}, fetching full content...")
                                    full_content = fetch_full_content_sync(item.link, timeout=8)
                                    
                                    if full_content and len(full_content) > 200:
                                        # 评估完整内容质量
                                        full_quality = calculate_content_quality(full_content)
                                        
                                        # 5. 选择质量更好的内容
                                        if full_quality['quality_score'] > desc_quality['quality_score']:
                                            item.full_content = full_content
                                            print(f"[RSS] Using full content ({len(full_content)} chars, score {full_quality['quality_score']}) for {item.title[:30]}...")
                                        else:
                                            item.full_content = cleaned_desc
                                            print(f"[RSS] Using description (full content quality {full_quality['quality_score']} < desc {desc_quality['quality_score']})")
                                    else:
                                        item.full_content = cleaned_desc
                                except Exception as e:
                                    print(f"[RSS] Failed to fetch full content: {e}, using description")
                                    item.full_content = cleaned_desc
                            else:
                                # 不抓取完整内容，直接使用清理后的 description
                                item.full_content = cleaned_desc
                                item.description = cleaned_desc
                        
                        results["all_news"].extend(news_items)
                    elif status == "timeout":
                        results["timeout"] += 1
                        results["failed"] += 1
                    elif status == "connection_error":
                        results["connection_error"] += 1
                        results["failed"] += 1
                    else:
                        results["failed"] += 1
                        
                except Exception as e:
                    print(f"[RSS] Exception for {url}: {e}")
                    results["failed"] += 1
                    results["details"].append({
                        "url": url,
                        "category": category,
                        "status": f"exception: {e}",
                        "count": 0
                    })
        
        elapsed = time.time() - start_time
        print(f"[RSS] Fetch completed in {elapsed:.1f}s")
        print(f"[RSS] Summary: {results['success']}/{results['total']} success, "
              f"{results['timeout']} timeout, {results['connection_error']} connection error, "
              f"{results['news_count']} news items")
        
        return results
    
    def save_to_database(self, news_items: List[NewsItem]):
        """保存新闻到 JSON 存储"""
        news_dicts = [item.to_dict() for item in news_items]
        saved_count = self.storage.save_news(news_dicts)
        print(f"[Storage] Saved {saved_count} news items")
        return saved_count
    
    def get_recent_news(self, hours: int = 24, category: str = None) -> List[NewsItem]:
        """获取最近的新闻"""
        news_dicts = self.storage.get_recent_news(hours=hours)
        
        # 转换为 NewsItem 对象
        news_items = []
        for item in news_dicts:
            if category and item.get('category') != category:
                continue
            
            news_items.append(NewsItem(
                title=item.get('title', ''),
                link=item.get('link', ''),
                description=item.get('description', ''),
                full_content=item.get('full_content', ''),
                published=item.get('published', ''),
                source=item.get('source', ''),
                category=item.get('category', ''),
                keywords=item.get('keywords', []),
                ai_score=item.get('ai_score', 0.0),
                ai_summary=item.get('ai_summary', ''),
                is_video_worthy=item.get('is_video_worthy', False)
            ))
        
        return news_items
    
    def update_full_content(self, link: str, full_content: str):
        """更新新闻完整内容"""
        self.storage.update_news_content(link, full_content)
        print(f"[Storage] Updated full content for: {link[:50]}...")


if __name__ == "__main__":
    fetcher = RSSNewsFetcher()
    
    # 测试抓取
    rss_feeds = [
        ("https://feeds.bbci.co.uk/news/world/rss.xml", "international"),
        ("https://www.theguardian.com/world/rss", "international"),
    ]
    
    results = fetcher.fetch_multiple_feeds(rss_feeds, max_workers=3, timeout=10)
    print(f"\nResults: {results}")
