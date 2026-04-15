"""
敏感度分级处理系统
自动识别新闻敏感度，高敏感新闻强制走两阶段+人工复核流程
"""
from typing import Dict, List, Tuple
from enum import Enum


class SensitivityLevel(Enum):
    """敏感度等级"""
    LOW = "low"           # 低敏感
    MEDIUM = "medium"     # 中敏感
    HIGH = "high"         # 高敏感（需人工复核）


class SensitivityChecker:
    """敏感度检查器"""
    
    # 高敏感关键词
    HIGH_SENSITIVE_KEYWORDS = {
        "religion": [
            "pope", "vatican", "catholic", "教皇", "教宗", "梵蒂冈",
            "islam", "muslim", "islamic", "伊斯兰", "穆斯林",
            "jewish", "judaism", "犹太", "犹太教",
            "buddhist", "buddhism", "佛教", "和尚", "喇嘛",
        ],
        "election": [
            "election", "vote", "voting", "ballot", "选举", "投票", "大选",
            "presidential election", "parliamentary election", "总统选举", "议会选举",
            "campaign", "rally", "竞选", "造势",
        ],
        "conflict": [
            "war", "conflict", "invasion", "attack", "战争", "冲突", "入侵", "袭击",
            "israel", "palestine", "gaza", "hamas", "以色列", "巴勒斯坦", "加沙", "哈马斯",
            "ukraine", "russia", "putin", "zelenskyy", "乌克兰", "俄罗斯", "普京", "泽连斯基",
            "taiwan", "taiwan strait", "台湾", "台海",
            "south china sea", "南海",
            "korea", "north korea", "kim jong", "朝鲜", "金正恩",
        ],
        "terrorism": [
            "terrorist", "terrorism", "isis", "al-qaeda", "恐怖", "恐怖主义",
            "bombing", "explosion", "爆炸", "炸弹",
        ],
        "extreme_weather": [
            "earthquake", "tsunami", "hurricane", "typhoon", "地震", "海啸", "飓风", "台风",
            "disaster", "catastrophe", "灾难", "灾害",
        ],
    }
    
    # 中敏感关键词
    MEDIUM_SENSITIVE_KEYWORDS = {
        "politics": [
            "government", "policy", "regulation", "政府", "政策", "法规",
            "sanction", "embargo", "制裁", "禁运",
            "diplomatic", "diplomacy", "外交",
            "summit", "meeting", "峰会", "会晤",
        ],
        "economy": [
            "trade war", "tariff", "贸易战", "关税",
            "recession", "crisis", "衰退", "危机",
            "currency", "exchange rate", "货币", "汇率",
        ],
        "social": [
            "protest", "demonstration", "抗议", "示威",
            "strike", "riot", "罢工", "骚乱",
        ],
    }
    
    @classmethod
    def check_sensitivity(cls, title: str, content: str) -> Tuple[SensitivityLevel, Dict]:
        """
        检查新闻敏感度
        
        Returns:
            (敏感度等级, 详细信息)
        """
        text = f"{title} {content}".lower()
        
        # 检查高敏感
        high_matches = []
        for category, keywords in cls.HIGH_SENSITIVE_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text:
                    high_matches.append((category, kw))
        
        if high_matches:
            return SensitivityLevel.HIGH, {
                "level": "high",
                "reason": "包含高敏感话题",
                "matched_keywords": list(set([m[1] for m in high_matches])),
                "categories": list(set([m[0] for m in high_matches])),
                "requires_review": True,
                "recommendation": "强制使用两阶段分析 + 建议人工复核"
            }
        
        # 检查中敏感
        medium_matches = []
        for category, keywords in cls.MEDIUM_SENSITIVE_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text:
                    medium_matches.append((category, kw))
        
        if medium_matches:
            return SensitivityLevel.MEDIUM, {
                "level": "medium",
                "reason": "包含中敏感话题",
                "matched_keywords": list(set([m[1] for m in medium_matches])),
                "categories": list(set([m[0] for m in medium_matches])),
                "requires_review": False,
                "recommendation": "建议使用两阶段分析"
            }
        
        # 低敏感
        return SensitivityLevel.LOW, {
            "level": "low",
            "reason": "常规话题",
            "matched_keywords": [],
            "categories": [],
            "requires_review": False,
            "recommendation": "标准分析流程"
        }
    
    @classmethod
    def get_sensitivity_label(cls, level: SensitivityLevel) -> str:
        """获取敏感度标签"""
        labels = {
            SensitivityLevel.LOW: "🟢 低敏感",
            SensitivityLevel.MEDIUM: "🟡 中敏感",
            SensitivityLevel.HIGH: "🔴 高敏感"
        }
        return labels.get(level, "未知")


# 便捷函数
def check_news_sensitivity(title: str, content: str) -> Tuple[str, Dict]:
    """检查新闻敏感度（便捷函数）"""
    level, info = SensitivityChecker.check_sensitivity(title, content)
    return level.value, info


if __name__ == "__main__":
    # 测试
    test_cases = [
        "Pope Leo XIV announces new policy",
        "Trump meets with Netanyahu in Washington",
        "Apple releases new iPhone",
        "Taiwan election results announced",
    ]
    
    for title in test_cases:
        level, info = check_news_sensitivity(title, "")
        print(f"\n{title}")
        print(f"  敏感度: {SensitivityChecker.get_sensitivity_label(SensitivityLevel(level))}")
        print(f"  原因: {info['reason']}")
        print(f"  建议: {info['recommendation']}")
