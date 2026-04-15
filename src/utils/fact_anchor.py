"""
事实锚点注入模块 - 动态敏感事实清单
用于强化事实锚点，防止AI生成过时或错误信息
"""
from datetime import datetime
from typing import Dict, List, Optional


class FactAnchorManager:
    """事实锚点管理器"""
    
    # 高频敏感事实清单（需要定期更新）
    SENSITIVE_FACTS = {
        "us_politics": {
            "president": {"name": "Donald Trump", "title": "President", "since": "2025-01-20"},
            "vice_president": {"name": "JD Vance", "title": "Vice President", "since": "2025-01-20"},
            "secretary_of_state": {"name": "Marco Rubio", "title": "Secretary of State", "since": "2025-01-21"},
        },
        "vatican": {
            "pope": {"name": "Pope Leo XIV", "title": "Pope", "since": "2025-05-08"},
        },
        "uk": {
            "prime_minister": {"name": "Keir Starmer", "title": "Prime Minister", "since": "2024-07-05"},
            "monarch": {"name": "King Charles III", "title": "King", "since": "2022-09-08"},
        },
        "china": {
            "president": {"name": "习近平", "title": "国家主席", "since": "2013-03-14"},
            "premier": {"name": "李强", "title": "国务院总理", "since": "2023-03-11"},
        },
        "russia": {
            "president": {"name": "Vladimir Putin", "title": "President", "since": "2000-05-07"},
        },
        "israel_palestine": {
            "israel_pm": {"name": "Benjamin Netanyahu", "title": "Prime Minister", "since": "2022-12-29"},
        },
        "ukraine": {
            "president": {"name": "Volodymyr Zelenskyy", "title": "President", "since": "2019-05-20"},
        },
    }
    
    @classmethod
    def get_current_date(cls) -> str:
        """获取当前日期"""
        return datetime.now().strftime("%Y-%m-%d")
    
    @classmethod
    def generate_anchor_prompt(cls, topics: Optional[List[str]] = None) -> str:
        """
        生成事实锚点提示
        
        Args:
            topics: 相关话题列表，用于筛选相关事实
        
        Returns:
            事实锚点提示文本
        """
        current_date = cls.get_current_date()
        
        prompt = f"""【事实锚点 - 当前日期: {current_date}】

以下事实经过验证，分析时必须遵循：

"""
        
        # 根据话题筛选相关事实
        if topics:
            relevant_facts = cls._filter_facts_by_topics(topics)
        else:
            relevant_facts = cls.SENSITIVE_FACTS
        
        # 生成事实清单
        for category, facts in relevant_facts.items():
            if facts:
                prompt += f"\n{cls._get_category_name(category)}:\n"
                for key, info in facts.items():
                    prompt += f"  - {info['title']}: {info['name']} (自{info['since']}起任职)\n"
        
        prompt += f"""
【重要规则】
1. 以上人物职位信息为当前准确信息，分析时必须使用
2. 如果新闻内容与上述事实矛盾，优先相信上述事实（可能新闻已过时）
3. 对于不确定的职位信息，宁可只用人名，不要加可能错误的头衔
4. 提及以上人物时，必须确认其当前职位状态

"""
        
        return prompt
    
    @classmethod
    def _filter_facts_by_topics(cls, topics: List[str]) -> Dict:
        """根据话题筛选相关事实"""
        topic_mapping = {
            "us": ["us_politics"],
            "usa": ["us_politics"],
            "america": ["us_politics"],
            "trump": ["us_politics"],
            "biden": ["us_politics"],
            "vatican": ["vatican"],
            "pope": ["vatican"],
            "catholic": ["vatican"],
            "uk": ["uk"],
            "britain": ["uk"],
            "china": ["china"],
            "russia": ["russia"],
            "putin": ["russia"],
            "israel": ["israel_palestine"],
            "palestine": ["israel_palestine"],
            "gaza": ["israel_palestine"],
            "ukraine": ["ukraine"],
            "zelenskyy": ["ukraine"],
        }
        
        relevant_categories = set()
        for topic in topics:
            topic_lower = topic.lower()
            if topic_lower in topic_mapping:
                relevant_categories.update(topic_mapping[topic_lower])
        
        # 如果没有匹配到，返回所有事实
        if not relevant_categories:
            return cls.SENSITIVE_FACTS
        
        return {cat: cls.SENSITIVE_FACTS.get(cat, {}) for cat in relevant_categories}
    
    @classmethod
    def _get_category_name(cls, category: str) -> str:
        """获取分类显示名称"""
        names = {
            "us_politics": "美国政治",
            "vatican": "梵蒂冈",
            "uk": "英国",
            "china": "中国",
            "russia": "俄罗斯",
            "israel_palestine": "以色列/巴勒斯坦",
            "ukraine": "乌克兰",
        }
        return names.get(category, category)
    
    @classmethod
    def extract_topics_from_news(cls, title: str, content: str) -> List[str]:
        """从新闻中提取话题关键词"""
        text = f"{title} {content}".lower()
        
        topic_keywords = {
            "trump": ["trump", "特朗普", "川普"],
            "biden": ["biden", "拜登"],
            "us": ["us", "usa", "america", "american", "美国", "华盛顿"],
            "vatican": ["vatican", "pope", "catholic", "梵蒂冈", "教皇", "教宗"],
            "uk": ["uk", "britain", "british", "london", "英国", "伦敦"],
            "china": ["china", "chinese", "beijing", "中国", "北京"],
            "russia": ["russia", "russian", "moscow", "putin", "俄罗斯", "莫斯科", "普京"],
            "israel": ["israel", "israeli", "netanyahu", "以色列", "内塔尼亚胡"],
            "palestine": ["palestine", "palestinian", "gaza", "巴勒斯坦", "加沙"],
            "ukraine": ["ukraine", "ukrainian", "zelenskyy", "乌克兰", "泽连斯基"],
        }
        
        found_topics = []
        for topic, keywords in topic_keywords.items():
            if any(kw in text for kw in keywords):
                found_topics.append(topic)
        
        return found_topics


# 便捷函数
def get_fact_anchor_prompt(title: str = "", content: str = "") -> str:
    """获取事实锚点提示（便捷函数）"""
    topics = FactAnchorManager.extract_topics_from_news(title, content)
    return FactAnchorManager.generate_anchor_prompt(topics)


if __name__ == "__main__":
    # 测试
    test_title = "Trump announces new policy on Israel"
    test_content = "The President met with Netanyahu in Washington..."
    
    prompt = get_fact_anchor_prompt(test_title, test_content)
    print(prompt)
