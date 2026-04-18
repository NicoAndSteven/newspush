"""
两阶段分析系统
阶段1: Fact-Checker - 提取纯事实清单 + 时间线 + 来源
阶段2: 生成 - 基于事实清单生成正文
"""
import json
from typing import Dict, List, Optional
from datetime import datetime

from ai_processor.deep_analyzer import DeepNewsAnalyzer, AnalysisDepth, DeepAnalysisResult
from utils.fact_anchor import get_fact_anchor_prompt


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

【任务】作为事实核查员，请从以下新闻中提取纯事实信息。

当前时间: {current_time}

新闻标题: {title}
新闻内容: {content}

请输出以下 JSON 格式的事实清单:
{{
    "basic_facts": {{
        "event_date": "事件发生的具体日期（YYYY-MM-DD格式，不确定则标注'未明确'）",
        "location": "事件发生的地点",
        "key_figures": [
            {{
                "name": "人物姓名",
                "title": "当前准确职位（必须对照事实锚点）",
                "role_in_event": "在事件中的角色"
            }}
        ],
        "main_event": "核心事件描述（1-2句话，只陈述事实）"
    }},
    "timeline": [
        {{
            "date": "时间点",
            "event": "具体事件",
            "source": "信息来源"
        }}
    ],
    "claims_verification": [
        {{
            "claim": "新闻中的主张/说法",
            "verified": true/false/null,
            "evidence": "验证依据",
            "confidence": "high/medium/low"
        }}
    ],
    "sources": [
        {{
            "type": "官方/媒体/专家/匿名",
            "name": "来源名称",
            "credibility": "high/medium/low"
        }}
    ],
    "conflicting_info": [
        "发现的矛盾点或存疑信息"
    ],
    "notes": "其他重要说明"
}}

【要求】
1. 只输出可验证的事实，不输出观点
2. 所有日期、人名、职位必须准确（对照事实锚点）
3. 如果新闻内容与事实锚点矛盾，标注矛盾并优先采信事实锚点
4. 不确定的信息标注"存疑"，不要猜测
5. 时间线按时间顺序排列
"""
        
        try:
            # 使用轻量级调用获取事实
            extra_body = {"enable_search": True} if self.analyzer.enable_search else {}
            
            response = self.analyzer.client.chat.completions.create(
                model="qwen3.6-flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # 低温度，更确定性的输出
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
        
        prompt = f"""【重要】当前时间: {current_time}

【风格要求】
参考《纽约时报》评论或《经济学人》分析风格：
- 专业、克制、平衡
- 多数据支撑，少用抽象形容词
- 避免戏剧化比喻
- 避免"深刻洞见""十字路口""历史转折"等模板句式
- 多用具体事实说话

【平衡性要求】
- 对于政治/宗教等敏感话题，必须呈现至少两方合理逻辑
- 不要只呈现单一视角
- 标注不同观点的信息来源

【反AI味指令】
- 禁止使用"值得注意的是""令人深思的是""无疑"等套话
- 禁止使用过多的形容词堆砌
- 每个论点必须有具体事实或数据支撑

【任务】基于以下已核实的事实清单，生成{depth_prompt[depth]}。

原始新闻标题: {title}
原始新闻内容: {content}

【已核实的事实清单】
{facts_text}

【要求】
1. 必须基于上述事实清单，不要添加未核实信息
2. 如果事实清单中有"存疑"或"矛盾"标注，在分析中明确指出
3. 遵循风格要求，写出专业、克制的分析
4. 确保平衡性，呈现多方观点

请按以下 JSON 格式返回:
{{
    "summary": "导语（一句话，包含核心事实）",
    "content_type": "breaking/tech/finance/social/politics",
    "importance_level": "重要性等级：critical（重大事件）/important（重要新闻）/normal（普通新闻）",
    "key_points": ["3-5个核心要点，每个必须有数据支撑"],
    "background": "背景（聚焦当前，历史脉络点到为止）",
    "impact_analysis": "影响分析（具体，含连锁反应）",
    "future_outlook": "展望（最可能+最坏场景）",
    "unique_angle": "独特视角（具体、有新意）",
    "controversial_aspects": ["争议点（呈现多方逻辑）"],
    "expert_opinion": "专家点评（专业克制风格）",
    "commentary": "根据重要性等级生成点评文章（critical:2000-3000字深度分析，important:800-1500字标准分析，normal:200-400字简洁概括）",
    "tags": ["5-8个标签"],
    "sentiment": "positive/negative/neutral/mixed",
    "urgency_level": 1-10,
    "credibility": {{
        "level": "high/medium/low",
        "issues": ["事实清单中标注的矛盾点"],
        "notes": "基于已核实事实"
    }}
}}
"""
        
        try:
            extra_body = {"enable_search": True} if self.analyzer.enable_search else {}
            
            response = self.analyzer.client.chat.completions.create(
                model="qwen3.6-flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
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
