import os
import sys
import schedule
import time
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import config
from news_capture.rss_fetcher import RSSNewsFetcher
from ai_processor.deep_analyzer import DeepNewsAnalyzer, CommentaryGenerator, AnalysisDepth
from ai_processor.two_stage_analyzer import TwoStageAnalyzer
from utils.sensitivity_checker import check_news_sensitivity, SensitivityChecker, SensitivityLevel
from utils.output_formatter import generate_both_versions
from utils.direct_word_generator import generate_word_directly, DOCX_AVAILABLE
from utils.translator import translate_if_needed
from utils.email_sender import send_results_via_email
from utils.cleanup import cleanup_all_results

class NewsPushPipeline:
    def __init__(self):
        from storage.json_storage import JSONStorage
        self.storage = JSONStorage()
        self.news_fetcher = RSSNewsFetcher(self.storage)
        
        # 深度分析器（使用阿里云百炼 Qwen 大模型）
        enable_search = os.getenv("ENABLE_SEARCH", "true").lower() == "true"
        self.deep_analyzer = None
        if config.DASHSCOPE_API_KEY:
            print("  [AI] 使用阿里云百炼 Qwen 大模型")
            self.deep_analyzer = DeepNewsAnalyzer("dashscope", config.DASHSCOPE_API_KEY, enable_search)
        else:
            print("  [警告] 未配置阿里云 API Key")
        
        self.commentary_generator = CommentaryGenerator(self.deep_analyzer) if self.deep_analyzer else None
        
        # 两阶段分析器
        self.two_stage_analyzer = TwoStageAnalyzer(self.deep_analyzer) if self.deep_analyzer else None
        
        # 图片获取器（分层配图策略）
        from utils.image_fetcher import ImageFetcherSync
        self.image_fetcher = ImageFetcherSync()
        
        self.results_dir = Path("./results")
        self.results_dir.mkdir(exist_ok=True)
    
    def fetch_news(self, hours: int = 1, use_keywords: bool = False):
        """
        抓取新闻（不保存到本地，仅返回内存中）
        use_keywords: 是否使用关键词过滤（False=抓取所有新闻）
        """
        print(f"[{datetime.now()}] 开始抓取新闻...")
        
        all_news = []
        
        for url in config.RSS_SOURCES:
            news_items, status = self.news_fetcher.fetch_rss_feed(
                url, 
                "general", 
                max_items=config.MAX_NEWS_PER_SOURCE
            )
            all_news.extend(news_items)
            print(f"  从 {url} 获取 {len(news_items)} 条新闻")
        
        # 不再保存原始新闻到本地，只在内存中处理
        print(f"  共获取 {len(all_news)} 条新闻（不保存原始数据）")
        
        return all_news
    
    def deep_analyze_news(self, news_items, depth: AnalysisDepth = AnalysisDepth.DEEP, max_analyze: int = None):
        """深度分析新闻（集成敏感度检查 + 两阶段分析）"""
        if not self.deep_analyzer or not self.two_stage_analyzer:
            print("未配置深度分析 AI API，跳过分析")
            return []
        
        print(f"[{datetime.now()}] 开始深度分析新闻（{depth.value}模式）...")
        
        # 限制分析数量
        if max_analyze is None:
            max_analyze = config.MAX_NEWS_TO_ANALYZE
        
        news_to_analyze = news_items[:max_analyze]
        print(f"  将分析 {len(news_to_analyze)} 条新闻（总共 {len(news_items)} 条）")
        
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
            
            # 显示分析结果摘要
            print(f"    [OK] 类型: {result.content_type}")
            print(f"    [OK] 紧急度: {result.urgency_level}/10")
            
            # 高敏感新闻提示人工复核
            if sensitivity_level == SensitivityLevel.HIGH:
                print(f"    [⚠️ 注意] 高敏感新闻，建议人工复核")
        
        return analyzed
    
    def generate_commentary(self, analyzed_items, style: str = "balanced", max_generate: int = None):
        """生成新闻点评文章（双版本输出：内部版 + 对外版）"""
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
            
            # 生成点评正文
            commentary = self.commentary_generator.generate_commentary(analysis, style)
            
            if commentary:
                # 获取配图
                print(f"    获取配图...")
                news_dict = {
                    "title": item['news'].title,
                    "url": getattr(item['news'], 'link', ''),  # NewsItem 使用 link 而不是 url
                    "description": getattr(item['news'], 'description', '')
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
                
                # 保存文件
                timestamp = int(time.time())
                # 使用翻译后的标题生成文件名
                safe_title = "".join(c for c in translated_title[:20] if c.isalnum() or c in (' ', '-', '_') or '\u4e00' <= c <= '\u9fff')
                
                # 对外发布版
                public_file = self.results_dir / f"commentary_{timestamp}_{safe_title}_public.md"
                with open(public_file, 'w', encoding='utf-8') as f:
                    f.write(versions["public"])
                print(f"    [OK] 对外版: {public_file}")
                
                # 内部完整版（高敏感新闻才生成）
                if sensitivity_info.get('level') in ['high', 'medium']:
                    internal_file = self.results_dir / f"commentary_{timestamp}_{safe_title}_internal.md"
                    with open(internal_file, 'w', encoding='utf-8') as f:
                        f.write(versions["internal"])
                    print(f"    [OK] 内部版: {internal_file}")
                
                # 生成 Word 文档（直接生成，不经过 Markdown 转换）
                if DOCX_AVAILABLE:
                    try:
                        print(f"    生成 Word 文档...")
                        word_file = self.results_dir / f"commentary_{timestamp}_{safe_title}_public.docx"
                        
                        # 提取核心事实
                        core_facts = analysis.core_facts if hasattr(analysis, 'core_facts') else {}
                        
                        # 直接生成 Word 文档
                        generate_word_directly(
                            title=translated_title,
                            summary=analysis.summary,
                            core_facts=core_facts,
                            key_points=analysis.key_points,
                            background=analysis.background,
                            impact_analysis=analysis.impact_analysis,
                            unique_angle=analysis.unique_angle,
                            controversial_aspects=analysis.controversial_aspects,
                            expert_opinion=commentary,  # 使用生成的点评
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
                    "sensitivity": sensitivity_info
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
            max_analyze: 最多分析多少条新闻（None=使用配置）
            max_generate: 最多生成多少篇点评（None=使用配置）
            send_email: 是否发送邮件
            cleanup: 是否清理存储
        """
        print("=" * 70)
        print(f"[{datetime.now()}] NewsPush 完整流水线")
        print("=" * 70)
        
        original_max_per_source = config.MAX_NEWS_PER_SOURCE
        if max_fetch is not None:
            config.MAX_NEWS_PER_SOURCE = max_fetch
            print(f"  每个源抓取数量: {max_fetch}")
        if max_analyze is not None:
            print(f"  分析数量: {max_analyze}")
        if max_generate is not None:
            print(f"  点评生成数量: {max_generate}")
        print()
        
        news_items = self.fetch_news(use_keywords=False)
        
        config.MAX_NEWS_PER_SOURCE = original_max_per_source
        
        if not news_items:
            print("没有获取到新新闻，结束本次执行")
            return
        
        analyzed = self.deep_analyze_news(news_items, AnalysisDepth.DEEP, max_analyze)
        
        commentaries = self.generate_commentary(analyzed, max_generate=max_generate)
        
        print("\n" + "=" * 70)
        print("📊 执行统计:")
        print(f"  - 抓取新闻: {len(news_items)} 条")
        print(f"  - 深度分析: {len(analyzed)} 条")
        print(f"  - 生成点评: {len(commentaries)} 篇")
        print("=" * 70)
        
        if send_email and commentaries:
            print("\n📧 发送邮件...")
            email_sent = send_results_via_email(
                results_dir=str(self.results_dir),
                to_email=config.EMAIL_TO
            )
            if email_sent:
                print("  [OK] 邮件发送成功")
            else:
                print("  [跳过] 邮件未发送（可能未配置）")
        
        if cleanup and config.CLEANUP_AFTER_SEND:
            print("\n🧹 清理存储...")
            cleanup_all_results(
                results_dir=str(self.results_dir),
                data_dir="./data",
                max_age_hours=1,
                keep_latest=0
            )
    
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
    
    pipeline = NewsPushPipeline()
    
    if args.fetch_only:
        pipeline.fetch_news(use_keywords=False)
    
    elif args.deep_analyze:
        # 从内存中重新抓取新闻进行分析（不读取本地存储）
        print("[注意] 重新抓取新闻进行分析...")
        news_items = pipeline.fetch_news(use_keywords=False)
        analyzed = pipeline.deep_analyze_news(news_items, max_analyze=args.analyze)
        
        print(f"\n完成深度分析 {len(analyzed)} 条新闻")
    
    elif args.send_email:
        send_results_via_email(results_dir=str(pipeline.results_dir))
    
    elif args.cleanup:
        cleanup_all_results(
            results_dir=str(pipeline.results_dir),
            data_dir="./data",
            max_age_hours=0,
            keep_latest=0
        )
    
    elif args.once:
        pipeline.run_full_pipeline(
            max_fetch=args.fetch,
            max_analyze=args.analyze,
            max_generate=args.generate,
            send_email=not args.no_email,
            cleanup=not args.no_cleanup
        )
    
    elif args.schedule:
        pipeline.run_scheduled(args.schedule)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
