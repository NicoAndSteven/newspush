"""
微信公众号草稿箱推送模块（NewsPush专用）
只支持推送长文章到公众号草稿箱，不使用 Server酱
支持文章内图片上传到微信服务器
"""

import requests
import time
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import tempfile
import os

class WeChatDraftPusher:
    """微信公众号 - 草稿箱推送"""
    
    def __init__(self):
        from config import config
        self.appid = getattr(config, 'WECHAT_APPID', None)
        self.secret = getattr(config, 'WECHAT_SECRET', None)
        self.access_token = None
        self.token_expire_time = 0
        self.uploaded_images = {}  # 缓存已上传的图片URL

    def _get_access_token(self) -> Optional[str]:
        """获取 access_token，有效期2小时"""
        if self.access_token and time.time() < self.token_expire_time:
            return self.access_token

        if not self.appid or not self.secret:
            print("❌ 未配置 WECHAT_APPID 或 WECHAT_SECRET")
            return None

        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.appid}&secret={self.secret}"
        
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            
            if "access_token" in data:
                self.access_token = data["access_token"]
                self.token_expire_time = time.time() + 7000
                print("✅ 微信 access_token 获取成功")
                return self.access_token
            else:
                print(f"❌ 获取 access_token 失败: {data.get('errmsg')}")
                return None
        except Exception as e:
            print(f"❌ 获取 access_token 异常: {e}")
            return None

    def _download_image(self, image_url: str) -> Optional[str]:
        """下载网络图片到临时文件"""
        if not image_url:
            return None
            
        if Path(image_url).exists():
            return image_url
        
        if not image_url.startswith(('http://', 'https://')):
            return None
        
        try:
            print(f"    [下载图片] {image_url[:60]}...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            response = requests.get(image_url, timeout=15, stream=True, headers=headers)
            
            if response.status_code != 200:
                print(f"    [下载失败] HTTP {response.status_code}")
                return None
            
            content_type = response.headers.get('content-type', '')
            print(f"    [下载成功] Content-Type: {content_type}, 大小: {len(response.content)} bytes")
            
            if 'image' not in content_type:
                if not any(ext in image_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    print(f"    [下载失败] 非图片类型")
                    return None
            
            suffix = '.jpg'
            if '.png' in image_url.lower():
                suffix = '.png'
            elif '.gif' in image_url.lower():
                suffix = '.gif'
            elif '.webp' in image_url.lower():
                suffix = '.webp'
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            print(f"    [保存成功] {tmp_path}")
            return tmp_path
            
        except Exception as e:
            print(f"    [下载异常] {type(e).__name__}: {e}")
            return None

    def upload_cover_image(self, image_path: str) -> Optional[str]:
        """上传封面图片，返回 thumb_media_id"""
        print(f"    [封面图] 开始处理: {image_path[:60] if image_path else 'None'}...")
        
        token = self._get_access_token()
        if not token:
            print(f"    [封面图] 获取 token 失败")
            return None

        temp_file = None
        actual_path = image_path
        
        if image_path and image_path.startswith(('http://', 'https://')):
            print(f"    [封面图] 检测到网络图片，开始下载...")
            temp_file = self._download_image(image_path)
            if temp_file:
                actual_path = temp_file
                print(f"    [封面图] 下载成功: {temp_file}")
            else:
                print(f"    [封面图] 下载失败")
                return None
        elif image_path and not Path(image_path).exists():
            print(f"    [封面图] 本地文件不存在: {image_path}")
            return None

        if not actual_path:
            print(f"    [封面图] 无有效图片路径")
            return None

        url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"

        try:
            with open(actual_path, 'rb') as f:
                files = {'media': (Path(actual_path).name, f, 'image/jpeg')}
                resp = requests.post(url, files=files, timeout=30)
            
            result = resp.json()
            print(f"    [封面图] 上传响应: {result}")
            
            if 'media_id' in result:
                print(f"✅ 封面图上传成功")
                return result['media_id']
            else:
                print(f"❌ 封面图上传失败: {result}")
                return None
        except Exception as e:
            print(f"❌ 上传封面图异常: {e}")
            return None
        finally:
            if temp_file and Path(temp_file).exists():
                try:
                    os.unlink(temp_file)
                except:
                    pass

    def upload_content_image(self, image_url: str) -> Optional[str]:
        """
        上传文章内容中的图片到微信服务器
        返回微信图片URL（可用于文章内容中）
        """
        # 检查缓存
        if image_url in self.uploaded_images:
            return self.uploaded_images[image_url]
        
        token = self._get_access_token()
        if not token:
            return None
        
        # 下载图片
        temp_file = self._download_image(image_url)
        if not temp_file:
            return None
        
        try:
            # 使用图文消息内图片上传接口
            url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"
            
            with open(temp_file, 'rb') as f:
                files = {'media': (Path(temp_file).name, f, 'image/jpeg')}
                resp = requests.post(url, files=files, timeout=30)
            
            result = resp.json()
            
            if 'url' in result:
                wechat_url = result['url']
                self.uploaded_images[image_url] = wechat_url
                print(f"    ✅ 内容图上传成功")
                return wechat_url
            else:
                print(f"    ❌ 内容图上传失败: {result}")
                return None
                
        except Exception as e:
            print(f"    ❌ 上传内容图异常: {e}")
            return None
        finally:
            if Path(temp_file).exists():
                try:
                    os.unlink(temp_file)
                except:
                    pass

    def process_content_images(self, content: str, images: List[str] = None) -> str:
        """
        处理文章内容中的图片
        将外部图片URL替换为微信图片URL
        
        Args:
            content: 文章内容（HTML或Markdown）
            images: 图片URL列表
            
        Returns:
            处理后的内容
        """
        if not images:
            # 从内容中提取图片URL
            img_pattern = r'!\[.*?\]\((https?://[^\)]+)\)'
            matches = re.findall(img_pattern, content)
            images = matches
        
        if not images:
            return content
        
        print(f"    处理 {len(images)} 张内容图片...")
        
        for i, img_url in enumerate(images[:5]):  # 最多处理5张
            if not img_url.startswith(('http://', 'https://')):
                continue
            
            # 上传图片到微信
            wechat_url = self.upload_content_image(img_url)
            
            if wechat_url:
                # 替换Markdown图片链接
                content = content.replace(img_url, wechat_url)
                print(f"    [{i+1}/{len(images)}] 图片已上传并替换")
            else:
                print(f"    [{i+1}/{len(images)}] 图片上传失败，保留原链接")
        
        return content

    def markdown_to_wechat_html(self, markdown_text: str, images: List[str] = None) -> str:
        """
        Markdown 转微信 HTML（美化版）
        支持图片上传和嵌入，添加微信适配样式
        """
        if not markdown_text:
            return "<p>暂无内容</p>"

        # 先处理图片（上传到微信）
        processed_text = self.process_content_images(markdown_text, images)
        
        # 转换Markdown图片为HTML img标签（带样式）
        img_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
        processed_text = re.sub(
            img_pattern, 
            r'<img src="\2" style="max-width:100%;display:block;margin:20px auto;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);" alt="\1"/>', 
            processed_text
        )
        
        # 转换标题（## 和 ###）
        processed_text = re.sub(
            r'^### (.+)$',
            r'<h3 style="font-size:18px;font-weight:bold;color:#333;margin:25px 0 15px 0;padding-left:12px;border-left:4px solid #07c160;">\1</h3>',
            processed_text,
            flags=re.MULTILINE
        )
        processed_text = re.sub(
            r'^## (.+)$',
            r'<h2 style="font-size:20px;font-weight:bold;color:#333;margin:30px 0 18px 0;padding-left:12px;border-left:4px solid #07c160;">\1</h2>',
            processed_text,
            flags=re.MULTILINE
        )
        
        # 转换粗体
        processed_text = re.sub(
            r'\*\*([^\*]+)\*\*',
            r'<strong style="color:#333;font-weight:600;">\1</strong>',
            processed_text
        )
        
        # 转换引用块
        processed_text = re.sub(
            r'^> (.+)$',
            r'<blockquote style="margin:20px 0;padding:15px 20px;background:#f8f9fa;border-left:4px solid #07c160;color:#666;font-style:italic;">\1</blockquote>',
            processed_text,
            flags=re.MULTILINE
        )
        
        # 转换列表
        processed_text = re.sub(
            r'^- (.+)$',
            r'<li style="margin:8px 0;padding-left:5px;color:#333;">\1</li>',
            processed_text,
            flags=re.MULTILINE
        )
        
        # 包裹连续的列表项
        processed_text = re.sub(
            r'(<li[^>]*>.*?</li>\n?)+',
            lambda m: f'<ul style="margin:15px 0;padding-left:25px;list-style-type:disc;">{m.group(0)}</ul>',
            processed_text
        )
        
        # 转换分隔线
        processed_text = re.sub(
            r'^---$',
            r'<hr style="margin:30px 0;border:none;border-top:1px solid #eee;"/>',
            processed_text,
            flags=re.MULTILINE
        )
        
        # 转换段落（双换行）
        paragraphs = processed_text.split('\n\n')
        formatted_paragraphs = []
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            # 如果已经是HTML标签开头，不包裹p标签
            if p.startswith(('<h2', '<h3', '<ul', '<blockquote', '<hr', '<img')):
                formatted_paragraphs.append(p)
            else:
                # 单换行转<br>
                p = p.replace('\n', '<br/>')
                formatted_paragraphs.append(f'<p style="margin:15px 0;line-height:1.8;text-align:justify;color:#333;">{p}</p>')
        
        content = '\n'.join(formatted_paragraphs)
        
        # 微信文章整体样式
        return f'''
<section style="font-size:16px;line-height:1.8;color:#333;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;padding:20px 15px;max-width:100%;word-wrap:break-word;">
    {content}
</section>
<section style="margin-top:30px;padding-top:20px;border-top:1px solid #eee;text-align:center;color:#999;font-size:12px;">
    <p>本文由 NewsPush 自动生成</p>
</section>
        '''

    def push_to_draft(self, title: str, markdown_content: str, cover_image_path: str = None, content_images: List[str] = None) -> bool:
        """
        主函数：把一篇文章推送到微信公众号草稿箱
        
        Args:
            title: 文章标题
            markdown_content: Markdown 格式内容
            cover_image_path: 封面图路径（本地路径或网络URL）
            content_images: 文章内容中的图片URL列表
        """
        if not self.appid or not self.secret:
            print("❌ 请先在 .env 中配置 WECHAT_APPID 和 WECHAT_SECRET")
            return False

        # 1. 处理封面图
        thumb_media_id = None
        if cover_image_path:
            thumb_media_id = self.upload_cover_image(cover_image_path)
        
        if not thumb_media_id:
            print("⚠️  未找到有效封面图，将尝试无封面推送（可能失败）")

        # 2. 转换内容为微信 HTML（包含图片上传）
        content_html = self.markdown_to_wechat_html(markdown_content, content_images)

        # 3. 推送到草稿箱
        token = self._get_access_token()
        if not token:
            return False

        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"

        article = {
            "articles": [{
                "title": title,
                "author": "NewsPush",
                "digest": title[:80] + "..." if len(title) > 80 else title,
                "content": content_html,
                "thumb_media_id": thumb_media_id or "",
                "need_open_comment": 1,
                "only_fans_can_comment": 0
            }]
        }

        try:
            import json
            article_json = json.dumps(article, ensure_ascii=False)
            headers = {"Content-Type": "application/json; charset=utf-8"}
            resp = requests.post(url, data=article_json.encode('utf-8'), headers=headers, timeout=20)
            result = resp.json()
            
            errcode = result.get("errcode")
            
            if errcode is not None and errcode != 0:
                print(f"❌ 推送失败: {result.get('errmsg', result)}")
                return False
            
            if result.get("media_id"):
                print(f"🎉 成功推送到微信公众号草稿箱！")
                print(f"标题：{title}")
                print(f"请登录 mp.weixin.qq.com → 素材管理 → 草稿箱 查看并发布")
                return True
            
            print(f"❌ 推送失败: 未知响应格式 - {result}")
            return False

        except Exception as e:
            print(f"❌ 推送异常: {e}")
            return False


def push_article_to_wechat(title: str, markdown_content: str, cover_image_path: str = None, content_images: List[str] = None) -> bool:
    """
    对外统一调用接口
    
    Args:
        title: 文章标题
        markdown_content: Markdown 格式内容
        cover_image_path: 封面图路径（本地路径或网络URL）
        content_images: 文章内容中的图片URL列表
    """
    pusher = WeChatDraftPusher()
    return pusher.push_to_draft(title, markdown_content, cover_image_path, content_images)


if __name__ == "__main__":
    print("微信公众号草稿箱推送模块加载完成")
    print("使用方式：push_article_to_wechat(title, markdown_content, cover_image_path, content_images)")
