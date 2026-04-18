import os
import sys
import schedule
import time
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

print("[LOG] ========== NewsPush 启动 ==========")
print(f"[LOG] 当前时间: {datetime.now()}")
print(f"[LOG] Python 版本: {sys.version}")
print(f"[LOG] 工作目录: {os.getcwd()}")

print("[LOG] 步骤1: 加载环境变量...")
load_dotenv(override=True)
print("[LOG] 步骤1: 完成")

print("[LOG] 步骤2: 下载 nltk 数据（newspaper3k 需要）...")
import nltk
try:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    print("[LOG] 步骤2: nltk 数据下载完成")
except Exception as e:
    print(f"[LOG] 步骤2: nltk 下载警告: {e}")

print("[LOG] 步骤3: 设置 Python 路径...")
sys.path.insert(0, str(Path(__file__).parent / "src"))
print("[LOG] 步骤3: 完成")

print("[LOG] 步骤4: 导入模块...")
print("[LOG]   - 导入 config...")
from config import config
print("[LOG]   - 导入 rss_fetcher...")
from news_capture.rss_fetcher import RSSNewsFetcher
print("[LOG]   - 导入 deep_analyzer...")
from ai_processor.deep_analyzer import DeepNewsAnalyzer, CommentaryGenerator, AnalysisDepth
print("[LOG]   - 导入 two_stage_analyzer...")
from ai_processor.two_stage_analyzer import TwoStageAnalyzer
print("[LOG]   - 导入 sensitivity_checker...")
from utils.sensitivity_checker import check_news_sensitivity, SensitivityChecker, SensitivityLevel
print("[LOG]   - 导入 output_formatter...")
from utils.output_formatter import generate_both_versions
print("[LOG]   - 导入 direct_word_generator...")
from utils.direct_word_generator import generate_word_directly, DOCX_AVAILABLE
print("[LOG]   - 导入 translator...")
from utils.translator import translate_if_needed
print("[LOG]   - 导入 wechat_pusher...")
from utils.wechat_pusher import push_article_to_wechat
print("[LOG]   - 导入 cleanup...")
from utils.cleanup import cleanup_all_results
print("[LOG] 步骤4: 所有模块导入完成")

class NewsPushPipeline:
    def __init__(self):
        print("[LOG] 步骤5: 初始化 NewsPushPipeline...")
        
        print("[LOG]   - 初始化存储...")
        from storage.json_storage import JSONStorage
        self.storage = JSONStorage()
        
        print("[LOG]   - 初始化 RSS 抓取器...")
        self.news_fetcher = RSSNewsFetcher(self.storage)
        
        # 深度分析器（使用阿里云百炼 Qwen 大模型）
        enable_search = os.getenv("ENABLE_SEARCH", "true").lower() == "true"
        self.deep_analyzer = None
        
        dashscope_key = os.getenv("DASHSCOPE_API_KEY", "")
        print(f"[LOG]   - 检查 API Key: 阿里云百炼={'已设置' if dashscope_key else '未设置'}")
        
        if config.DASHSCOPE_API_KEY:
            print("[LOG]   - 初始化阿里云百炼 Qwen 大模型...")
            self.deep_analyzer = DeepNewsAnalyzer("dashscope", config.DASHSCOPE_API_KEY, enable_search)
            print("[LOG]   - AI 初始化完成")
        else:
            print("[LOG]   - [警告] 未配置阿里云百炼 API Key")
        
        print("[LOG]   - 初始化点评生成器...")
        self.commentary_generator = CommentaryGenerator(self.deep_analyzer) if self.deep_analyzer else None
        
        print("[LOG]   - 初始化两阶段分析器...")
        self.two_stage_analyzer = TwoStageAnalyzer(self.deep_analyzer) if self.deep_analyzer else None
        
        print("[LOG]   - 初始化图片获取器...")
        from utils.image_fetcher import ImageFetcherSync
        self.image_fetcher = ImageFetcherSync()
        
        print("[LOG]   - 创建结果目录...")
        self.results_dir = Path("./results")
        self.results_dir.mkdir(exist_ok=True)
        
        print("[LOG] 步骤5: NewsPushPipeline 初始化完成")
    
    def fetch_news(self, hours: int = 1, use_keywords: bool = False):
        """
        抓取新闻（自动跳过已分析的文章）
        支持板块均衡：每个板块抓取指定数量的新闻
        """
        print(f"[{datetime.now()}] 开始抓取新闻（板块均衡模式）...")
        
        # 按分类组织新闻
        news_by_category = {}
        
        for source in config.RSS_SOURCES:
            # 支持新旧两种配置格式
            if isinstance(source, tuple):
                url, category = source
            else:
                url, category = source, "general"
            
            news_items, status = self.news_fetcher.fetch_rss_feed(
                url, 
                category, 
                max_items=config.MAX_NEWS_PER_CATEGORY,
                skip_analyzed=True  # 在抓取阶段就跳过已分析的文章
            )
            
            if category not in news_by_category:
                news_by_category[category] = []
            news_by_category[category].extend(news_items)
            
            print(f"  [{category}] 从 {url[:50]}... 获取 {len(news_items)} 条新闻")
        
        # 打印各板块统计
        print(f"\n  各板块新闻统计:")
        total_count = 0
        for cat, items in news_by_category.items():
            print(f"    - {cat}: {len(items)} 条")
            total_count += len(items)
        
        print(f"  共获取 {total_count} 条新新闻（已跳过已分析的文章）")
        
        # 返回按板块组织的新闻
        return news_by_category
    
    def deep_analyze_news(self, news_by_category, depth: AnalysisDepth = AnalysisDepth.DEEP, max_analyze: int = None):
        """深度分析新闻（板块均衡：每个板块各挑一篇）
        
        Args:
            news_by_category: 按板块组织的新闻字典 {category: [news_items]}
            depth: 分析深度
            max_analyze: 最大分析数量（None=每个板块各分析一篇）
        """
        if not self.deep_analyzer or not self.two_stage_analyzer:
            print("未配置深度分析 AI API，跳过分析")
            return []
        
        print(f"[{datetime.now()}] 开始深度分析新闻（{depth.value}模式，板块均衡）...")
        print(f"  已分析文章总数: {self.storage.get_analyzed_count()} 篇")
        
        # 板块均衡：每个板块各挑一篇
        news_to_analyze = []
        
        if isinstance(news_by_category, dict):
            # 新格式：按板块组织的新闻
            for category, items in news_by_category.items():
                for item in items:
                    # 检查是否已分析过
                    if not self.storage.is_news_analyzed(item.link):
                        news_to_analyze.append(item)
                        print(f"  [选择] {category}: {item.title[:40]}...")
                        break  # 每个板块只选一篇
        else:
            # 兼容旧格式：列表
            for item in news_by_category:
                if len(news_to_analyze) >= (max_analyze or config.MAX_NEWS_TO_ANALYZE):
                    break
                if not self.storage.is_news_analyzed(item.link):
                    news_to_analyze.append(item)
        
        print(f"  将分析 {len(news_to_analyze)} 条新闻（各板块各一篇）")
        
        if not news_to_analyze:
            print("  没有需要分析的新新闻")
            return []
        
        analyzed = []
        for item in news_to_analyze:
            print(f"\n  分析: {item.title[:50]}...")
            
            # 步骤1: 敏感度检查
            sensitivity_level, sensitivity_info = check_news_sensitivity(item.title, item.description)
            print(f"    [敏感度] {SensitivityChecker.get_sensitivity_label(sensitivity_level)}")
            print(f"    [原因] {sensitivity_info['reason']}")
            
            # 高敏感新闻强制使用两阶段分析
            use_two_stage = (sensitivity_level == SensitivityLevel.HIGH or 
                           sensitivity_level == SensitivityLevel.MEDIUM)
            
            if use_two_stage:
                print(f"    [流程] 使用两阶段分析（Fact-Checker + 生成）")
                try:
                    two_stage_result = self.two_stage_analyzer.analyze(
                        item.title,
                        item.description,
                        depth
                    )
                    
                    # 从两阶段结果中提取分析结果
                    combined = two_stage_result["combined_result"]
                    result = two_stage_result["stage2_analysis"]
                    
                    # 保存阶段1事实清单供参考
                    result.stage1_facts = two_stage_result["stage1_facts"]
                    
                    print(f"    [阶段1] 事实核查完成")
                    if two_stage_result["stage1_facts"].get("conflicting_info"):
                        print(f"    [警告] 发现 {len(two_stage_result['stage1_facts']['conflicting_info'])} 个矛盾点")
                    
                except Exception as e:
                    print(f"    [错误] 两阶段分析失败: {e}，回退到标准分析")
                    result = self.deep_analyzer.analyze_news_deep(
                        item.title, 
                        item.description,
                        depth
                    )
            else:
                print(f"    [流程] 使用标准分析")
                result = self.deep_analyzer.analyze_news_deep(
                    item.title, 
                    item.description,
                    depth
                )
            
            analyzed.append({
                "news": item,
                "deep_analysis": result,
                "sensitivity": sensitivity_info,
                "use_two_stage": use_two_stage
            })
            
            # 标记为已分析
            self.storage.mark_news_as_analyzed(item.link, {
                'summary': result.summary,
                'content_type': result.content_type
            })
            
            # 显示分析结果摘要
            print(f"    [OK] 类型: {result.content_type}")
            print(f"    [OK] 重要性: {result.importance_level}")
            print(f"    [OK] 紧急度: {result.urgency_level}/10")
            
            # 高敏感新闻提示人工复核
            if sensitivity_level == SensitivityLevel.HIGH:
                print(f"    [⚠️ 注意] 高敏感新闻，建议人工复核")
        
        # 清理旧数据
        self.storage.clear_old_analyzed_news(keep_days=7)
        
        return analyzed
    
    def generate_commentary(self, analyzed_items, style: str = "balanced", max_generate: int = None, skip_files: bool = False):
        """生成新闻点评（双版本）
        
        Args:
            analyzed_items: 已分析的新闻列表
            style: 写作风格
            max_generate: 最大生成数量
            skip_files: 是否跳过文件生成（微信推送时不需要生成 Markdown 和 Word）
        """
        if not self.commentary_generator:
            print("未配置 AI，跳过点评生成")
            return []
        
        print(f"[{datetime.now()}] 开始生成新闻点评（双版本）...")
        
        # 如果没有指定生成数量，则生成数量 = 分析数量（一对一）
        if max_generate is None:
            max_generate = len(analyzed_items)
        
        commentaries = []
        generated_count = 0
        skipped_count = 0
        
        for item in analyzed_items:
            # 检查是否已达到最大数量
            if generated_count >= max_generate:
                print(f"  已达到最大点评数量限制 ({max_generate})，停止生成")
                break
            
            analysis = item["deep_analysis"]
            sensitivity_info = item.get("sensitivity", {})
            
            # 可信度检查
            credibility = analysis.credibility or {}
            credibility_level = credibility.get("level", "unknown")
            issues = credibility.get("issues", [])
            
            # 如果可信度为 low，跳过该新闻
            if credibility_level == "low":
                print(f"  [跳过] 可信度过低: {item['news'].title[:50]}...")
                if issues:
                    print(f"    问题: {', '.join(issues[:2])}")
                skipped_count += 1
                continue
            
            # 生成点评
            print(f"  生成点评: {item['news'].title[:50]}...")
            
            # 如果可信度为 medium，添加警告标记
            if credibility_level == "medium":
                print(f"    [警告] 可信度中等: {', '.join(issues[:2])}")
            
            # 使用合并调用时直接返回的点评（如果有的话）
            commentary = analysis.commentary if hasattr(analysis, 'commentary') and analysis.commentary else ""
            
            # 如果没有点评，则单独生成（兼容旧逻辑）
            if not commentary:
                commentary = self.commentary_generator.generate_commentary(analysis, style)
            
            if commentary:
                # 获取配图
                print(f"    获取配图...")
                news_dict = {
                    "title": item['news'].title,
                    "url": getattr(item['news'], 'link', ''),
                    "description": getattr(item['news'], 'description', ''),
                    "images": getattr(item['news'], 'images', [])  # RSS 提供的图片
                }
                analysis_dict = analysis.to_dict() if hasattr(analysis, 'to_dict') else {}
                images = self.image_fetcher.get_article_images(news_dict, analysis_dict)
                print(f"    获取到 {len(images)} 张图片")
                
                # 准备分析数据
                stage2_analysis = {
                    "title": analysis.title,
                    "summary": analysis.summary,
                    "content_type": analysis.content_type,
                    "key_points": analysis.key_points,
                    "background": analysis.background,
                    "impact_analysis": analysis.impact_analysis,
                    "future_outlook": analysis.future_outlook,
                    "unique_angle": analysis.unique_angle,
                    "controversial_aspects": analysis.controversial_aspects,
                    "expert_opinion": commentary,  # 使用生成的点评作为专家观点
                    "tags": analysis.tags,
                    "sentiment": analysis.sentiment,
                    "urgency_level": analysis.urgency_level,
                    "credibility": analysis.credibility,
                    "core_facts": analysis.core_facts if hasattr(analysis, 'core_facts') else {}
                }
                
                # 获取阶段1事实清单（如果有）
                stage1_facts = getattr(analysis, 'stage1_facts', {})
                
                # 翻译标题为中文
                print(f"    翻译标题...")
                translated_title = translate_if_needed(item['news'].title)
                print(f"    原标题: {item['news'].title[:50]}...")
                print(f"    译标题: {translated_title[:50]}...")
                
                # 生成双版本
                print(f"    生成双版本...")
                versions = generate_both_versions(
                    news_title=translated_title,  # 使用翻译后的标题
                    news_source=item['news'].source,
                    stage1_facts=stage1_facts,
                    stage2_analysis=stage2_analysis,
                    sensitivity_info=sensitivity_info,
                    images=images
                )
                
                # 保存文件（如果配置了微信推送，则跳过文件生成）
                if not skip_files:
                    timestamp = int(time.time())
                    safe_title = "".join(c for c in translated_title[:20] if c.isalnum() or c in (' ', '-', '_') or '\u4e00' <= c <= '\u9fff')
                    
                    # Markdown 文件（根据配置决定是否生成）
                    if config.GENERATE_MARKDOWN:
                        public_file = self.results_dir / f"commentary_{timestamp}_{safe_title}_public.md"
                        with open(public_file, 'w', encoding='utf-8') as f:
                            f.write(versions["public"])
                        print(f"    [OK] Markdown: {public_file}")
                    
                    # 内部完整版（根据配置 + 敏感度决定是否生成）
                    if config.GENERATE_INTERNAL_VERSION and sensitivity_info.get('level') in ['high', 'medium']:
                        internal_file = self.results_dir / f"commentary_{timestamp}_{safe_title}_internal.md"
                        with open(internal_file, 'w', encoding='utf-8') as f:
                            f.write(versions["internal"])
                        print(f"    [OK] 内部版: {internal_file}")
                    
                    # Word 文档（根据配置决定是否生成）
                    if config.GENERATE_WORD and DOCX_AVAILABLE:
                        try:
                            word_file = self.results_dir / f"commentary_{timestamp}_{safe_title}_public.docx"
                            core_facts = analysis.core_facts if hasattr(analysis, 'core_facts') else {}
                            
                            generate_word_directly(
                                title=translated_title,
                                summary=analysis.summary,
                                core_facts=core_facts,
                                key_points=analysis.key_points,
                                background=analysis.background,
                                impact_analysis=analysis.impact_analysis,
                                unique_angle=analysis.unique_angle,
                                controversial_aspects=analysis.controversial_aspects,
                                expert_opinion=commentary,
                                future_outlook=analysis.future_outlook,
                                images=images,
                                output_path=str(word_file)
                            )
                            print(f"    [OK] Word: {word_file}")
                        except Exception as e:
                            print(f"    [警告] Word 生成失败: {e}")
                
                commentaries.append({
                    "news": item["news"],
                    "analysis": analysis,
                    "commentary": commentary,
                    "versions": versions,
                    "sensitivity": sensitivity_info,
                    "images": images,
                    "translated_title": translated_title  # 保存翻译后的标题
                })
                
                generated_count += 1
        
        print(f"  生成 {len(commentaries)} 篇点评")
        if skipped_count > 0:
            print(f"  跳过 {skipped_count} 篇低可信度新闻")
        return commentaries
    
    def publish_to_platforms(self, analyzed_items, platforms: List[str] = None):
        """发布到多平台（功能已移除）"""
        print(f"[{datetime.now()}] 发布功能已移除，跳过...")
        return []
    
    def run_full_pipeline(self, max_fetch: int = None, max_analyze: int = None, max_generate: int = None, send_email: bool = True, cleanup: bool = True):
        """
        运行完整流水线
        流程：抓取新闻 → 深度分析 → 生成点评 → 发送邮件 → 清理存储
        
        Args:
            max_fetch: 每个源最多抓取多少条新闻（None=使用配置）
            max_analyze: 最多分析多少条新闻（None=每个板块各一篇）
            max_generate: 最多生成多少篇点评（None=使用配置）
            send_email: 是否发送邮件
            cleanup: 是否清理存储
        """
        print("=" * 70)
        print(f"[{datetime.now()}] NewsPush 完整流水线（板块均衡模式）")
        print("=" * 70)
        
        if max_fetch is not None:
            config.MAX_NEWS_PER_CATEGORY = max_fetch
            print(f"  每个板块抓取数量: {max_fetch}")
        if max_analyze is not None:
            print(f"  分析数量上限: {max_analyze}")
        if max_generate is not None:
            print(f"  点评生成数量上限: {max_generate}")
        print()
        
        news_by_category = self.fetch_news(use_keywords=False)
        
        if not news_by_category or all(len(items) == 0 for items in news_by_category.values()):
            print("没有获取到新新闻，结束本次执行")
            return
        
        analyzed = self.deep_analyze_news(news_by_category, AnalysisDepth.DEEP, max_analyze)
        
        # 如果配置了微信推送，则跳过 Markdown 和 Word 文件生成
        commentaries = self.generate_commentary(analyzed, max_generate=max_generate, skip_files=send_email)
        
        # 统计总新闻数
        total_news = sum(len(items) for items in news_by_category.values()) if isinstance(news_by_category, dict) else len(news_by_category)
        
        print("\n" + "=" * 70)
        print("执行统计:")
        print(f"  - 抓取新闻: {total_news} 条")
        if isinstance(news_by_category, dict):
            print("  - 各板块:")
            for cat, items in news_by_category.items():
                print(f"      {cat}: {len(items)} 条")
        print(f"  - 深度分析: {len(analyzed)} 条（各板块各一篇）")
        print(f"  - 生成点评: {len(commentaries)} 篇")
        print("=" * 70)
        
        if send_email and commentaries:
            print("\n📱 推送到微信公众号草稿箱...")
            pushed_count = 0
            for item in commentaries:
                news = item.get('news')
                versions = item.get('versions', {})
                images = item.get('images', [])
                translated_title = item.get('translated_title', '')  # 使用翻译后的标题
                
                # 使用翻译后的标题，如果没有则使用原标题
                title = translated_title if translated_title else getattr(news, 'title', '未命名文章')
                news_url = getattr(news, 'link', '') if news else ''
                content = versions.get('public', '')
                cover_image = None
                
                # 显示新闻源信息
                print(f"\n  新闻源: {news_url}")
                print(f"  标题: {title[:40]}...")
                
                # 封面图使用第一张（新闻源图片）
                # 正文图片使用剩余的（Pexels 补充）
                if images:
                    cover_image = images[0]  # 封面图
                    content_images = images[1:] if len(images) > 1 else []  # 正文图片
                    print(f"  封面图: {cover_image[:60]}...")
                    if content_images:
                        print(f"  正文图片: {len(content_images)} 张")
                else:
                    cover_image = None
                    content_images = []
                
                # 推送到微信（封面图 + 正文图片）
                if push_article_to_wechat(title, content, cover_image, content_images):
                    pushed_count += 1
                    print(f"  [OK] 推送成功")
                else:
                    print(f"  [跳过] 推送失败")
            
            if pushed_count > 0:
                print(f"  [完成] 成功推送 {pushed_count} 篇文章到草稿箱")
            else:
                print("  [跳过] 未推送任何文章（可能未配置微信公众号）")
        
        if cleanup and config.CLEANUP_AFTER_SEND:
            print("\n🧹 清理存储...")
            cleanup_all_results(
                results_dir=str(self.results_dir),
                data_dir="./data",
                max_age_hours=0,
                keep_latest=0,
                exclude_files=['analyzed_urls.json']
            )
            from utils.cleanup import clear_directory
            clear_directory("./data", exclude_files=['analyzed_urls.json'])
    
    def run_scheduled(self, interval_hours: int = 1):
        """定时运行"""
        print(f"启动定时任务，每 {interval_hours} 小时执行一次")
        
        schedule.every(interval_hours).hours.do(self.run_full_pipeline)
        
        self.run_full_pipeline()
        
        while True:
            schedule.run_pending()
            time.sleep(60)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="NewsPush - 智能新闻分析与邮箱推送系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 运行完整流程（使用配置文件的默认值）
  python main.py --once
  
  # 分析 5 条新闻，生成 5 篇点评
  python main.py --once --analyze 5
  
  # 快速测试：分析 2 条，生成 2 篇
  python main.py --once --analyze 2
  
  # 仅抓取新闻
  python main.py --fetch-only
  
  # 深度分析已有新闻
  python main.py --deep-analyze
  
  # 仅发送邮件（发送已有结果）
  python main.py --send-email
  
  # 仅清理存储
  python main.py --cleanup

环境变量配置:
  DASHSCOPE_API_KEY  - 阿里云百炼 API Key
  SMTP_SERVER        - SMTP服务器（默认: smtp.gmail.com）
  SMTP_PORT          - SMTP端口（默认: 587）
  SMTP_USER          - SMTP用户名（邮箱地址）
  SMTP_PASSWORD      - SMTP密码（应用专用密码）
  EMAIL_TO           - 收件人邮箱
  CLEANUP_AFTER_SEND - 发送后是否清理（默认: true）
        """
    )
    
    parser.add_argument("--once", action="store_true", help="执行一次完整流程")
    parser.add_argument("--fetch", type=int, help="每个RSS源最多抓取多少条新闻")
    parser.add_argument("--analyze", type=int, help="最多分析多少条新闻")
    parser.add_argument("--generate", type=int, help="最多生成多少篇点评文章")
    parser.add_argument("--schedule", type=int, help="定时执行间隔（小时）")
    parser.add_argument("--fetch-only", action="store_true", help="仅抓取新闻")
    parser.add_argument("--deep-analyze", action="store_true", help="深度分析已有新闻")
    parser.add_argument("--send-email", action="store_true", help="仅发送邮件（发送已有结果）")
    parser.add_argument("--cleanup", action="store_true", help="仅清理存储")
    parser.add_argument("--no-email", action="store_true", help="不发送邮件")
    parser.add_argument("--no-cleanup", action="store_true", help="不清理存储")
    
    args = parser.parse_args()
    
    print("[LOG] ==========================================")
    print("[LOG] 步骤6: 开始执行主流程")
    print(f"[LOG] 参数: once={args.once}, analyze={args.analyze}, no_email={args.no_email}")
    print("[LOG] ==========================================")
    
    print("[LOG] 创建 NewsPushPipeline 实例...")
    pipeline = NewsPushPipeline()
    print("[LOG] NewsPushPipeline 实例创建完成")
    
    if args.fetch_only:
        print("[LOG] 模式: 仅抓取新闻")
        pipeline.fetch_news(use_keywords=False)
    
    elif args.deep_analyze:
        print("[LOG] 模式: 深度分析")
        print("[LOG] 重新抓取新闻进行分析...")
        news_items = pipeline.fetch_news(use_keywords=False)
        analyzed = pipeline.deep_analyze_news(news_items, max_analyze=args.analyze)
        print(f"\n[LOG] 完成深度分析 {len(analyzed)} 条新闻")
    
    elif args.send_email:
        print("[LOG] 模式: 仅推送到微信")
        results_dir = Path("./results")
        if results_dir.exists():
            md_files = list(results_dir.glob("commentary_*_public.md"))
            for md_file in md_files:
                content = md_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                title = lines[0].replace('# ', '') if lines else md_file.stem
                push_article_to_wechat(title, content)
        else:
            print("[LOG] results 目录不存在")
    
    elif args.cleanup:
        print("[LOG] 模式: 仅清理存储")
        cleanup_all_results(
            results_dir=str(pipeline.results_dir),
            data_dir="./data",
            max_age_hours=0,
            keep_latest=0
        )
    
    elif args.once:
        print("[LOG] 模式: 执行完整流程")
        pipeline.run_full_pipeline(
            max_fetch=args.fetch,
            max_analyze=args.analyze,
            max_generate=args.generate,
            send_email=not args.no_email,
            cleanup=not args.no_cleanup
        )
    
    elif args.schedule:
        print(f"[LOG] 模式: 定时执行，间隔 {args.schedule} 小时")
        pipeline.run_scheduled(args.schedule)
    
    else:
        parser.print_help()
    
    print("[LOG] ==========================================")
    print("[LOG] 流程执行完毕")
    print("[LOG] ==========================================")

if __name__ == "__main__":
    main()
