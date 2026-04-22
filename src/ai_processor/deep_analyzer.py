import os
import json
import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import time
import httpx


def get_random_temperature(min_temp: float = 0.7, max_temp: float = 1.0) -> float:
    """生成随机 temperature，让输出更多样化"""
    return round(random.uniform(min_temp, max_temp), 2)


class AnalysisDepth(Enum):
    LIGHT = "light"
    STANDARD = "standard"
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
                self.model = self.model or "qwen3.6-max-preview"
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
        
        prompt = f"""当前时间：{current_time}

请对以下新闻进行深度分析并撰写公众号风格的点评文章。

标题：{title}
内容：{content}

请返回 JSON 格式的分析结果，包含以下字段：
- summary: 一句话新闻摘要
- content_type: 内容类型（breaking/tech/finance/sports/entertainment/politics/lifestyle）
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

【点评文章写作要求】

字数规则：
- 娱乐/体育新闻：200-400字
- 科技/财经新闻：600-1000字
- 时政/突发新闻：400-600字
- 一般新闻：400-600字

公众号风格准则：
- 像朋友聊天一样娓娓道来，理性中带温度
- 开头用场景、疑问或感叹快速切入
- 中间把事实、背景、影响自然穿插叙述
- 结尾轻度总结 + 一个开放式问题
- 段落要短，句子长短交错

绝对禁止：
1. 不要出现任何小标题
2. 不要用编号列表
3. 不要出现"核心要点""市场背景"等报告式标签
4. 不要用"首先、其次、最后""一方面、另一方面"
5. 不要用"可能的场景是""未来可能会""值得关注的是"
6. 不要用"这表明""这说明""不难看出""值得注意的是"
7. 不要用"引发了广泛关注""具有重要影响"
8. 不要用括号补充说明
9. 不要用"某国""某组织"等模糊表述

输出格式：先给2-3个标题选项，然后空一行输出正文。

请开始分析，直接输出 JSON 结果："""
        
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
                            temperature=get_random_temperature(0.7, 1.0)
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
                            temperature=get_random_temperature(0.7, 1.0),
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
                    temperature=get_random_temperature(0.7, 1.0)
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
                "style": "轻松有趣",
                "focus": "事件经过 + 明星动态 + 有趣细节",
                "style_guide": "像朋友聊天一样讲述，轻松幽默但不低俗，直接报道事件，不要深度分析。"
            },
            "lifestyle": {
                "min": 200, "max": 400,
                "style": "轻松有趣",
                "focus": "事件经过 + 有趣细节",
                "style_guide": "像朋友聊天一样讲述，轻松幽默但不低俗，直接报道事件。"
            },
            "sports": {
                "min": 300, "max": 500,
                "style": "专业热情",
                "focus": "比赛结果 + 关键时刻 + 球员表现",
                "style_guide": "像体育解说员一样热情专业，聚焦赛事本身，简洁有力，不要过度分析背景。"
            },
            "tech": {
                "min": 600, "max": 1000,
                "style": "专业易懂",
                "focus": "技术突破 + 产品亮点 + 行业影响 + 未来趋势",
                "style_guide": "深度解读技术新闻，用通俗语言解释专业概念，分析技术价值和行业影响，可以适度追溯技术发展脉络。"
            },
            "finance": {
                "min": 600, "max": 1000,
                "style": "专业严谨",
                "focus": "核心数据 + 市场影响 + 投资启示 + 行业趋势",
                "style_guide": "数据说话，聚焦关键信息，分析市场影响和投资启示，语言严谨但不晦涩。"
            },
            "politics": {
                "min": 300, "max": 500,
                "style": "客观简洁",
                "focus": "核心事实 + 主要立场 + 直接影响",
                "style_guide": "客观呈现，不过度解读，说明直接影响即可，避免主观评论和过多历史背景。"
            },
            "breaking": {
                "min": 400, "max": 600,
                "style": "快速准确",
                "focus": "核心事实 + 最新进展 + 直接影响",
                "style_guide": "信息优先，简洁有力，说明最新进展和直接影响，避免过度分析和背景追溯。"
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
                "style_guide": "客观报道严肃事件，聚焦事实，不过度分析，体现对事件的尊重，避免猜测和主观评论。"
            }
        elif content_type in type_config:
            config = type_config[content_type]
        else:
            config = {
                "min": 400, "max": 600,
                "style": "专业平易",
                "focus": "核心事实 + 背景补充 + 简要分析",
                "style_guide": "专业但平易近人的报道，可以适度比喻帮助理解，保持客观但有观点，语言简洁有力。"
            }
        
        prompt = f"""请根据以下新闻信息，撰写一篇公众号风格的新闻点评文章。

新闻标题：{analysis.title}
字数要求：{config['min']}-{config['max']}字

关键信息：
- 核心要点：{', '.join(analysis.key_points[:3])}
- 背景：{analysis.background}
- 影响：{analysis.impact_analysis}
- 独特角度：{analysis.unique_angle}

风格提示：{config['style_guide']}

【写作准则】

你是经验丰富的国际新闻观察者，擅长用自然、口语化的笔触写微信公众号风格的新闻点评文章。你的文字像朋友聊天或个人随笔一样娓娓道来。

【风格要求】
- 整体感觉：像人在讲故事或分享观察，读起来舒服、自然、有代入感
- 语言：口语化、生活化，说人话
- 开头：用场景、时间、人物动作、简单疑问或感叹快速切入
- 中间：把事实、背景、影响自然穿插叙述，段落要短，句子长短交错
- 结尾：轻度总结 + 一个开放式问题

【绝对禁止】
1. 不要出现任何小标题
2. 不要用编号列表、bullet list
3. 不要出现"核心要点""市场背景""投资展望"等报告式标签
4. 不要用"首先、其次、最后""一方面、另一方面"
5. 不要用"可能的场景是""未来可能会""值得关注的是""让我们拭目以待"
6. 不要用"这表明""这说明""不难看出""值得注意的是"
7. 不要用"引发了广泛关注""具有重要影响""具有里程碑意义"
8. 不要用括号补充说明
9. 不要用"某国""某组织""某人物"等模糊表述

【输出格式】
先给出 2-3 个标题选项（每个 20-30 字，带点悬念或疑问）。
然后空一行，直接输出正文。

请开始写："""
        
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
                            temperature=get_random_temperature(0.7, 1.0)
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
                            temperature=get_random_temperature(0.7, 1.0),
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
                    temperature=get_random_temperature(0.7, 1.0)
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
                    model="qwen3.6-max-preview",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=get_random_temperature(0.7, 1.0),
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
