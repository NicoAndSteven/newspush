"""
微信公众号草稿箱推送模块（NewsPush专用）
只支持推送长文章到公众号草稿箱，不使用 Server酱
"""

import requests
import time
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

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

    def upload_cover_image(self, image_path: str) -> Optional[str]:
        """上传封面图片，返回 thumb_media_id"""
        token = self._get_access_token()
        if not token:
            return None

        url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"

        try:
            with open(image_path, 'rb') as f:
                files = {'media': (Path(image_path).name, f, 'image/jpeg')}
                resp = requests.post(url, files=files, timeout=30)
            
            result = resp.json()
            if 'media_id' in result:
                print(f"✅ 封面图上传成功 → {result['media_id']}")
                return result['media_id']
            else:
                print(f"❌ 封面图上传失败: {result}")
                return None
        except Exception as e:
            print(f"❌ 上传封面图异常: {e}")
            return None

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
        """
        if not self.appid or not self.secret:
            print("❌ 请先在 .env 中配置 WECHAT_APPID 和 WECHAT_SECRET")
            return False

        # 1. 处理封面图（如果没有则使用默认）
        thumb_media_id = None
        if cover_image_path and Path(cover_image_path).exists():
            thumb_media_id = self.upload_cover_image(cover_image_path)
        
        if not thumb_media_id:
            print("⚠️  未找到有效封面图，将使用默认封面（可能失败）")
            # 这里可以放一个默认图片的 media_id，后续可优化

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
            resp = requests.post(url, json=article, timeout=20)
            result = resp.json()

            if result.get("errcode") == 0:
                print(f"🎉 成功推送到微信公众号草稿箱！")
                print(f"标题：{title}")
                print(f"请登录 mp.weixin.qq.com → 素材管理 → 草稿箱 查看并发布")
                return True
            else:
                print(f"❌ 推送失败: {result.get('errmsg', result)}")
                return False

        except Exception as e:
            print(f"❌ 推送异常: {e}")
            return False


# ====================== 对外调用函数 ======================
def push_article_to_wechat(title: str, markdown_content: str, cover_image_path: str = None) -> bool:
    """对外统一调用接口"""
    pusher = WeChatDraftPusher()
    return pusher.push_to_draft(title, markdown_content, cover_image_path)


if __name__ == "__main__":
    print("微信公众号草稿箱推送模块加载完成")
    print("使用方式：push_article_to_wechat(title, markdown_content, cover_image_path)")