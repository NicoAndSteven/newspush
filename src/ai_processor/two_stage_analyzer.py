"""
两阶段分析系统
阶段1: Fact-Checker - 提取纯事实清单 + 时间线 + 来源
阶段2: 生成 - 基于事实清单生成正文
"""
import json
import random
from typing import Dict, List, Optional
from datetime import datetime

from ai_processor.deep_analyzer import DeepNewsAnalyzer, AnalysisDepth, DeepAnalysisResult, get_random_temperature
from utils.fact_anchor import get_fact_anchor_prompt


def get_random_temperature_for_facts(min_temp: float = 0.3, max_temp: float = 0.5) -> float:
    """生成用于事实核查的随机 temperature（较低，更准确）"""
    return round(random.uniform(min_temp, max_temp), 2)


class TwoStageAnalyzer:
    """两阶段分析器"""
    
    def __init__(self, analyzer: DeepNewsAnalyzer):
        self.analyzer = analyzer
    
    def analyze(self, title: str, content: str, depth: AnalysisDepth = AnalysisDepth.DEEP) -> Dict:
        """
        执行两阶段分析
        
        Returns:
            {
                "stage1_facts": 阶段1事实清单,
                "stage2_analysis": 阶段2深度分析,
                "combined_result": 合并后的最终结果
            }
        """
        print("  [两阶段分析] 开始...")
        
        # 阶段1: Fact-Checker - 提取事实
        print("  [阶段1] 提取事实清单...")
        stage1_result = self._stage1_fact_check(title, content)
        
        # 阶段2: 基于事实生成分析
        print("  [阶段2] 生成深度分析...")
        stage2_result = self._stage2_generate(title, content, stage1_result, depth)
        
        return {
            "stage1_facts": stage1_result,
            "stage2_analysis": stage2_result,
            "combined_result": self._combine_results(stage1_result, stage2_result)
        }
    
    def _stage1_fact_check(self, title: str, content: str) -> Dict:
        """
        阶段1: Fact-Checker
        输出纯事实清单 + 时间线 + 来源
        """
        # 获取事实锚点
        fact_anchor = get_fact_anchor_prompt(title, content)
        
        current_time = datetime.now().strftime("%Y年%m月%d日")
        
        prompt = f"""{fact_anchor}

当前时间: {current_time}

你是一位事实核查员，请从以下新闻中提取事实信息。

新闻标题: {title}
新闻内容: {content}

请返回 JSON 格式的事实清单：
- basic_facts: 基本信息（event_date, location, key_figures, main_event）
- timeline: 时间线（date, event, source）
- claims_verification: 主张验证（claim, verified, evidence, confidence）
- sources: 信息来源（type, name, credibility）
- conflicting_info: 矛盾点
- notes: 其他说明

要求：
1. 只输出可验证的事实，不输出观点
2. 不确定的信息标注"存疑"
3. 时间线按时间顺序排列

请直接输出 JSON 结果："""
        
        try:
            # 使用轻量级调用获取事实
            extra_body = {"enable_search": True} if self.analyzer.enable_search else {}
            
            response = self.analyzer.client.chat.completions.create(
                model="qwen3.6-flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=get_random_temperature_for_facts(0.3, 0.5),
                extra_body=extra_body
            )
            
            result_text = response.choices[0].message.content
            json_str = self.analyzer._extract_json(result_text)
            return json.loads(json_str)
            
        except Exception as e:
            print(f"  [阶段1错误] {e}")
            return self._create_fallback_stage1(title, content)
    
    def _stage2_generate(self, title: str, content: str, stage1_facts: Dict, depth: AnalysisDepth) -> DeepAnalysisResult:
        """
        阶段2: 基于事实生成深度分析
        """
        # 将阶段1事实转换为文本
        facts_text = json.dumps(stage1_facts, ensure_ascii=False, indent=2)
        
        current_time = datetime.now().strftime("%Y年%m月%d日")
        
        depth_prompt = {
            AnalysisDepth.LIGHT: "提供简要分析",
            AnalysisDepth.STANDARD: "提供标准分析",
            AnalysisDepth.DEEP: "提供深度分析"
        }
        
        prompt = f"""当前时间: {current_time}

你是一位资深新闻评论员，请基于以下已核实的事实清单进行深度分析。

原始新闻标题: {title}
原始新闻内容: {content}

【已核实的事实清单】
{facts_text}

请返回 JSON 格式的分析结果，包含以下字段：
- summary: 导语（一句话核心事实）
- content_type: 内容类型（breaking/tech/finance/sports/entertainment/politics）
- importance_level: 重要性（critical/important/normal）
- key_points: 3-5个核心要点
- background: 背景信息
- impact_analysis: 影响分析
- future_outlook: 未来展望
- unique_angle: 独特视角
- controversial_aspects: 争议点
- expert_opinion: 专家点评
- commentary: 完整的新闻点评文章（公众号风格）
- tags: 标签列表
- sentiment: 情感倾向
- urgency_level: 紧急程度1-10
- credibility: 可信度评估

【点评文章字数规则】
- critical（重大事件）：800-1500字
- important（重要新闻）：600-1000字
- normal（普通新闻）：200-400字

【公众号风格准则】
- 像朋友聊天一样娓娓道来，理性中带温度
- 开头用场景、疑问或感叹快速切入
- 中间把事实、背景、影响自然穿插叙述
- 结尾轻度总结 + 一个开放式问题
- 段落要短，句子长短交错

【绝对禁止】
1. 不要出现任何小标题
2. 不要用编号列表
3. 不要出现"核心要点""市场背景"等报告式标签
4. 不要用"首先、其次、最后""一方面、另一方面"
5. 不要用"可能的场景是""未来可能会""值得关注的是"
6. 不要用"这表明""这说明""不难看出""值得注意的是"
7. 不要用"引发了广泛关注""具有重要影响"
8. 不要用括号补充说明

【事实原则】
必须基于事实清单，不要添加未核实信息。

输出格式：先给2-3个标题选项，然后空一行输出正文。

请直接输出 JSON 结果："""
        
        try:
            extra_body = {"enable_search": True} if self.analyzer.enable_search else {}
            
            response = self.analyzer.client.chat.completions.create(
                model="qwen3.6-flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=get_random_temperature(0.7, 1.0),
                extra_body=extra_body
            )
            
            result_text = response.choices[0].message.content
            json_str = self.analyzer._extract_json(result_text)
            result_json = json.loads(json_str)
            
            # 转换为 DeepAnalysisResult
            return DeepAnalysisResult(
                title=title,
                summary=result_json.get("summary", ""),
                content_type=result_json.get("content_type", "news"),
                importance_level=result_json.get("importance_level", "normal"),
                key_points=result_json.get("key_points", []),
                background=result_json.get("background", ""),
                impact_analysis=result_json.get("impact_analysis", ""),
                future_outlook=result_json.get("future_outlook", ""),
                unique_angle=result_json.get("unique_angle", ""),
                controversial_aspects=result_json.get("controversial_aspects", []),
                expert_opinion=result_json.get("expert_opinion", ""),
                platform_contents={},
                tags=result_json.get("tags", []),
                sentiment=result_json.get("sentiment", "neutral"),
                urgency_level=int(result_json.get("urgency_level", 5)),
                target_audience=[],
                suggested_platforms=[],
                is_video_worthy=False,
                video_hooks=[],
                credibility=result_json.get("credibility", {"level": "medium", "issues": [], "notes": ""}),
                core_facts=stage1_facts.get("basic_facts", {}),
                commentary=result_json.get("commentary", "")
            )
            
        except Exception as e:
            print(f"  [阶段2错误] {e}")
            # 回退到原始分析方法
            return self.analyzer.analyze_news_deep(title, content, depth, enable_fact_check=False)
    
    def _combine_results(self, stage1_facts: Dict, stage2_analysis: DeepAnalysisResult) -> Dict:
        """合并两个阶段的结果"""
        return {
            "title": stage2_analysis.title,
            "summary": stage2_analysis.summary,
            "content_type": stage2_analysis.content_type,
            "key_points": stage2_analysis.key_points,
            "background": stage2_analysis.background,
            "impact_analysis": stage2_analysis.impact_analysis,
            "future_outlook": stage2_analysis.future_outlook,
            "unique_angle": stage2_analysis.unique_angle,
            "controversial_aspects": stage2_analysis.controversial_aspects,
            "expert_opinion": stage2_analysis.expert_opinion,
            "tags": stage2_analysis.tags,
            "sentiment": stage2_analysis.sentiment,
            "urgency_level": stage2_analysis.urgency_level,
            "credibility": stage2_analysis.credibility,
            "core_facts": stage2_analysis.core_facts,
            "stage1_raw": stage1_facts,  # 保留原始事实清单供参考
        }
    
    def _create_fallback_stage1(self, title: str, content: str) -> Dict:
        """创建回退的阶段1结果"""
        return {
            "basic_facts": {
                "event_date": "未明确",
                "location": "未明确",
                "key_figures": [],
                "main_event": content[:200] if content else title
            },
            "timeline": [],
            "claims_verification": [],
            "sources": [],
            "conflicting_info": ["事实核查阶段失败，使用原始内容"],
            "notes": "回退模式"
        }
