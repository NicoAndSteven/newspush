import os
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

class AnalysisDepth(Enum):
    LIGHT = "light"           # 简要分析
    STANDARD = "standard"     # 标准分析
    DEEP = "deep"             # 深度分析

class ContentType(Enum):
    NEWS = "news"
    COMMENTARY = "commentary"
    ANALYSIS = "analysis"
    OPINION = "opinion"

@dataclass
class DeepAnalysisResult:
    # 基础信息
    title: str
    summary: str
    content_type: str
    
    # 深度分析
    key_points: List[str]
    background: str
    impact_analysis: str
    future_outlook: str
    
    # 观点与角度
    unique_angle: str
    controversial_aspects: List[str]
    expert_opinion: str
    
    # 多平台适配内容
    platform_contents: Dict[str, str]
    
    # 元数据
    tags: List[str]
    sentiment: str
    urgency_level: int  # 1-10
    target_audience: List[str]
    suggested_platforms: List[str]
    
    # 视频相关（保留）
    is_video_worthy: bool
    video_hooks: List[str]
    video_script: Optional[Dict] = None
    
    # 可信度评估
    credibility: Dict = None  # {"level": "high/medium/low", "issues": [], "notes": ""}
    
    # 核心事实清单
    core_facts: Dict = None  # {"when": "", "where": "", "who": [], "what": "", "key_disputes": []}
    
    def to_dict(self):
        return asdict(self)

class DeepNewsAnalyzer:
    def __init__(self, provider: str = "openai", api_key: str = None, enable_search: bool = True):
        self.provider = provider
        self.api_key = api_key
        self.enable_search = enable_search
        self.client = None
        self.init_client()
    
    def init_client(self):
        print(f"  [DEBUG] 初始化 AI 客户端: provider={self.provider}, api_key={'已设置' if self.api_key else '未设置'}")
        
        if not self.api_key:
            print("  [错误] API Key 为空，无法初始化客户端")
            return
        
        if self.provider == "openai":
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                print("  [DEBUG] OpenAI 客户端初始化成功")
            except ImportError as e:
                print(f"  [错误] OpenAI package 未安装: {e}")
            except Exception as e:
                print(f"  [错误] OpenAI 客户端初始化失败: {e}")
        elif self.provider == "anthropic":
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                print("  [DEBUG] Anthropic 客户端初始化成功")
            except ImportError as e:
                print(f"  [错误] Anthropic package 未安装: {e}")
            except Exception as e:
                print(f"  [错误] Anthropic 客户端初始化失败: {e}")
        elif self.provider == "dashscope":
            # 阿里云百炼 API
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                )
                print("  [DEBUG] 阿里云百炼客户端初始化成功")
            except ImportError as e:
                print(f"  [错误] OpenAI package 未安装: {e}")
            except Exception as e:
                print(f"  [错误] 阿里云百炼客户端初始化失败: {e}")
    
    def analyze_news_deep(self, title: str, content: str, depth: AnalysisDepth = AnalysisDepth.DEEP, enable_fact_check: bool = True) -> DeepAnalysisResult:
        """深度分析新闻，不限题材
        
        Args:
            title: 新闻标题
            content: 新闻内容
            depth: 分析深度
            enable_fact_check: 是否启用事实核查（已弃用，保留参数用于兼容）
        """
        
        # 检查客户端是否初始化成功
        if not self.client:
            print(f"  [错误] AI 客户端未初始化，请检查 API Key 配置")
            return self._create_fallback_result(title, content)
        
        current_time = datetime.now().strftime("%Y年%m月%d日")
        
        depth_prompt = {
            AnalysisDepth.LIGHT: "提供简要分析，重点在核心观点",
            AnalysisDepth.STANDARD: "提供标准分析，包括背景、影响和观点",
            AnalysisDepth.DEEP: "提供深度分析，挖掘背后逻辑、多角度观点、未来趋势"
        }
        
        prompt = f"""【重要提示】当前时间是 {current_time}。请基于此时间点进行分析。

【核心原则：具体、准确、有深度】
1. **具体性优先**：分析必须包含具体的事实细节（时间、地点、人物、数据），避免泛泛而谈
2. **称谓使用**：
   - 新闻原文中出现的人名和职位，应如实引用（如"黎巴嫩总统Aoun"、"以色列总理Netanyahu"）
   - 对于原文中模糊提及的实体（如"the group"），应结合上下文明确指出（如"普遍认为指真主党Hezbollah"）
   - 不要刻意回避人名或用"某人物""某组织"替代，这会降低文章信息量
3. **事实与观点分离**：
   - 核心要点和事实清单必须基于新闻原文
   - 背景分析和专家点评可以补充合理的背景知识，但需注明"根据公开信息"
   - 对于可能随时间变化的信息，使用"根据报道""截至当前"等限定语
4. **信息密度**：每段话都应有实质内容，避免"正确但空洞"的表述
5. **时效性优先**：背景分析应聚焦当前局势（最近1-2年），历史脉络点到为止，不要过度追溯久远历史
6. **风险分析尖锐化**：分析潜在风险时，要具体说明升级路径、连锁反应、最坏场景，而非泛泛而谈

请对以下新闻进行{depth_prompt[depth]}：

标题：{title}
内容：{content}

请按以下 JSON 格式返回深度分析结果：
{{
    "core_facts": {{
        "when": "事件发生的时间（具体日期，非模糊表述）",
        "where": "事件发生的地点",
        "who": ["关键人物及其身份（姓名+职位，如'黎巴嫩总统Joseph Aoun'）"],
        "what": "核心事件是什么（1-2句话，包含具体细节）",
        "key_disputes": ["各方的核心分歧点（具体而非抽象）"]
    }},
    
    "summary": "一句话总结新闻核心（包含具体人物和事件，作为文章导语）",
    "content_type": "内容类型：breaking突发/tech科技/finance财经/social社会/entertainment娱乐/politics政治/lifestyle生活",
    
    "key_points": ["3-5个核心要点（每个要点必须包含具体事实，不能只是抽象概括）"],
    "background": "事件背景（聚焦当前局势和最近发展，历史脉络简要点明即可，不少于200字）",
    "impact_analysis": "影响分析（具体说明对哪些方面有影响，用数据或案例支撑，包括潜在连锁反应）",
    "future_outlook": "未来趋势预测（基于当前局势的具体预判，包括最可能和最坏两种场景）",
    
    "unique_angle": "独特的切入角度或观点（必须是具体的、有新意的，而非老生常谈）",
    "controversial_aspects": ["争议点（具体说明各方立场和分歧原因，包括潜在升级风险）"],
    "expert_opinion": "专家视角点评（结合具体事实进行深度分析，避免空洞的'弱国无外交'式套话）",
    
    "platform_contents": {{
        "wechat": "适合微信公众号的长文点评（800-1500字，包含具体事实和深度分析）",
        "xiaohongshu": "适合小红书的短文案（300-500字，带emoji，口语化）",
        "weibo": "适合微博的短评（200-300字，带话题标签）",
        "zhihu": "适合知乎的深度分析（1000-2000字，结构化，有数据支撑）",
        "douyin": "适合抖音口播的文案（30-60秒，口语化，钩子开头）"
    }},
    
    "tags": ["5-8个标签"],
    "sentiment": "情感倾向：positive/negative/neutral/mixed",
    "urgency_level": "紧急程度 1-10",
    "target_audience": ["目标受众群体"],
    "suggested_platforms": ["推荐推送的平台"],
    
    "is_video_worthy": true/false,
    "video_hooks": ["3个视频开头钩子"],
    
    "credibility": {{
        "level": "high/medium/low",
        "issues": ["发现的事实问题"],
        "notes": "可信度说明"
    }}
}}

要求：
1. **具体性**：每个字段都必须包含具体信息，拒绝"某国""某组织""某人物"等模糊表述
2. **深度**：分析要有独到见解，避免正确但空洞的套话
3. **准确性**：人名、地名、数据等必须准确，不确定的加限定语
4. **信息密度**：每段话都有实质内容，读者读完后应清楚"到底发生了什么"
5. **时效性**：背景分析聚焦当前局势，历史脉络点到为止
6. **风险尖锐化**：分析风险时具体说明升级路径、连锁反应、最坏场景
"""
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8
                )
                result_text = response.choices[0].message.content
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}]
                )
                result_text = response.content[0].text
            elif self.provider == "dashscope":
                # 阿里云百炼 Qwen 模型
                # 开启联网搜索功能（如果配置允许）
                extra_body = {}
                if self.enable_search:
                    extra_body["enable_search"] = True
                
                response = self.client.chat.completions.create(
                    model="qwen3.6-plus",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8,
                    extra_body=extra_body
                )
                result_text = response.choices[0].message.content
            
            # 提取 JSON
            json_str = self._extract_json(result_text)
            result_json = json.loads(json_str)
            
            # 构建可信度信息
            credibility = result_json.get("credibility", {"level": "unknown", "issues": [], "notes": ""})
            
            # 提取核心事实
            core_facts = result_json.get("core_facts", {})
            
            return DeepAnalysisResult(
                title=title,
                summary=result_json.get("summary", ""),
                content_type=result_json.get("content_type", "news"),
                key_points=result_json.get("key_points", []),
                background=result_json.get("background", ""),
                impact_analysis=result_json.get("impact_analysis", ""),
                future_outlook=result_json.get("future_outlook", ""),
                unique_angle=result_json.get("unique_angle", ""),
                controversial_aspects=result_json.get("controversial_aspects", []),
                expert_opinion=result_json.get("expert_opinion", ""),
                platform_contents=result_json.get("platform_contents", {}),
                tags=result_json.get("tags", []),
                sentiment=result_json.get("sentiment", "neutral"),
                urgency_level=int(result_json.get("urgency_level", 5)),
                target_audience=result_json.get("target_audience", []),
                suggested_platforms=result_json.get("suggested_platforms", []),
                is_video_worthy=result_json.get("is_video_worthy", False),
                video_hooks=result_json.get("video_hooks", []),
                credibility=credibility,
                core_facts=core_facts
            )
            
        except Exception as e:
            print(f"Deep analysis error: {e}")
            return self._create_fallback_result(title, content)
    
    def _extract_json(self, text: str) -> str:
        """从文本中提取 JSON"""
        # 尝试找到 JSON 块
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            return text[start_idx:end_idx+1]
        
        return text
    
    def _create_fallback_result(self, title: str, content: str) -> DeepAnalysisResult:
        """创建备用结果"""
        return DeepAnalysisResult(
            title=title,
            summary=content[:100] + "..." if len(content) > 100 else content,
            content_type="news",
            key_points=[],
            background="",
            impact_analysis="",
            future_outlook="",
            unique_angle="",
            controversial_aspects=[],
            expert_opinion="",
            platform_contents={},
            tags=[],
            sentiment="neutral",
            urgency_level=5,
            target_audience=[],
            suggested_platforms=[],
            is_video_worthy=False,
            video_hooks=[]
        )
    
    def batch_analyze(self, news_items: List[Dict], depth: AnalysisDepth = AnalysisDepth.DEEP) -> List[DeepAnalysisResult]:
        """批量分析新闻"""
        results = []
        for item in news_items:
            result = self.analyze_news_deep(
                item.get("title", ""),
                item.get("description", ""),
                depth
            )
            results.append(result)
        return results
    
    def compare_news(self, news_items: List[Dict]) -> Dict:
        """对比分析多条新闻，找出关联和趋势"""
        news_text = "\n\n".join([f"标题：{item.get('title', '')}\n内容：{item.get('description', '')}" for item in news_items])
        
        prompt = f"""请对比分析以下{len(news_items)}条新闻，找出它们之间的关联：

{news_text}

请按以下 JSON 格式返回分析：
{{
    "common_themes": ["共同主题"],
    "trends": ["趋势分析"],
    "connections": ["新闻之间的关联"],
    "combined_angle": "综合分析角度",
    "recommended_focus": "最值得深入的话题"
}}
"""
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                result_text = response.choices[0].message.content
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                result_text = response.content[0].text
            else:
                return {}
            
            json_str = self._extract_json(result_text)
            return json.loads(json_str)
            
        except Exception as e:
            print(f"Compare news error: {e}")
            return {}

class CommentaryGenerator:
    """生成新闻点评内容"""
    
    def __init__(self, analyzer: DeepNewsAnalyzer):
        self.analyzer = analyzer
    
    def generate_commentary(self, analysis: DeepAnalysisResult, style: str = "balanced") -> str:
        """生成新闻点评"""
        
        # 检查分析器是否可用
        if not self.analyzer or not self.analyzer.client:
            print(f"  [错误] AI 客户端未初始化，无法生成点评")
            return ""
        
        style_prompt = {
            "balanced": "客观平衡，多角度分析",
            "critical": "批判性思维，质疑主流观点",
            "optimistic": "积极乐观，关注机会",
            "provocative": "观点鲜明，引发讨论",
            "storytelling": "讲故事风格，引人入胜"
        }
        
        prompt = f"""你是一个聪明幽默的国际新闻评论员，正在给朋友们讲新闻。请基于以下分析，写一篇轻松有趣、带点调侃的点评文章：

新闻标题：{analysis.title}
核心要点：{', '.join(analysis.key_points)}
背景：{analysis.background}
影响分析：{analysis.impact_analysis}
独特角度：{analysis.unique_angle}
争议点：{', '.join(analysis.controversial_aspects)}

【写作风格要求】
1. **语气轻松幽默**：像聪明朋友在吐槽国际新闻一样，可以适当讽刺和自嘲，但不要刻薄或低俗
2. **拒绝括号**：正文中尽量不用括号，能用破折号、冒号或直接融入句子就不用括号
3. **口语化表达**：避免"极限施压""切香肠战术""外交悖论""恶性循环""标志性""系统性"等严肃模板词汇，用生活化语言替代
4. **标题要吸引人**：开头第一句就是标题，要带点幽默、反讽或反转感，让人眼前一亮
5. **导语要有趣**：开头几句话要轻松有趣，让人想继续往下读
6. **结构自然流畅**：不要用"核心事实""深度分析""多方视角"等生硬小标题，让文章像专栏评论一样自然流动
7. **事实必须准确**：核心信息不能编造，但要用轻松的方式讲出来，不要板着脸严肃分析
8. **字数控制**：1000-1500字，和原文差不多长度
9. **直接点名**：不要用"某国""某组织""某人物"等模糊表述

【禁止事项】
- 不要用括号补充说明
- 不要用"值得注意的是""需要指出的是"等官腔
- 不要用"首先、其次、最后"等模板结构
- 不要用"这一事件标志着""具有里程碑意义"等套话

现在请开始写，直接输出文章正文，不要有任何前言或解释："""
        
        try:
            if self.analyzer.provider == "openai":
                response = self.analyzer.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8
                )
                return response.choices[0].message.content
            elif self.analyzer.provider == "anthropic":
                response = self.analyzer.client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=2500,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            elif self.analyzer.provider == "dashscope":
                # 阿里云百炼 Qwen 模型
                extra_body = {}
                if self.analyzer.enable_search:
                    extra_body["enable_search"] = True
                
                response = self.analyzer.client.chat.completions.create(
                    model="qwen3.6-plus",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8,
                    extra_body=extra_body
                )
                return response.choices[0].message.content
            else:
                return ""
        except Exception as e:
            print(f"Commentary generation error: {e}")
            return ""
    
    def generate_thread(self, analysis: DeepAnalysisResult, platform: str = "weibo") -> List[str]:
        """生成系列推文/帖子"""
        
        platform_config = {
            "weibo": {"count": 5, "length": 200},
            "twitter": {"count": 5, "length": 280},
            "xiaohongshu": {"count": 3, "length": 300}
        }
        
        config = platform_config.get(platform, {"count": 5, "length": 200})
        
        prompt = f"""基于以下新闻，生成{config['count']}条系列{platform}帖子：

标题：{analysis.title}
要点：{', '.join(analysis.key_points)}
独特角度：{analysis.unique_angle}

要求：
1. 每条{config['length']}字以内
2. 系列帖子要有连贯性
3. 第1条要吸引人
4. 最后一条要有互动引导
5. 适合{platform}平台风格

返回JSON格式：{{"posts": ["帖子1", "帖子2", ...]}}
"""
        
        try:
            if self.analyzer.provider == "openai":
                response = self.analyzer.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8
                )
                result_text = response.choices[0].message.content
            elif self.analyzer.provider == "anthropic":
                response = self.analyzer.client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}]
                )
                result_text = response.content[0].text
            elif self.analyzer.provider == "dashscope":
                # 阿里云百炼 Qwen 模型
                extra_body = {}
                if self.analyzer.enable_search:
                    extra_body["enable_search"] = True
                
                response = self.analyzer.client.chat.completions.create(
                    model="qwen3.6-plus",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8,
                    extra_body=extra_body
                )
                result_text = response.choices[0].message.content
            else:
                return []
            
            json_str = self.analyzer._extract_json(result_text)
            result_json = json.loads(json_str)
            return result_json.get("posts", [])
            
        except Exception as e:
            print(f"Thread generation error: {e}")
            return []

if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        analyzer = DeepNewsAnalyzer("openai", api_key)
        
        test_news = {
            "title": "SpaceX 星舰第四次试飞成功，人类离火星又近一步",
            "description": "SpaceX 的星舰火箭在第四次试飞中成功完成所有预定目标，助推器成功回收，飞船按计划溅落。这是人类航天史上的重要里程碑..."
        }
        
        result = analyzer.analyze_news_deep(test_news["title"], test_news["description"])
        
        print(f"深度分析结果：")
        print(f"  类型：{result.content_type}")
        print(f"  总结：{result.summary}")
        print(f"  核心要点：{result.key_points}")
        print(f"  独特角度：{result.unique_angle}")
        print(f"\n  平台内容：")
        for platform, content in result.platform_contents.items():
            print(f"\n  [{platform}]:")
            print(f"    {content[:200]}...")
    else:
        print("请设置 OPENAI_API_KEY 环境变量")
