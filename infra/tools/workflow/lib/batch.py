"""批量任务分发 - 作家/审核员循环分配"""
from typing import Dict, List

from .tasks import dispatch_task


def batch_dispatch_writer(chapters: List[str], writers: List[str] = None) -> Dict[str, str]:
    """批量分配作家任务

    Args:
        chapters: 章节列表（如 ['ch001', 'ch002']）
        writers: 作家列表，默认10个作家循环

    Returns:
        {chapter: task_id} 映射
    """
    if writers is None:
        writers = [chr(ord('a') + i) for i in range(10)]  # a-j

    results = {}
    for i, ch in enumerate(chapters):
        writer_id = writers[i % len(writers)]
        task_id = dispatch_task(f"write_{ch}", f"writer-{writer_id}", f"撰写{ch}")
        results[ch] = task_id

    return results


def batch_dispatch_reviewer(chapters: List[str], reviewers: List[str] = None) -> Dict[str, str]:
    """批量分配审核员任务

    Args:
        chapters: 章节列表
        reviewers: 审核员列表，默认5个审核员每2人一组

    Returns:
        {chapter: task_id} 映射
    """
    if reviewers is None:
        reviewers = [chr(ord('a') + i) for i in range(5)]  # a-e

    results = {}
    for i, ch in enumerate(chapters):
        reviewer_id = reviewers[i % len(reviewers)]
        task_id = dispatch_task(f"review_{ch}", f"reviewer-{reviewer_id}", f"审核{ch}")
        results[ch] = task_id

    return results
