"""
双版本输出格式化器
生成内部完整版（带事实来源标注）和对外发布版（干净专业）
"""
from typing import Dict, List, Optional
from datetime import datetime


class OutputFormatter:
    """输出格式化器"""
    
    @staticmethod
    def generate_internal_version(
        news_title: str,
        news_source: str,
        stage1_facts: Dict,
        stage2_analysis: Dict,
        sensitivity_info: Dict,
        images: List[str] = None
    ) -> str:
        """
        生成内部完整版（带事实来源标注）
        
        包含：
        - 完整的事实核查信息
        - 敏感度标注
        - 信息来源标注
        - 矛盾点标注
        """
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
        
        # 时间线
        timeline = stage1_facts.get("timeline", [])
        if timeline:
            md += "\n### 时间线\n"
            for item in timeline:
                md += f"\n- **{item.get('date', '')}**: {item.get('event', '')}"
                if item.get('source'):
                    md += f" (来源: {item['source']})"
        
        # 主张验证
        claims = stage1_facts.get("claims_verification", [])
        if claims:
            md += "\n\n### 主张验证\n"
            for claim in claims:
                status = "✓" if claim.get('verified') else "✗" if claim.get('verified') is False else "?"
                md += f"\n{status} **{claim.get('claim', '')}**"
                md += f"\n  - 置信度: {claim.get('confidence', 'unknown')}"
                md += f"\n  - 依据: {claim.get('evidence', '')}"
        
        # 信息来源
        sources = stage1_facts.get("sources", [])
        if sources:
            md += "\n\n### 信息来源\n"
            for src in sources:
                md += f"\n- [{src.get('credibility', 'unknown').upper()}] {src.get('type', '')}: {src.get('name', '')}"
        
        # 矛盾点
        conflicts = stage1_facts.get("conflicting_info", [])
        if conflicts:
            md += "\n\n### ⚠️ 矛盾/存疑信息\n"
            for conflict in conflicts:
                md += f"\n- {conflict}"
        
        # 阶段2分析
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
- **可信度**: {(stage2_analysis.get('credibility') or {}).get('level', 'unknown')}

---

*此版本为内部完整版，包含事实来源标注和系统痕迹*
"""
        
        return md
    
    @staticmethod
    def generate_public_version(
        news_title: str,
        news_source: str,
        stage2_analysis: Dict,
        images: List[str] = None
    ) -> str:
        """
        生成对外发布版（轻松幽默风格）
        
        特点：
        - 去掉所有系统痕迹
        - 轻松幽默的专栏风格
        - 结构自然流畅，无生硬小标题
        - 适合直接发布
        """
        images = images or []
        
        md = f"# {news_title}\n\n"
        
        # 导语
        if stage2_analysis.get('summary'):
            md += f"{stage2_analysis['summary']}\n\n"
        
        # 专家点评作为主体内容（AI生成的轻松幽默风格文章）
        if stage2_analysis.get('expert_opinion'):
            md += f"{stage2_analysis['expert_opinion']}\n\n"
        
        # 配图穿插（正文图片，从第1张开始）
        if images:
            md += f"![配图]({images[0]})\n\n"
        
        # 背景补充（如果有）
        if stage2_analysis.get('background'):
            md += f"{stage2_analysis['background']}\n\n"
        
        # 第二张配图（如果有）
        if len(images) > 1:
            md += f"![配图]({images[1]})\n\n"
        
        # 影响分析（如果有）
        if stage2_analysis.get('impact_analysis'):
            md += f"{stage2_analysis['impact_analysis']}\n\n"
        
        # 未来展望（如果有）
        if stage2_analysis.get('future_outlook'):
            md += f"{stage2_analysis['future_outlook']}\n\n"
        
        # 标签（简洁）
        if stage2_analysis.get('tags'):
            md += "---\n\n"
            md += ' '.join([f"#{t.replace(' ', '_')}" for t in stage2_analysis['tags'][:6]])
            md += "\n"
        
        return md


# 便捷函数
def generate_both_versions(
    news_title: str,
    news_source: str,
    stage1_facts: Dict,
    stage2_analysis: Dict,
    sensitivity_info: Dict,
    images: List[str] = None
) -> Dict[str, str]:
    """同时生成两个版本"""
    formatter = OutputFormatter()
    
    return {
        "internal": formatter.generate_internal_version(
            news_title, news_source, stage1_facts, stage2_analysis, sensitivity_info, images
        ),
        "public": formatter.generate_public_version(
            news_title, news_source, stage2_analysis, images
        )
    }


if __name__ == "__main__":
    # 测试
    test_stage1 = {
        "basic_facts": {
            "event_date": "2026-04-13",
            "location": "Washington D.C.",
            "key_figures": [{"name": "Donald Trump", "title": "President", "role_in_event": "Host"}],
            "main_event": "Meeting with Israeli PM"
        },
        "timeline": [{"date": "2026-04-13", "event": "Meeting held", "source": "White House"}],
        "claims_verification": [],
        "sources": [{"type": "官方", "name": "White House", "credibility": "high"}],
        "conflicting_info": []
    }
    
    test_stage2 = {
        "summary": "Trump meets Netanyahu to discuss Middle East peace.",
        "key_points": ["Point 1", "Point 2"],
        "background": "Background info...",
        "impact_analysis": "Impact analysis...",
        "expert_opinion": "Expert opinion...",
        "tags": ["US", "Israel", "Politics"]
    }
    
    test_sensitivity = {"level": "high", "reason": "Political meeting"}
    
    versions = generate_both_versions(
        "Test News", "BBC", test_stage1, test_stage2, test_sensitivity
    )
    
    print("=== 内部版 ===")
    print(versions["internal"][:500])
    print("\n=== 对外版 ===")
    print(versions["public"][:500])
