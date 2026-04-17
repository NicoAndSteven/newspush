"""
微信公众号草稿箱推送模块（NewsPush专用）
只支持推送长文章到公众号草稿箱，不使用 Server酱
"""

import requests
import time
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
                self.token_expire_time = time.time() + 7000   # 提前刷新
                print("✅ 微信 access_token 获取成功")
                return self.access_token
            else:
                print(f"❌ 获取 access_token 失败: {data.get('errmsg')}")
                return None
        except Exception as e:
            print(f"❌ 获取 access_token 异常: {e}")
            return None

    def _download_image(self, image_url: str) -> Optional[str]:
        """
        下载网络图片到临时文件
        
        Args:
            image_url: 图片URL
            
        Returns:
            str: 本地临时文件路径 或 None
        """
        if not image_url:
            return None
            
        # 如果已经是本地路径，直接返回
        if Path(image_url).exists():
            return image_url
        
        # 检查是否是有效的URL
        if not image_url.startswith(('http://', 'https://')):
            print(f"⚠️  无效的图片URL: {image_url}")
            return None
        
        try:
            print(f"    正在下载封面图: {image_url[:50]}...")
            response = requests.get(image_url, timeout=15, stream=True)
            
            if response.status_code != 200:
                print(f"⚠️  下载图片失败，状态码: {response.status_code}")
                return None
            
            # 检查Content-Type
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type:
                # 尝试从URL判断
                if not any(ext in image_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    print(f"⚠️  不是有效的图片: {content_type}")
                    return None
            
            # 保存到临时文件
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
            
            print(f"    图片下载成功: {tmp_path}")
            return tmp_path
            
        except Exception as e:
            print(f"⚠️  下载图片异常: {e}")
            return None

    def upload_cover_image(self, image_path: str) -> Optional[str]:
        """
        上传封面图片，返回 thumb_media_id
        支持本地路径或网络URL
        """
        token = self._get_access_token()
        if not token:
            return None

        # 处理网络URL - 先下载到本地
        temp_file = None
        actual_path = image_path
        
        if image_path.startswith(('http://', 'https://')):
            temp_file = self._download_image(image_path)
            if temp_file:
                actual_path = temp_file
            else:
                return None
        elif not Path(image_path).exists():
            print(f"⚠️  图片路径不存在: {image_path}")
            return None

        url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"

        try:
            with open(actual_path, 'rb') as f:
                files = {'media': (Path(actual_path).name, f, 'image/jpeg')}
                resp = requests.post(url, files=files, timeout=30)
            
            result = resp.json()
            if 'media_id' in result:
                print(f"✅ 封面图上传成功 → {result['media_id'][:20]}...")
                return result['media_id']
            else:
                print(f"❌ 封面图上传失败: {result}")
                return None
        except Exception as e:
            print(f"❌ 上传封面图异常: {e}")
            return None
        finally:
            # 清理临时文件
            if temp_file and Path(temp_file).exists():
                try:
                    os.unlink(temp_file)
                except:
                    pass

    def markdown_to_wechat_html(self, markdown_text: str) -> str:
        """简单 Markdown 转微信 HTML（可后续继续优化）"""
        if not markdown_text:
            return "<p>暂无内容</p>"

        html = markdown_text.replace("\n\n", "<br><br>")
        html = html.replace("\n", "<br>")
        html = html.replace("**", "<strong>").replace("__", "<strong>")
        html = html.replace("*", "<em>")

        return f'''
        <section style="font-size: 16px; line-height: 1.8; color: #333;">
            {html}
        </section>
        '''

    def push_to_draft(self, title: str, markdown_content: str, cover_image_path: str = None) -> bool:
        """
        主函数：把一篇文章推送到微信公众号草稿箱
        
        Args:
            title: 文章标题
            markdown_content: Markdown 格式内容
            cover_image_path: 封面图路径（本地路径或网络URL）
        """
        if not self.appid or not self.secret:
            print("❌ 请先在 .env 中配置 WECHAT_APPID 和 WECHAT_SECRET")
            return False

        # 1. 处理封面图（支持本地路径或网络URL）
        thumb_media_id = None
        if cover_image_path:
            thumb_media_id = self.upload_cover_image(cover_image_path)
        
        if not thumb_media_id:
            print("⚠️  未找到有效封面图，将尝试无封面推送（可能失败）")

        # 2. 转换内容为微信 HTML
        content_html = self.markdown_to_wechat_html(markdown_content)

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
                "thumb_media_id": thumb_media_id or "",   # 封面必填，建议必须有
                "need_open_comment": 1,
                "only_fans_can_comment": 0
            }]
        }

        try:
            # 使用 ensure_ascii=False 防止中文被转义为 Unicode
            import json
            article_json = json.dumps(article, ensure_ascii=False)
            headers = {"Content-Type": "application/json; charset=utf-8"}
            resp = requests.post(url, data=article_json.encode('utf-8'), headers=headers, timeout=20)
            result = resp.json()
            
            # 调试日志
            print(f"    [调试] 微信API响应: {result}")

            # 微信API返回的错误码判断
            # 成功时返回: {"media_id": "xxx"}
            # 失败时返回: {"errcode": xxx, "errmsg": "..."}
            errcode = result.get("errcode")
            
            # 有错误码且不为0，说明失败
            if errcode is not None and errcode != 0:
                print(f"❌ 推送失败: {result.get('errmsg', result)}")
                return False
            
            # 有 media_id 说明成功（无论 item 是否为空）
            if result.get("media_id"):
                print(f"🎉 成功推送到微信公众号草稿箱！")
                print(f"标题：{title}")
                print(f"media_id: {result.get('media_id')}")
                print(f"请登录 mp.weixin.qq.com → 素材管理 → 草稿箱 查看并发布")
                return True
            
            # 其他情况
            print(f"❌ 推送失败: 未知响应格式 - {result}")
            return False

        except Exception as e:
            print(f"❌ 推送异常: {e}")
            return False


# ====================== 对外调用函数 ======================
def push_article_to_wechat(title: str, markdown_content: str, cover_image_path: str = None) -> bool:
    """
    对外统一调用接口
    
    Args:
        title: 文章标题
        markdown_content: Markdown 格式内容
        cover_image_path: 封面图路径（本地路径或网络URL，如 Pexels 图片链接）
    """
    pusher = WeChatDraftPusher()
    return pusher.push_to_draft(title, markdown_content, cover_image_path)


if __name__ == "__main__":
    print("微信公众号草稿箱推送模块加载完成")
    print("使用方式：push_article_to_wechat(title, markdown_content, cover_image_path)")
