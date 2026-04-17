"""
JSON 文件存储 - 轻量级本地存储
替代 SQLite 数据库
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path


class JSONStorage:
    """JSON 文件存储管理器"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.news_file = self.data_dir / "news.json"
        self.tasks_file = self.data_dir / "tasks.json"
        
        # 初始化文件
        self._init_file(self.news_file, {"news": []})
        self._init_file(self.tasks_file, {"tasks": []})
    
    def _init_file(self, file_path: Path, default_data: dict):
        """初始化 JSON 文件"""
        if not file_path.exists():
            self._save_json(file_path, default_data)
    
    def _load_json(self, file_path: Path) -> dict:
        """加载 JSON 文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Storage] Error loading {file_path}: {e}")
            return {}
    
    def _save_json(self, file_path: Path, data: dict):
        """保存 JSON 文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Storage] Error saving {file_path}: {e}")
    
    # ========== 新闻相关操作 ==========
    
    def save_news(self, news_items: List[Dict]):
        """保存新闻（去重）"""
        data = self._load_json(self.news_file)
        existing_links = {item['link'] for item in data.get('news', [])}
        
        for item in news_items:
            if item['link'] not in existing_links:
                # 添加元数据
                item['created_at'] = datetime.now().isoformat()
                item['id'] = len(data.get('news', [])) + 1
                data['news'].append(item)
                existing_links.add(item['link'])
        
        self._save_json(self.news_file, data)
        return len(news_items)
    
    def get_recent_news(self, hours: int = 24) -> List[Dict]:
        """获取最近的新闻"""
        data = self._load_json(self.news_file)
        all_news = data.get('news', [])
        
        if hours <= 0:
            return all_news
        
        # 过滤最近的新闻
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_news = []
        
        for item in all_news:
            try:
                item_time = datetime.fromisoformat(item.get('created_at', ''))
                if item_time >= cutoff_time:
                    recent_news.append(item)
            except:
                # 如果没有创建时间，也包含在内
                recent_news.append(item)
        
        # 按创建时间倒序
        recent_news.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return recent_news
    
    def get_news_by_link(self, link: str) -> Optional[Dict]:
        """通过链接获取新闻"""
        data = self._load_json(self.news_file)
        for item in data.get('news', []):
            if item['link'] == link:
                return item
        return None
    
    def update_news_content(self, link: str, full_content: str):
        """更新新闻完整内容"""
        data = self._load_json(self.news_file)
        for item in data.get('news', []):
            if item['link'] == link:
                item['full_content'] = full_content
                item['updated_at'] = datetime.now().isoformat()
                break
        self._save_json(self.news_file, data)
    
    def clear_old_news(self, keep_days: int = 30):
        """清理旧新闻"""
        data = self._load_json(self.news_file)
        cutoff_time = datetime.now() - timedelta(days=keep_days)
        
        filtered_news = []
        for item in data.get('news', []):
            try:
                item_time = datetime.fromisoformat(item.get('created_at', ''))
                if item_time >= cutoff_time:
                    filtered_news.append(item)
            except:
                filtered_news.append(item)
        
        data['news'] = filtered_news
        self._save_json(self.news_file, data)
        return len(filtered_news)
    
    def delete_news_by_links(self, links: List[str]) -> int:
        """根据链接删除新闻"""
        data = self._load_json(self.news_file)
        original_count = len(data.get('news', []))
        
        # 过滤掉要删除的新闻
        data['news'] = [item for item in data.get('news', []) if item['link'] not in links]
        
        self._save_json(self.news_file, data)
        deleted_count = original_count - len(data['news'])
        return deleted_count
    
    def delete_all_news(self) -> int:
        """删除所有新闻"""
        data = self._load_json(self.news_file)
        count = len(data.get('news', []))
        data['news'] = []
        self._save_json(self.news_file, data)
        return count
    
    # ========== 任务相关操作 ==========
    
    def save_task(self, task: Dict) -> int:
        """保存任务"""
        data = self._load_json(self.tasks_file)
        task_id = len(data.get('tasks', [])) + 1
        task['id'] = task_id
        task['created_at'] = datetime.now().isoformat()
        data['tasks'].append(task)
        self._save_json(self.tasks_file, data)
        return task_id
    
    def get_task(self, task_id: int) -> Optional[Dict]:
        """获取任务"""
        data = self._load_json(self.tasks_file)
        for task in data.get('tasks', []):
            if task['id'] == task_id:
                return task
        return None
    
    def update_task(self, task_id: int, updates: Dict):
        """更新任务"""
        data = self._load_json(self.tasks_file)
        for task in data.get('tasks', []):
            if task['id'] == task_id:
                task.update(updates)
                task['updated_at'] = datetime.now().isoformat()
                break
        self._save_json(self.tasks_file, data)
    
    def get_pending_tasks(self) -> List[Dict]:
        """获取待处理任务"""
        data = self._load_json(self.tasks_file)
        return [t for t in data.get('tasks', []) if t.get('status') == 'pending']
    
    # ========== 已分析文章去重 ==========
    
    def is_news_analyzed(self, link: str) -> bool:
        """检查新闻是否已分析过"""
        data = self._load_json(self.news_file)
        for item in data.get('news', []):
            if item['link'] == link:
                # 检查是否有分析标记
                return item.get('analyzed', False)
        return False
    
    def mark_news_as_analyzed(self, link: str, analysis_result: Dict = None):
        """标记新闻为已分析"""
        data = self._load_json(self.news_file)
        for item in data.get('news', []):
            if item['link'] == link:
                item['analyzed'] = True
                item['analyzed_at'] = datetime.now().isoformat()
                if analysis_result:
                    item['analysis_summary'] = analysis_result.get('summary', '')
                    item['content_type'] = analysis_result.get('content_type', '')
                break
        self._save_json(self.news_file, data)
    
    def get_unanalyzed_news(self, hours: int = 24) -> List[Dict]:
        """获取未分析的新闻"""
        data = self._load_json(self.news_file)
        all_news = data.get('news', [])
        
        if hours <= 0:
            return [item for item in all_news if not item.get('analyzed', False)]
        
        # 过滤最近的新闻且未分析的
        cutoff_time = datetime.now() - timedelta(hours=hours)
        unanalyzed_news = []
        
        for item in all_news:
            # 已分析的跳过
            if item.get('analyzed', False):
                continue
            
            try:
                item_time = datetime.fromisoformat(item.get('created_at', ''))
                if item_time >= cutoff_time:
                    unanalyzed_news.append(item)
            except:
                # 如果没有创建时间，也包含在内
                unanalyzed_news.append(item)
        
        # 按创建时间倒序
        unanalyzed_news.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return unanalyzed_news
    
    def clear_old_analyzed_news(self, keep_days: int = 7):
        """清理已分析的旧新闻（保留最近 N 天）"""
        data = self._load_json(self.news_file)
        cutoff_time = datetime.now() - timedelta(days=keep_days)
        
        filtered_news = []
        for item in data.get('news', []):
            # 保留未分析的
            if not item.get('analyzed', False):
                filtered_news.append(item)
                continue
            
            # 已分析的，检查时间
            try:
                item_time = datetime.fromisoformat(item.get('analyzed_at', item.get('created_at', '')))
                if item_time >= cutoff_time:
                    filtered_news.append(item)
            except:
                filtered_news.append(item)
        
        data['news'] = filtered_news
        self._save_json(self.news_file, data)
        return len(filtered_news)


# 全局实例
storage = JSONStorage()
