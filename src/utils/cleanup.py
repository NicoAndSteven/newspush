"""
存储清理工具 - 自动清理生成的文件，防止存储空间溢出
适用于GitHub Actions等有限存储环境
"""
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List


def cleanup_old_files(
    directory: str,
    max_age_hours: int = 24,
    keep_latest: int = 0,
    dry_run: bool = False,
    exclude_files: List[str] = None
) -> dict:
    """
    清理旧文件
    
    Args:
        directory: 要清理的目录
        max_age_hours: 文件最大保留时间（小时）
        keep_latest: 保留最新的N个文件（0=不保留）
        dry_run: 仅模拟，不实际删除
        exclude_files: 要保留的文件名列表
    
    Returns:
        {
            'deleted_count': 删除的文件数,
            'deleted_size': 删除的总大小（字节）,
            'kept_count': 保留的文件数,
            'errors': 错误列表
        }
    """
    result = {
        'deleted_count': 0,
        'deleted_size': 0,
        'kept_count': 0,
        'errors': []
    }
    
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"[Cleanup] 目录不存在: {directory}")
        return result
    
    exclude_files = exclude_files or []
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    
    all_files = sorted(
        dir_path.glob("*"),
        key=lambda x: x.stat().st_mtime if x.is_file() else 0,
        reverse=True
    )
    
    files_to_keep = set(all_files[:keep_latest]) if keep_latest > 0 else set()
    
    for file_path in all_files:
        if not file_path.is_file():
            continue
        
        if file_path.name in exclude_files:
            result['kept_count'] += 1
            continue
        
        if file_path in files_to_keep:
            result['kept_count'] += 1
            continue
        
        try:
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            if file_mtime < cutoff_time:
                file_size = file_path.stat().st_size
                
                if dry_run:
                    print(f"[Cleanup] [模拟] 将删除: {file_path.name}")
                else:
                    file_path.unlink()
                    print(f"[Cleanup] 已删除: {file_path.name}")
                
                result['deleted_count'] += 1
                result['deleted_size'] += file_size
            else:
                result['kept_count'] += 1
                
        except Exception as e:
            result['errors'].append(f"{file_path.name}: {e}")
    
    return result


def cleanup_all_results(
    results_dir: str = "./results",
    data_dir: str = "./data",
    max_age_hours: int = 24,
    keep_latest: int = 0,
    dry_run: bool = False,
    exclude_files: List[str] = None
) -> dict:
    """
    清理所有生成的文件
    
    Args:
        results_dir: 结果目录
        data_dir: 数据目录
        max_age_hours: 最大保留时间
        keep_latest: 保留最新的N个文件
        dry_run: 仅模拟
        exclude_files: 要保留的文件名列表
    """
    total_result = {
        'deleted_count': 0,
        'deleted_size': 0,
        'kept_count': 0,
        'errors': []
    }
    
    exclude_files = exclude_files or []
    
    print(f"[Cleanup] 开始清理，最大保留时间: {max_age_hours}小时")
    
    for directory in [results_dir, data_dir]:
        if Path(directory).exists():
            result = cleanup_old_files(
                directory=directory,
                max_age_hours=max_age_hours,
                keep_latest=keep_latest,
                dry_run=dry_run
            )
            total_result['deleted_count'] += result['deleted_count']
            total_result['deleted_size'] += result['deleted_size']
            total_result['kept_count'] += result['kept_count']
            total_result['errors'].extend(result['errors'])
    
    deleted_mb = total_result['deleted_size'] / (1024 * 1024)
    print(f"[Cleanup] 清理完成: 删除 {total_result['deleted_count']} 个文件，释放 {deleted_mb:.2f} MB")
    
    if total_result['errors']:
        print(f"[Cleanup] 错误: {len(total_result['errors'])} 个")
    
    return total_result


def clear_directory(directory: str, exclude_files: List[str] = None, dry_run: bool = False) -> int:
    """
    清空整个目录（可排除特定文件）
    
    Args:
        directory: 要清空的目录
        exclude_files: 要保留的文件名列表（如 ['analyzed_urls.json']）
        dry_run: 仅模拟
    
    Returns:
        删除的文件数
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        return 0
    
    exclude_files = exclude_files or []
    count = 0
    
    for item in dir_path.iterdir():
        if item.is_file():
            if item.name in exclude_files:
                if not dry_run:
                    print(f"[Cleanup] 保留: {item.name}")
                continue
            
            if dry_run:
                print(f"[Cleanup] [模拟] 将删除: {item.name}")
            else:
                item.unlink()
                print(f"[Cleanup] 已删除: {item.name}")
            count += 1
        elif item.is_dir():
            if dry_run:
                print(f"[Cleanup] [模拟] 将删除目录: {item.name}")
            else:
                shutil.rmtree(item)
            count += 1
    
    if not dry_run:
        print(f"[Cleanup] 已清空目录: {directory}（保留 {len(exclude_files)} 个文件）")
    
    return count


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="存储清理工具")
    parser.add_argument("--dry-run", action="store_true", help="仅模拟，不实际删除")
    parser.add_argument("--max-age", type=int, default=24, help="最大保留时间（小时）")
    parser.add_argument("--keep-latest", type=int, default=0, help="保留最新的N个文件")
    parser.add_argument("--clear-all", action="store_true", help="清空所有文件")
    
    args = parser.parse_args()
    
    if args.clear_all:
        clear_directory("./results", dry_run=args.dry_run)
        clear_directory("./data", dry_run=args.dry_run)
    else:
        cleanup_all_results(
            max_age_hours=args.max_age,
            keep_latest=args.keep_latest,
            dry_run=args.dry_run
        )
