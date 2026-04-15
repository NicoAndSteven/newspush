"""
翻译模块 - 使用 Google 翻译
将英文新闻标题翻译为中文
"""
from typing import Optional

try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    print("[警告] deep-translator 未安装，翻译功能将不可用")


def translate_title(title: str, target_lang: str = "zh-CN") -> str:
    """
    翻译标题
    
    Args:
        title: 原始标题（可能是英文）
        target_lang: 目标语言，默认中文
    
    Returns:
        翻译后的标题
    """
    if not TRANSLATOR_AVAILABLE:
        return title
    
    # 如果标题已经是中文，直接返回
    if _is_chinese(title):
        return title
    
    try:
        translator = GoogleTranslator(source='auto', target=target_lang)
        result = translator.translate(title)
        return result
    except Exception as e:
        print(f"  [翻译错误] {e}")
        return title


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
