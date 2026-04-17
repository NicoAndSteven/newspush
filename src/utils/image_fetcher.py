"""
智能图片获取模块
分层配图策略：newspaper3k > OG图 > Wikipedia > Pexels
支持图片代理，解决国内访问外网图片问题
"""
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Optional, Dict
import os
import requests

# newspaper3k 导入
try:
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False
    print("[ImageFetcher] newspaper3k 未安装，跳过")

class ImageFetcher:
    """智能图片获取器"""
    
    # 图片代理服务配置
    IMAGE_PROXY_URL = "https://wsrv.nl/?url="
    
    def __init__(self):
        self.pexels_api_key = os.getenv("PEXELS_API_KEY", "")
        self.pixabay_api_key = os.getenv("PIXABAY_API_KEY", "")
        # 是否启用图片代理
        self.enable_image_proxy = os.getenv("ENABLE_IMAGE_PROXY", "true").lower() == "true"
    
    def _proxy_image_url(self, img_url: str) -> str:
        """
        将外网图片 URL 转换为代理 URL
        
        Args:
            img_url: 原始图片 URL
            
        Returns:
            str: 代理后的图片 URL
        """
        if not self.enable_image_proxy:
            return img_url
        
        # 如果已经是代理 URL，直接返回
        if img_url.startswith(self.IMAGE_PROXY_URL):
            return img_url
        
        # 如果已经是国内可访问的 URL，直接返回
        if any(domain in img_url.lower() for domain in [
            'pexels.com', 'pixabay.com', 'aliyun', 'alicdn.com',
            'wechat', 'qq.com', 'baidu.com', 'zhihu.com'
        ]):
            return img_url
        
        # 使用代理服务
        # 移除协议头，因为 weserv 会自动处理
        clean_url = img_url.replace('https://', '').replace('http://', '')
        proxied_url = f"{self.IMAGE_PROXY_URL}{clean_url}"
        
        return proxied_url
    
    async def get_article_images(self, news_item: dict, analysis: dict = None) -> List[str]:
        """
        获取文章配图（分层策略）
        
        优先级：
        1. RSS 提供的图片（通过代理）- 最优先
        2. newspaper3k 抓取的所有图片（通过代理转换）
        3. OG 图（原文配图，通过代理转换）
        4. Wikipedia 图片（人物/地点）
        5. Pexels 关键词搜索（兜底）
        
        Returns:
            List[str]: 图片URL列表（最多5张）
        """
        images = []
        url = news_item.get("url", "")
        
        # 第一优先级：RSS 提供的图片（通过代理转换）
        rss_images = news_item.get("images", [])
        if rss_images:
            for img_url in rss_images:
                if img_url and self._is_valid_image_url(img_url):
                    proxied_img = self._proxy_image_url(img_url)
                    if proxied_img not in images:
                        images.append(proxied_img)
            if images:
                print(f"    [图片] RSS 提供 {len(images)} 张图片（已代理）")
        
        # 第二优先级：newspaper3k 抓取所有图片
        if url and NEWSPAPER_AVAILABLE and len(images) < 2:
            np_images = await self.extract_newspaper_images(url)
            if np_images:
                for img_url in np_images:
                    proxied_img = self._proxy_image_url(img_url)
                    if proxied_img not in images:
                        images.append(proxied_img)
                        if len(images) >= 3:
                            break
                print(f"    [图片] newspaper3k 找到 {len(np_images)} 张图片（已代理）")
        
        # 第三优先级：从原文抓 OG 图
        if url and len(images) < 2:
            og_image = await self.extract_og_image(url)
            if og_image:
                proxied_og = self._proxy_image_url(og_image)
                if proxied_og not in images:
                    images.append(proxied_og)
                    print(f"    [图片] 找到 OG 图（已代理）")
        
        # 第四优先级：Wikipedia 人物/地点图
        if analysis and len(images) < 3:
            entities = self._extract_entities(analysis)
            for entity in entities[:2]:
                if len(images) >= 3:
                    break
                wiki_img = await self.get_wikipedia_image(entity)
                if wiki_img:
                    proxied_wiki = self._proxy_image_url(wiki_img)
                    if proxied_wiki not in images:
                        images.append(proxied_wiki)
                        print(f"    [图片] 找到 Wikipedia 图: {entity}")
        
        # 兜底：Pexels 关键词搜索
        if len(images) < 1:
            tags = analysis.get("tags", []) if analysis else []
            if not tags and news_item.get("title"):
                tags = news_item["title"].split()[:3]
            if tags:
                pexels_imgs = await self.search_pexels(tags[:3])
                for img in pexels_imgs:
                    if img not in images:
                        images.append(img)
                        if len(images) >= 2:
                            break
                if pexels_imgs:
                    print(f"    [图片] 找到 Pexels 图")
        
        return images[:5]
    
    async def extract_newspaper_images(self, url: str) -> List[str]:
        """
        使用 newspaper3k 抓取文章所有图片
        
        Args:
            url: 新闻原文链接（可以是 RSS 中转源）
        
        Returns:
            List[str]: 图片URL列表
        """
        if not NEWSPAPER_AVAILABLE:
            return []
        
        try:
            loop = asyncio.get_event_loop()
            article = Article(url, language='en')
            
            def parse_article():
                try:
                    article.download()
                    article.parse()
                    return article.images
                except Exception as e:
                    print(f"    [newspaper3k] 解析失败: {e}")
                    return set()
            
            images = await loop.run_in_executor(None, parse_article)
            
            valid_images = []
            for img_url in images:
                if self._is_valid_image_url(img_url):
                    valid_images.append(img_url)
            
            return valid_images[:5]
            
        except Exception as e:
            print(f"    [newspaper3k] 获取图片失败: {e}")
            return []
    
    def _is_valid_image_url(self, url: str) -> bool:
        """检查图片URL是否有效"""
        if not url:
            return False
        
        invalid_patterns = [
            'icon', 'logo', 'avatar', 'button', 'banner',
            'ad.', 'ads.', 'advertisement', 'tracking',
            'pixel', 'beacon', 'spacer',
            'facebook.com/tr', 'google-analytics',
            'doubleclick', 'googlesyndication'
        ]
        
        url_lower = url.lower()
        for pattern in invalid_patterns:
            if pattern in url_lower:
                return False
        
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        has_valid_ext = any(url_lower.endswith(ext) for ext in valid_extensions)
        has_img_path = '/image' in url_lower or '/img' in url_lower or 'cdn' in url_lower
        
        return has_valid_ext or has_img_path
    
    async def extract_og_image(self, url: str) -> Optional[str]:
        """从网页提取 OG 图"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status != 200:
                        return None
                    
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")
                    
                    og = soup.find("meta", property="og:image")
                    if og and og.get("content"):
                        return og["content"]
                    
                    twitter = soup.find("meta", attrs={"name": "twitter:image"})
                    if twitter and twitter.get("content"):
                        return twitter["content"]
                    
                    img = soup.find("img")
                    if img and img.get("src"):
                        src = img["src"]
                        if src.startswith("http"):
                            return src
                        
        except Exception as e:
            print(f"    [OG图提取失败] {e}")
        
        return None
    
    async def get_wikipedia_image(self, entity: str) -> Optional[str]:
        """从 Wikipedia 获取人物/地点图片"""
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{entity}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        thumbnail = data.get("thumbnail", {})
                        if thumbnail.get("source"):
                            return thumbnail["source"]
        
        except Exception as e:
            print(f"    [Wikipedia图获取失败] {entity}: {e}")
        
        return None
    
    async def search_pexels(self, keywords: List[str]) -> List[str]:
        """使用 Pexels API 搜索图片"""
        if not self.pexels_api_key:
            return []
        
        try:
            query = " ".join(keywords[:2])
            
            headers = {"Authorization": self.pexels_api_key}
            params = {
                "query": query,
                "per_page": 3,
                "orientation": "landscape"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.pexels.com/v1/search",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        photos = data.get("photos", [])
                        return [p["src"]["large"] for p in photos]
        
        except Exception as e:
            print(f"    [Pexels搜索失败] {e}")
        
        return []
    
    def _extract_entities(self, analysis: dict) -> List[str]:
        """从分析结果中提取实体"""
        entities = []
        
        tags = analysis.get("tags", [])
        for tag in tags:
            if tag and tag[0].isupper():
                entities.append(tag)
        
        return entities[:3]


# 同步版本
class ImageFetcherSync:
    """同步版本的图片获取器"""
    
    IMAGE_PROXY_URL = "https://wsrv.nl/?url="
    
    def __init__(self):
        self.pexels_api_key = os.getenv("PEXELS_API_KEY", "")
        self.pixabay_api_key = os.getenv("PIXABAY_API_KEY", "")
        self.enable_image_proxy = os.getenv("ENABLE_IMAGE_PROXY", "true").lower() == "true"
    
    def _proxy_image_url(self, img_url: str) -> str:
        """将外网图片 URL 转换为代理 URL"""
        if not self.enable_image_proxy:
            return img_url
        
        if img_url.startswith(self.IMAGE_PROXY_URL):
            return img_url
        
        if any(domain in img_url.lower() for domain in [
            'pexels.com', 'pixabay.com', 'aliyun', 'alicdn.com',
            'wechat', 'qq.com', 'baidu.com', 'zhihu.com'
        ]):
            return img_url
        
        clean_url = img_url.replace('https://', '').replace('http://', '')
        return f"{self.IMAGE_PROXY_URL}{clean_url}"
    
    def get_article_images(self, news_item: dict, analysis: dict = None) -> List[str]:
        """获取文章配图（同步版本）
        
        优先级：
        1. RSS 提供的图片（通过代理）- 最优先，因为服务器可以访问
        2. newspaper3k 抓取的图片（通过代理）
        3. OG 图（通过代理）
        4. Wikipedia 图片
        5. Pexels（兜底）
        """
        images = []
        url = news_item.get("url", "")
        
        # 第一优先级：RSS 提供的图片（通过代理转换）
        rss_images = news_item.get("images", [])
        if rss_images:
            for img_url in rss_images:
                if img_url and self._is_valid_image_url(img_url):
                    proxied_img = self._proxy_image_url(img_url)
                    if proxied_img not in images:
                        images.append(proxied_img)
            if images:
                print(f"    [图片] RSS 提供 {len(images)} 张图片（已代理）")
        
        # 第二优先级：newspaper3k（如果 RSS 图片不足）
        if url and NEWSPAPER_AVAILABLE and len(images) < 2:
            np_images = self.extract_newspaper_images(url)
            if np_images:
                for img_url in np_images:
                    proxied_img = self._proxy_image_url(img_url)
                    if proxied_img not in images:
                        images.append(proxied_img)
                        if len(images) >= 3:
                            break
                print(f"    [图片] newspaper3k 找到 {len(np_images)} 张图片（已代理）")
        
        # 第三优先级：OG 图（如果图片不足）
        if url and len(images) < 2:
            og_image = self.extract_og_image(url)
            if og_image:
                proxied_og = self._proxy_image_url(og_image)
                if proxied_og not in images:
                    images.append(proxied_og)
                    print(f"    [图片] 找到 OG 图（已代理）")
        
        # 第四优先级：Wikipedia
        if analysis and len(images) < 3:
            entities = self._extract_entities(analysis)
            for entity in entities[:2]:
                if len(images) >= 3:
                    break
                wiki_img = self.get_wikipedia_image(entity)
                if wiki_img:
                    proxied_wiki = self._proxy_image_url(wiki_img)
                    if proxied_wiki not in images:
                        images.append(proxied_wiki)
                        print(f"    [图片] 找到 Wikipedia 图: {entity}")
        
        # 兜底：Pexels
        if len(images) < 1:
            tags = analysis.get("tags", []) if analysis else []
            if not tags and news_item.get("title"):
                tags = news_item["title"].split()[:3]
            if tags:
                pexels_imgs = self.search_pexels(tags[:3])
                for img in pexels_imgs:
                    if img not in images:
                        images.append(img)
                        if len(images) >= 2:
                            break
                if pexels_imgs:
                    print(f"    [图片] 找到 Pexels 图")
        
        return images[:5]
    
    def extract_newspaper_images(self, url: str) -> List[str]:
        """使用 newspaper3k 抓取文章所有图片（同步版本）"""
        if not NEWSPAPER_AVAILABLE:
            return []
        
        try:
            article = Article(url, language='en')
            article.download()
            article.parse()
            
            valid_images = []
            for img_url in article.images:
                if self._is_valid_image_url(img_url):
                    valid_images.append(img_url)
            
            return valid_images[:5]
            
        except Exception as e:
            print(f"    [newspaper3k] 获取图片失败: {e}")
            return []
    
    def _is_valid_image_url(self, url: str) -> bool:
        """检查图片URL是否有效"""
        if not url:
            return False
        
        invalid_patterns = [
            'icon', 'logo', 'avatar', 'button', 'banner',
            'ad.', 'ads.', 'advertisement', 'tracking',
            'pixel', 'beacon', 'spacer',
            'facebook.com/tr', 'google-analytics',
            'doubleclick', 'googlesyndication'
        ]
        
        url_lower = url.lower()
        for pattern in invalid_patterns:
            if pattern in url_lower:
                return False
        
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        has_valid_ext = any(url_lower.endswith(ext) for ext in valid_extensions)
        has_img_path = '/image' in url_lower or '/img' in url_lower or 'cdn' in url_lower
        
        return has_valid_ext or has_img_path
    
    def extract_og_image(self, url: str) -> Optional[str]:
        """提取 OG 图（同步版本）"""
        try:
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            og = soup.find("meta", property="og:image")
            if og and og.get("content"):
                return og["content"]
            
            twitter = soup.find("meta", attrs={"name": "twitter:image"})
            if twitter and twitter.get("content"):
                return twitter["content"]
            
        except Exception as e:
            print(f"    [OG图提取失败] {e}")
        
        return None
    
    def get_wikipedia_image(self, entity: str) -> Optional[str]:
        """获取 Wikipedia 图片（同步版本）"""
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{entity}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                thumbnail = data.get("thumbnail", {})
                if thumbnail.get("source"):
                    return thumbnail["source"]
        
        except Exception as e:
            print(f"    [Wikipedia图获取失败] {entity}: {e}")
        
        return None
    
    def search_pexels(self, keywords: List[str]) -> List[str]:
        """Pexels 搜索（同步版本）"""
        if not self.pexels_api_key:
            return []
        
        try:
            query = " ".join(keywords[:2])
            
            headers = {"Authorization": self.pexels_api_key}
            params = {
                "query": query,
                "per_page": 3,
                "orientation": "landscape"
            }
            
            response = requests.get(
                "https://api.pexels.com/v1/search",
                headers=headers,
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                photos = data.get("photos", [])
                return [p["src"]["large"] for p in photos]
        
        except Exception as e:
            print(f"    [Pexels搜索失败] {e}")
        
        return []
    
    def _extract_entities(self, analysis: dict) -> List[str]:
        """提取实体"""
        entities = []
        tags = analysis.get("tags", [])
        for tag in tags:
            if tag and tag[0].isupper():
                entities.append(tag)
        return entities[:3]
