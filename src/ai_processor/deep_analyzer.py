import os
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import time
import httpx

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
    importance_level: str = "normal"  # critical/important/normal
    
    # 深度分析
    key_points: List[str] = None
    background: str = ""
    impact_analysis: str = ""
    future_outlook: str = ""
    
    # 观点与角度
    unique_angle: str = ""
    controversial_aspects: List[str] = None
    expert_opinion: str = ""
    
    # 多平台适配内容
    platform_contents: Dict[str, str] = None
    
    # 元数据
    tags: List[str] = None
    sentiment: str = "neutral"
    urgency_level: int = 5
    target_audience: List[str] = None
    suggested_platforms: List[str] = None
    
    # 视频相关（保留）
    is_video_worthy: bool = False
    video_hooks: List[str] = None
    video_script: Optional[Dict] = None
    
    # 可信度评估
    credibility: Dict = None  # {"level": "high/medium/low", "issues": [], "notes": ""}
    
    # 核心事实清单
    core_facts: Dict = None  # {"when": "", "where": "", "who": [], "what": "", "key_disputes": []}
    
    # 点评文章（合并调用时使用）
    commentary: str = ""
    
    def __post_init__(self):
        if self.key_points is None:
            self.key_points = []
        if self.controversial_aspects is None:
            self.controversial_aspects = []
        if self.platform_contents is None:
            self.platform_contents = {}
        if self.tags is None:
            self.tags = []
        if self.target_audience is None:
            self.target_audience = []
        if self.suggested_platforms is None:
            self.suggested_platforms = []
        if self.video_hooks is None:
            self.video_hooks = []
    
    def to_dict(self):
        return asdict(self)

class DeepNewsAnalyzer:
    def __init__(self, provider: str = "openai", api_key: str = None, enable_search: bool = True, model: str = None):
        self.provider = provider
        self.api_key = api_key
        self.enable_search = enable_search
        self.model = model
        self.client = None
        self.init_client()
    
    def init_client(self):
        print(f"  [DEBUG] 初始化 AI 客户端: provider={self.provider}, api_key={'已设置' if self.api_key else '未设置'}, model={self.model}")
        
        if not self.api_key:
            print("  [错误] API Key 为空，无法初始化客户端")
            return
        
        if self.provider == "openai":
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                self.model = self.model or "gpt-4o-mini"
                print(f"  [DEBUG] OpenAI 客户端初始化成功，模型: {self.model}")
            except ImportError as e:
                print(f"  [错误] OpenAI package 未安装: {e}")
            except Exception as e:
                print(f"  [错误] OpenAI 客户端初始化失败: {e}")
        elif self.provider == "openrouter":
            # OpenRouter API（兼容 OpenAI 格式）
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://openrouter.ai/api/v1"
                )
                self.model = self.model or "openai/gpt-4o-mini"
                print(f"  [DEBUG] OpenRouter 客户端初始化成功，模型: {self.model}")
            except ImportError as e:
                print(f"  [错误] OpenAI package 未安装: {e}")
            except Exception as e:
                print(f"  [错误] OpenRouter 客户端初始化失败: {e}")
        elif self.provider == "anthropic":
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                self.model = self.model or "claude-3-opus-20240229"
                print(f"  [DEBUG] Anthropic 客户端初始化成功，模型: {self.model}")
            except ImportError as e:
                print(f"  [错误] Anthropic package 未安装: {e}")
            except Exception as e:
                print(f"  [错误] Anthropic 客户端初始化失败: {e}")
        elif self.provider == "dashscope":
            # 阿里云百炼 API
            try:
                from openai import OpenAI
                import httpx
                # 增加超时时间，避免 SSL 连接中断
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    timeout=httpx.Timeout(120.0, connect=60.0)
                )
                self.model = self.model or "qwen3.6-flash"
                print(f"  [DEBUG] 阿里云百炼客户端初始化成功，模型: {self.model}")
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
    
    "importance_level": "重要性等级：critical（重大事件，如战争、灾难、重大政策）/important（重要新闻，如经济数据、外交动态）/normal（普通新闻，如日常社会事件）",
    
    "key_points": ["3-5个核心要点（每个要点必须包含具体事实，不能只是抽象概括）"],
    "background": "事件背景（聚焦当前局势和最近发展，历史脉络简要点明即可）",
    "impact_analysis": "影响分析（具体说明对哪些方面有影响，用数据或案例支撑，包括潜在连锁反应）",
    "future_outlook": "未来趋势预测（基于当前局势的具体预判，包括最可能和最坏两种场景）",
    
    "unique_angle": "独特的切入角度或观点（必须是具体的、有新意的，而非老生常谈）",
    "controversial_aspects": ["争议点（具体说明各方立场和分歧原因，包括潜在升级风险）"],
    "expert_opinion": "专家视角点评（结合具体事实进行深度分析，避免空洞的'弱国无外交'式套话）",
    
    "commentary": "根据新闻重要性生成点评文章（见下方篇幅和风格要求）",
    
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

【点评文章的篇幅和风格要求】

**按新闻类型决定篇幅和风格**：

1. **娱乐新闻**（entertainment/lifestyle）：
   - 篇幅：200-400字，简洁轻快
   - 风格：像朋友聊天一样，轻松有趣
   - 内容：事件经过 + 明星动态 + 有趣细节
   - 不要深度分析，不要严肃评论，直接报道就好
   
2. **体育新闻**（sports）：
   - 篇幅：300-500字，赛事报道风格
   - 风格：专业但热情，像体育解说
   - 内容：比赛结果 + 关键时刻 + 球员表现
   - 聚焦赛事本身，简洁有力
   
3. **科技新闻**（tech）：
   - 篇幅：600-1000字，深度技术解读
   - 风格：专业易懂，解释技术价值
   - 内容：技术突破 + 产品亮点 + 行业影响 + 未来趋势
   - 可以适度追溯技术发展脉络，让普通人看懂
   
4. **财经新闻**（finance）：
   - 篇幅：600-1000字，深度财经解读
   - 风格：专业严谨，数据说话
   - 内容：核心数据 + 市场影响 + 投资启示 + 行业趋势
   - 可以适度引用历史案例
   
5. **时政新闻**（politics）：
   - 篇幅：300-500字，客观简洁
   - 风格：客观呈现，不过度解读
   - 内容：核心事实 + 主要立场 + 直接影响
   - 避免主观评论和过多历史背景
   
6. **突发新闻**（breaking）：
   - 篇幅：400-600字，快速准确
   - 风格：信息优先，简洁有力
   - 内容：核心事实 + 最新进展 + 直接影响
   - 避免过度分析和背景追溯
   
7. **严肃事件**（战争/灾难/伤亡）：
   - 篇幅：400-600字，客观严谨
   - 风格：尊重事实，不过度分析
   - 内容：核心事实 + 直接影响 + 后续关注
   - 体现对事件的尊重，避免猜测
   
8. **一般新闻**（其他）：
   - 篇幅：400-600字，标准报道
   - 风格：专业平易，有观点但不夸张
   - 内容：核心事实 + 背景补充 + 简要分析

**通用禁止事项**：
- 不要用括号补充说明
- 不要用"值得注意的是""需要指出的是"等官腔
- 不要用"首先、其次、最后"等模板结构
- 不要用"这一事件标志着""具有里程碑意义"等套话
- 不要用"某国""某组织""某人物"等模糊表述

**严格禁止的模板化表达**：
1. 禁止结尾套话："可能的场景是""未来可能会""值得关注的是""让我们拭目以待"
2. 禁止官腔："这表明""这说明""不难看出""不难发现"
3. 禁止模板结构："一方面、另一方面""从...角度来看"
4. 禁止空洞套话："引发了广泛关注""具有重要影响""影响深远"

**正确的写法**：
- 直接表达观点，不要铺垫
- 有结论就直接说，不要用"可能""也许"
- 结尾要自然收束，不要强行升华
- 像专业记者写新闻稿一样，简洁有力

要求：
1. **具体性**：每个字段都必须包含具体信息
2. **准确性**：人名、地名、数据等必须准确，不确定的加限定语
3. **信息密度**：每段话都有实质内容
4. **时效性**：背景分析聚焦当前局势，历史脉络点到为止
"""
        
        try:
            max_retries = 5  # 增加重试次数
            retry_delay = 10  # 增加初始延迟
            
            for attempt in range(max_retries):
                try:
                    print(f"    [API] 正在调用 {self.provider} API（尝试 {attempt + 1}/{max_retries}），模型: {self.model}...")
                    
                    if self.provider in ["openai", "openrouter"]:
                        # OpenAI 和 OpenRouter 使用相同的 API 格式
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.8
                        )
                        result_text = response.choices[0].message.content
                    elif self.provider == "anthropic":
                        response = self.client.messages.create(
                            model=self.model,
                            max_tokens=4000,
                            messages=[{"role": "user", "content": prompt}]
                        )
                        result_text = response.content[0].text
                    elif self.provider == "dashscope":
                        # 阿里云百炼 Qwen 模型
                        extra_body = {}
                        if self.enable_search:
                            extra_body["enable_search"] = True
                        
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.8,
                            extra_body=extra_body
                        )
                        result_text = response.choices[0].message.content
                    
                    print(f"    [API] API 调用成功")
                    break  # 成功则跳出重试循环
                    
                except Exception as api_error:
                    if attempt < max_retries - 1:
                        print(f"    [警告] API 调用失败: {api_error}，{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                    else:
                        raise api_error
            
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
                importance_level=result_json.get("importance_level", "normal"),
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
                core_facts=core_facts,
                commentary=result_json.get("commentary", "")  # 合并调用时直接返回点评
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
        """生成新闻点评（根据新闻类型自动选择风格和篇幅）"""
        
        if not self.analyzer or not self.analyzer.client:
            print(f"  [错误] AI 客户端未初始化，无法生成点评")
            return ""
        
        content_type = analysis.content_type
        
        type_config = {
            "entertainment": {
                "min": 200, "max": 400,
                "style": "轻松有趣，像朋友聊天",
                "focus": "事件经过 + 明星动态 + 有趣细节",
                "style_guide": """【风格：轻松有趣】
像聪明朋友在聊天一样讲述：
- 轻松幽默但不低俗
- 直接报道事件，不要深度分析
- 可以适当调侃
- 让人读起来轻松愉快"""
            },
            "lifestyle": {
                "min": 200, "max": 400,
                "style": "轻松有趣，像朋友聊天",
                "focus": "事件经过 + 有趣细节",
                "style_guide": """【风格：轻松有趣】
像聪明朋友在聊天一样讲述：
- 轻松幽默但不低俗
- 直接报道事件，不要深度分析
- 让人读起来轻松愉快"""
            },
            "sports": {
                "min": 300, "max": 500,
                "style": "专业热情，像体育解说",
                "focus": "比赛结果 + 关键时刻 + 球员表现",
                "style_guide": """【风格：体育解说】
像体育解说员一样热情专业：
- 聚焦赛事本身，简洁有力
- 突出关键时刻和精彩表现
- 专业但易懂
- 不要过度分析背景"""
            },
            "tech": {
                "min": 600, "max": 1000,
                "style": "专业易懂，技术解读",
                "focus": "技术突破 + 产品亮点 + 行业影响 + 未来趋势",
                "style_guide": """【风格：技术解读】
深度解读技术新闻：
- 解释技术是什么、为什么重要
- 用通俗语言解释专业概念
- 分析技术价值和行业影响
- 展望未来发展趋势
- 可以适度追溯技术发展脉络"""
            },
            "finance": {
                "min": 600, "max": 1000,
                "style": "专业严谨，数据说话",
                "focus": "核心数据 + 市场影响 + 投资启示 + 行业趋势",
                "style_guide": """【风格：财经解读】
深度解读财经新闻：
- 数据说话，聚焦关键信息
- 分析市场影响和投资启示
- 探讨行业趋势和未来走向
- 语言严谨但不晦涩
- 可以适度引用历史案例"""
            },
            "politics": {
                "min": 300, "max": 500,
                "style": "客观简洁，事实报道",
                "focus": "核心事实 + 主要立场 + 直接影响",
                "style_guide": """【风格：客观简洁】
简洁客观的政治报道：
- 聚焦核心事实，不过度解读
- 客观呈现各方立场
- 说明直接影响即可
- 避免主观评论和猜测
- 不要追溯过多历史背景"""
            },
            "breaking": {
                "min": 400, "max": 600,
                "style": "快速准确，信息优先",
                "focus": "核心事实 + 最新进展 + 直接影响",
                "style_guide": """【风格：突发新闻】
快速传递核心信息：
- 聚焦事实，信息密度高
- 简洁有力，不拖泥带水
- 说明最新进展和直接影响
- 避免过度分析和背景追溯"""
            }
        }
        
        serious_keywords = ["战争", "冲突", "灾难", "死亡", "伤亡", "袭击", "恐怖", "危机"]
        is_serious = (
            any(kw in analysis.title for kw in serious_keywords) or
            any(kw in analysis.summary for kw in serious_keywords) or
            analysis.urgency_level >= 8
        )
        
        if is_serious and content_type not in ["entertainment", "lifestyle", "sports", "tech", "finance"]:
            config = {
                "min": 400, "max": 600,
                "style": "客观严谨",
                "focus": "核心事实 + 直接影响 + 后续关注",
                "style_guide": """【风格：客观严谨】
客观报道严肃事件：
- 聚焦事实，不过度分析
- 客观呈现事件经过
- 说明直接影响
- 体现对事件的尊重
- 避免猜测和主观评论"""
            }
        elif content_type in type_config:
            config = type_config[content_type]
        else:
            config = {
                "min": 400, "max": 600,
                "style": "专业平易",
                "focus": "核心事实 + 背景补充 + 简要分析",
                "style_guide": """【风格：专业平易】
专业但平易近人的报道：
- 可以适度比喻帮助理解
- 保持客观但有观点
- 避免过度娱乐化
- 语言简洁有力"""
            }
        
        prompt = f"""请基于以下分析，写一篇新闻点评文章：

新闻标题：{analysis.title}
内容类型：{content_type}
字数要求：{config['min']}-{config['max']}字
核心要点：{', '.join(analysis.key_points[:3])}
背景：{analysis.background}
影响分析：{analysis.impact_analysis}
独特角度：{analysis.unique_angle}
争议点：{', '.join(analysis.controversial_aspects)}

{config['style_guide']}

【写作规范】
1. **结构自然流畅**：不要用"核心事实""深度分析"等生硬小标题
2. **事实必须准确**：核心信息不能编造
3. **直接点名**：不要用"某国""某组织""某人物"等模糊表述
4. **信息密度**：每段话都有实质内容

【严格禁止的模板化表达】
以下表达方式严格禁止，会让文章显得机械、模板化：

1. 禁止结尾套话：
   - "可能的场景是..."
   - "未来可能会..."
   - "值得关注的是..."
   - "这一事件的影响将持续..."
   - "让我们拭目以待..."
   - "时间会给出答案..."

2. 禁止官腔：
   - "值得注意的是""需要指出的是"
   - "这表明""这说明"
   - "不难看出""不难发现"

3. 禁止模板结构：
   - "首先、其次、最后"
   - "一方面、另一方面"
   - "从...角度来看"

4. 禁止空洞套话：
   - "这一事件标志着""具有里程碑意义"
   - "引发了广泛关注""引起了热议"
   - "具有重要意义""影响深远"

【正确的写法】
- 直接表达观点，不要铺垫
- 有结论就直接说，不要用"可能""也许"
- 结尾要自然收束，不要强行升华
- 像专业记者写新闻稿一样，简洁有力

现在请开始写，直接输出文章正文，不要有任何前言或解释："""
        
        try:
            max_retries = 5  # 增加重试次数
            retry_delay = 10  # 增加初始延迟
            
            for attempt in range(max_retries):
                try:
                    print(f"    [API] 正在生成点评（尝试 {attempt + 1}/{max_retries}），模型: {self.analyzer.model}...")
                    
                    if self.analyzer.provider in ["openai", "openrouter"]:
                        response = self.analyzer.client.chat.completions.create(
                            model=self.analyzer.model,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.8
                        )
                        print(f"    [API] 点评生成成功")
                        return response.choices[0].message.content
                    elif self.analyzer.provider == "anthropic":
                        response = self.analyzer.client.messages.create(
                            model=self.analyzer.model,
                            max_tokens=2500,
                            messages=[{"role": "user", "content": prompt}]
                        )
                        print(f"    [API] 点评生成成功")
                        return response.content[0].text
                    elif self.analyzer.provider == "dashscope":
                        extra_body = {}
                        if self.analyzer.enable_search:
                            extra_body["enable_search"] = True
                        
                        response = self.analyzer.client.chat.completions.create(
                            model=self.analyzer.model,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.8,
                            extra_body=extra_body
                        )
                        print(f"    [API] 点评生成成功")
                        return response.choices[0].message.content
                    else:
                        return ""
                        
                except Exception as api_error:
                    if attempt < max_retries - 1:
                        print(f"    [警告] 点评生成失败: {api_error}，{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise api_error
                        
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
                    model="qwen3.6-flash",
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
