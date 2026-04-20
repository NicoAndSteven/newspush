"""
翻译模块 - 使用阿里云翻译 API
将英文新闻标题翻译为中文
"""
import os
import random
from typing import Optional


def get_random_temperature_for_translation(min_temp: float = 0.2, max_temp: float = 0.4) -> float:
    """生成用于翻译的随机 temperature（较低，确保准确性）"""
    return round(random.uniform(min_temp, max_temp), 2)


# 尝试导入 Google 翻译（备用）
try:
    from deep_translator import GoogleTranslator
    GOOGLE_TRANSLATOR_AVAILABLE = True
except ImportError:
    GOOGLE_TRANSLATOR_AVAILABLE = False

# 阿里云翻译 API 配置
ALIBABA_TRANSLATE_URL = "https://mt.aliyuncs.com/api/translate/web/general"


def translate_title(title: str, target_lang: str = "zh-CN") -> str:
    """
    翻译标题 - 优先使用阿里云翻译
    
    Args:
        title: 原始标题（可能是英文）
        target_lang: 目标语言，默认中文
    
    Returns:
        翻译后的标题
    """
    # 如果标题已经是中文，直接返回
    if _is_chinese(title):
        return title
    
    # 首先尝试阿里云翻译
    result = _translate_with_alibaba(title, target_lang)
    if result and result != title:
        return result
    
    # 如果阿里云翻译失败，尝试 Google 翻译（备用）
    if GOOGLE_TRANSLATOR_AVAILABLE:
        try:
            translator = GoogleTranslator(source='auto', target=target_lang)
            result = translator.translate(title)
            return result
        except Exception as e:
            print(f"  [Google翻译错误] {e}")
    
    # 都失败则返回原文
    return title


def _translate_with_alibaba(text: str, target_lang: str = "zh-CN") -> Optional[str]:
    """使用阿里云机器翻译 API"""
    import json
    import time
    import hmac
    import hashlib
    import base64
    import urllib.parse
    import requests
    
    access_key_id = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
    access_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
    
    if not access_key_id or not access_key_secret:
        # 如果没有配置阿里云翻译，尝试使用 DashScope 进行翻译
        return _translate_with_dashscope(text, target_lang)
    
    try:
        # 构建签名
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        params = {
            "Format": "JSON",
            "Version": "2019-01-02",
            "AccessKeyId": access_key_id,
            "SignatureMethod": "HMAC-SHA1",
            "Timestamp": timestamp,
            "SignatureVersion": "1.0",
            "SignatureNonce": str(int(time.time() * 1000)),
            "Action": "TranslateGeneral",
            "SourceLanguage": "auto",
            "TargetLanguage": target_lang,
            "SourceText": text,
        }
        
        # 排序并编码参数
        sorted_params = sorted(params.items())
        canonical_query_string = urllib.parse.urlencode(sorted_params)
        
        # 构建签名字符串
        string_to_sign = f"GET&%2F&{urllib.parse.quote(canonical_query_string, safe='')}"        
        key = f"{access_key_secret}&"
        signature = base64.b64encode(
            hmac.new(key.encode(), string_to_sign.encode(), hashlib.sha1).digest()
        ).decode()
        
        params["Signature"] = signature
        
        response = requests.get(
            "https://mt.aliyuncs.com/",
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "Data" in data and "Translated" in data["Data"]:
                return data["Data"]["Translated"]
        
        return None
        
    except Exception as e:
        print(f"  [阿里云翻译错误] {e}")
        return None


def _translate_with_dashscope(text: str, target_lang: str = "zh-CN") -> Optional[str]:
    """使用 DashScope API 进行翻译（备用方案）"""
    try:
        from openai import OpenAI
        
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return None
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        prompt = f"请将以下英文新闻标题翻译成中文，只返回翻译结果，不要解释：\n\n{text}"
        
        response = client.chat.completions.create(
            model="qwen3.6-35b-a3b",
            messages=[{"role": "user", "content": prompt}],
            temperature=get_random_temperature_for_translation()
        )
        
        result = response.choices[0].message.content.strip()
        # 移除可能的引号
        result = result.strip('"\'')
        return result
        
    except Exception as e:
        print(f"  [DashScope翻译错误] {e}")
        return None


def _is_chinese(text: str) -> bool:
    """判断文本是否主要是中文"""
    if not text:
        return False
    
    chinese_count = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    return chinese_count / len(text) > 0.3


def translate_if_needed(title: str) -> str:
    """
    如果需要则翻译标题
    返回格式：翻译后的标题
    """
    return translate_title(title)


if __name__ == "__main__":
    # 测试
    test_titles = [
        "U.S. imposes naval blockade as Trump demands Iran end nuclear program",
        "中国经济增长强劲",
        "Pope Leo XIV calls for peace in Easter message",
        "特斯拉发布新车型",
    ]
    
    print("=" * 60)
    print("翻译测试")
    print("=" * 60)
    
    for title in test_titles:
        translated = translate_if_needed(title)
        print(f"\n原文: {title}")
        print(f"译文: {translated}")
