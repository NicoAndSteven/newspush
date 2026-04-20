"""
多模板输出格式化器
根据新闻类型自动选择合适的模板
"""
from typing import Dict, List, Optional
from datetime import datetime


class OutputFormatter:
    """输出格式化器 - 支持多模板"""
    
    @staticmethod
    def generate_internal_version(
        news_title: str,
        news_source: str,
        stage1_facts: Dict,
        stage2_analysis: Dict,
        sensitivity_info: Dict,
        images: List[str] = None
    ) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        images = images or []
        
        md = f"""# {news_title}

> **来源**: {news_source} | **生成时间**: {now}
> **敏感度**: {sensitivity_info.get('level', 'unknown').upper()} | {sensitivity_info.get('reason', '')}

---

## 事实核查详情

### 基础事实
"""
        
        basic_facts = stage1_facts.get("basic_facts", {})
        if basic_facts:
            md += f"""
- **事件日期**: {basic_facts.get('event_date', '未明确')}
- **地点**: {basic_facts.get('location', '未明确')}
- **核心事件**: {basic_facts.get('main_event', '')}

### 关键人物
"""
            for figure in basic_facts.get("key_figures", []):
                md += f"""
- **{figure.get('name', '')}**: {figure.get('title', '')}
  - 角色: {figure.get('role_in_event', '')}
"""
        
        timeline = stage1_facts.get("timeline", [])
        if timeline:
            md += "\n### 时间线\n"
            for item in timeline:
                md += f"\n- **{item.get('date', '')}**: {item.get('event', '')}"
                if item.get('source'):
                    md += f" (来源: {item['source']})"
        
        claims = stage1_facts.get("claims_verification", [])
        if claims:
            md += "\n\n### 主张验证\n"
            for claim in claims:
                status = "✓" if claim.get('verified') else "✗" if claim.get('verified') is False else "?"
                md += f"\n{status} **{claim.get('claim', '')}**"
                md += f"\n  - 置信度: {claim.get('confidence', 'unknown')}"
                md += f"\n  - 依据: {claim.get('evidence', '')}"
        
        sources = stage1_facts.get("sources", [])
        if sources:
            md += "\n\n### 信息来源\n"
            for src in sources:
                md += f"\n- [{src.get('credibility', 'unknown').upper()}] {src.get('type', '')}: {src.get('name', '')}"
        
        conflicts = stage1_facts.get("conflicting_info", [])
        if conflicts:
            md += "\n\n### ⚠️ 矛盾/存疑信息\n"
            for conflict in conflicts:
                md += f"\n- {conflict}"
        
        md += f"""

---

## 深度分析

### 导语
{stage2_analysis.get('summary', '')}

### 核心要点
"""
        for i, point in enumerate(stage2_analysis.get("key_points", []), 1):
            md += f"\n{i}. {point}"
        
        md += f"""

### 背景
{stage2_analysis.get('background', '')}

### 影响分析
{stage2_analysis.get('impact_analysis', '')}

### 未来展望
{stage2_analysis.get('future_outlook', '')}

### 争议焦点
"""
        for aspect in stage2_analysis.get("controversial_aspects", []):
            md += f"\n- {aspect}"
        
        md += f"""

### 专家点评
{stage2_analysis.get('expert_opinion', '')}

---

## 元数据

- **内容类型**: {stage2_analysis.get('content_type', '') or ''}
- **情感倾向**: {stage2_analysis.get('sentiment', '') or ''}
- **紧急程度**: {stage2_analysis.get('urgency_level', 5) or 5}/10
- **标签**: {', '.join(stage2_analysis.get('tags', []) or [])}
- **可信度**: {((stage2_analysis.get('credibility') if isinstance(stage2_analysis.get('credibility'), dict) else {'level': stage2_analysis.get('credibility', 'unknown')}) or {}).get('level', 'unknown')}

---

*此版本为内部完整版，包含事实来源标注和系统痕迹*
"""
        
        return md
    
    @staticmethod
    def generate_public_version(
        news_title: str,
        news_source: str,
        stage2_analysis: Dict,
        images: List[str] = None,
        category: str = "general"
    ) -> str:
        """
        根据新闻类型选择合适的模板
        """
        content_type = stage2_analysis.get('content_type', 'news')
        
        template_map = {
            'entertainment': OutputFormatter._generate_entertainment_version,
            'lifestyle': OutputFormatter._generate_entertainment_version,
            'sports': OutputFormatter._generate_sports_version,
            'tech': OutputFormatter._generate_tech_version,
            'finance': OutputFormatter._generate_finance_version,
            'breaking': OutputFormatter._generate_breaking_version,
        }
        
        category_template_map = {
            'entertainment': OutputFormatter._generate_entertainment_version,
            'sports': OutputFormatter._generate_sports_version,
            'tech': OutputFormatter._generate_tech_version,
            'finance': OutputFormatter._generate_finance_version,
        }
        
        if category in category_template_map:
            return category_template_map[category](news_title, news_source, stage2_analysis, images)
        
        if content_type in template_map:
            return template_map[content_type](news_title, news_source, stage2_analysis, images)
        
        return OutputFormatter._generate_standard_version(news_title, news_source, stage2_analysis, images)
    
    @staticmethod
    def _generate_entertainment_version(
        news_title: str,
        news_source: str,
        stage2_analysis: Dict,
        images: List[str] = None
    ) -> str:
        """娱乐新闻模板 - 轻松活泼，简洁报道"""
        images = images or []
        md = f"# {news_title}\n\n"
        
        if images:
            md += f"![配图]({images[0]})\n\n"
        
        if stage2_analysis.get('summary'):
            md += f"{stage2_analysis['summary']}\n\n"
        
        if stage2_analysis.get('expert_opinion'):
            md += f"{stage2_analysis['expert_opinion']}\n\n"
        
        if len(images) > 1:
            md += f"![配图]({images[1]})\n\n"
        
        if stage2_analysis.get('background'):
            md += f"**背景**：{stage2_analysis['background']}\n\n"
        
        if stage2_analysis.get('tags'):
            md += "---\n\n"
            md += ' '.join([f"#{t.replace(' ', '_')}" for t in stage2_analysis['tags'][:5]])
            md += "\n"
        
        return md
    
    @staticmethod
    def _generate_sports_version(
        news_title: str,
        news_source: str,
        stage2_analysis: Dict,
        images: List[str] = None
    ) -> str:
        """体育新闻模板 - 赛事报道风格"""
        images = images or []
        md = f"# {news_title}\n\n"
        
        if images:
            md += f"![配图]({images[0]})\n\n"
        
        if stage2_analysis.get('summary'):
            md += f"**{stage2_analysis['summary']}**\n\n"
        
        key_points = stage2_analysis.get('key_points', [])
        if key_points:
            md += "## 比赛亮点\n\n"
            for point in key_points[:5]:
                md += f"- {point}\n"
            md += "\n"
        
        if stage2_analysis.get('expert_opinion'):
            md += f"{stage2_analysis['expert_opinion']}\n\n"
        
        if len(images) > 1:
            md += f"![配图]({images[1]})\n\n"
        
        if stage2_analysis.get('impact_analysis'):
            md += f"**赛后分析**：{stage2_analysis['impact_analysis']}\n\n"
        
        if stage2_analysis.get('future_outlook'):
            md += f"**后续展望**：{stage2_analysis['future_outlook']}\n\n"
        
        if stage2_analysis.get('tags'):
            md += "---\n\n"
            md += ' '.join([f"#{t.replace(' ', '_')}" for t in stage2_analysis['tags'][:5]])
            md += "\n"
        
        return md
    
    @staticmethod
    def _generate_tech_version(
        news_title: str,
        news_source: str,
        stage2_analysis: Dict,
        images: List[str] = None
    ) -> str:
        """科技新闻模板 - 技术解读风格"""
        images = images or []
        md = f"# {news_title}\n\n"
        
        if images:
            md += f"![配图]({images[0]})\n\n"
        
        if stage2_analysis.get('summary'):
            md += f"{stage2_analysis['summary']}\n\n"
        
        key_points = stage2_analysis.get('key_points', [])
        if key_points:
            md += "## 技术要点\n\n"
            for i, point in enumerate(key_points[:5], 1):
                md += f"{i}. {point}\n"
            md += "\n"
        
        if stage2_analysis.get('expert_opinion'):
            md += f"{stage2_analysis['expert_opinion']}\n\n"
        
        if len(images) > 1:
            md += f"![配图]({images[1]})\n\n"
        
        if stage2_analysis.get('background'):
            md += f"**技术背景**：{stage2_analysis['background']}\n\n"
        
        if stage2_analysis.get('impact_analysis'):
            md += f"**行业影响**：{stage2_analysis['impact_analysis']}\n\n"
        
        if stage2_analysis.get('future_outlook'):
            md += f"**未来趋势**：{stage2_analysis['future_outlook']}\n\n"
        
        if stage2_analysis.get('tags'):
            md += "---\n\n"
            md += ' '.join([f"#{t.replace(' ', '_')}" for t in stage2_analysis['tags'][:5]])
            md += "\n"
        
        return md
    
    @staticmethod
    def _generate_finance_version(
        news_title: str,
        news_source: str,
        stage2_analysis: Dict,
        images: List[str] = None
    ) -> str:
        """财经新闻模板 - 数据解读风格"""
        images = images or []
        md = f"# {news_title}\n\n"
        
        if images:
            md += f"![配图]({images[0]})\n\n"
        
        if stage2_analysis.get('summary'):
            md += f"**{stage2_analysis['summary']}**\n\n"
        
        key_points = stage2_analysis.get('key_points', [])
        if key_points:
            md += "## 核心要点\n\n"
            for i, point in enumerate(key_points[:5], 1):
                md += f"{i}. {point}\n"
            md += "\n"
        
        if stage2_analysis.get('expert_opinion'):
            md += f"{stage2_analysis['expert_opinion']}\n\n"
        
        if len(images) > 1:
            md += f"![配图]({images[1]})\n\n"
        
        if stage2_analysis.get('background'):
            md += f"**市场背景**：{stage2_analysis['background']}\n\n"
        
        if stage2_analysis.get('impact_analysis'):
            md += f"**市场影响**：{stage2_analysis['impact_analysis']}\n\n"
        
        if stage2_analysis.get('future_outlook'):
            md += f"**投资展望**：{stage2_analysis['future_outlook']}\n\n"
        
        if stage2_analysis.get('tags'):
            md += "---\n\n"
            md += ' '.join([f"#{t.replace(' ', '_')}" for t in stage2_analysis['tags'][:5]])
            md += "\n"
        
        return md
    
    @staticmethod
    def _generate_breaking_version(
        news_title: str,
        news_source: str,
        stage2_analysis: Dict,
        images: List[str] = None
    ) -> str:
        """突发新闻模板 - 简洁快速"""
        images = images or []
        md = f"# ⚡ {news_title}\n\n"
        
        if images:
            md += f"![配图]({images[0]})\n\n"
        
        md += f"> **突发** | 来源：{news_source}\n\n"
        
        if stage2_analysis.get('summary'):
            md += f"{stage2_analysis['summary']}\n\n"
        
        key_points = stage2_analysis.get('key_points', [])
        if key_points:
            md += "## 最新进展\n\n"
            for point in key_points[:3]:
                md += f"- {point}\n"
            md += "\n"
        
        if stage2_analysis.get('expert_opinion'):
            md += f"{stage2_analysis['expert_opinion']}\n\n"
        
        if stage2_analysis.get('tags'):
            md += "---\n\n"
            md += ' '.join([f"#{t.replace(' ', '_')}" for t in stage2_analysis['tags'][:5]])
            md += "\n"
        
        return md
    
    @staticmethod
    def _generate_standard_version(
        news_title: str,
        news_source: str,
        stage2_analysis: Dict,
        images: List[str] = None
    ) -> str:
        """标准新闻模板 - 通用格式"""
        images = images or []
        
        md = f"# {news_title}\n\n"
        
        if images:
            md += f"![配图]({images[0]})\n\n"
        
        if stage2_analysis.get('summary'):
            md += f"{stage2_analysis['summary']}\n\n"
        
        if stage2_analysis.get('expert_opinion'):
            md += f"{stage2_analysis['expert_opinion']}\n\n"
        
        if len(images) > 1:
            md += f"![配图]({images[1]})\n\n"
        
        if stage2_analysis.get('background'):
            md += f"{stage2_analysis['background']}\n\n"
        
        if len(images) > 2:
            md += f"![配图]({images[2]})\n\n"
        
        if stage2_analysis.get('impact_analysis'):
            md += f"{stage2_analysis['impact_analysis']}\n\n"
        
        if stage2_analysis.get('future_outlook'):
            md += f"{stage2_analysis['future_outlook']}\n\n"
        
        if stage2_analysis.get('tags'):
            md += "---\n\n"
            md += ' '.join([f"#{t.replace(' ', '_')}" for t in stage2_analysis['tags'][:6]])
            md += "\n"
        
        return md


def generate_both_versions(
    news_title: str,
    news_source: str,
    stage1_facts: Dict,
    stage2_analysis: Dict,
    sensitivity_info: Dict,
    images: List[str] = None,
    category: str = "general"
) -> Dict[str, str]:
    """同时生成两个版本"""
    formatter = OutputFormatter()
    
    return {
        "internal": formatter.generate_internal_version(
            news_title, news_source, stage1_facts, stage2_analysis, sensitivity_info, images
        ),
        "public": formatter.generate_public_version(
            news_title, news_source, stage2_analysis, images, category
        )
    }


if __name__ == "__main__":
    test_stage2 = {
        "summary": "这是一条测试新闻",
        "key_points": ["要点1", "要点2", "要点3"],
        "background": "背景信息...",
        "impact_analysis": "影响分析...",
        "future_outlook": "未来展望...",
        "expert_opinion": "专家点评内容...",
        "tags": ["测试", "新闻"]
    }
    
    print("=== 娱乐新闻模板 ===")
    print(OutputFormatter._generate_entertainment_version("明星动态", "TMZ", test_stage2))
    
    print("\n=== 体育新闻模板 ===")
    print(OutputFormatter._generate_sports_version("比赛结果", "ESPN", test_stage2))
    
    print("\n=== 科技新闻模板 ===")
    print(OutputFormatter._generate_tech_version("技术突破", "TechCrunch", test_stage2))
    
    print("\n=== 财经新闻模板 ===")
    print(OutputFormatter._generate_finance_version("市场动态", "Financial Times", test_stage2))
