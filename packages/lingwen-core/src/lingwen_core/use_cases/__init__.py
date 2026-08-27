"""灵文核心 · Use-cases — 业务用例包

Phase 18.2 — 业务逻辑的事件驱动实现。

每个 use-case:
- 接受 Ports 注入 (LLMPort / EventStorePort / CheckerPort)
- 返回 DomainEvent 供上游订阅
- 不直接访问 DB / 文件系统

模块:
- write_chapter: WriteChapterUseCase + WriteChapterCommand
- review_chapter: ReviewChapterUseCase + ReviewChapterCommand
- merge_ripples: MergeRipplesUseCase (ripple 状态机管理)
"""
from __future__ import annotations

from lingwen_core.use_cases.merge_ripples import MergeRipplesUseCase
from lingwen_core.use_cases.review_chapter import (
    ReviewChapterCommand,
    ReviewChapterUseCase,
)
from lingwen_core.use_cases.write_chapter import (
    WriteChapterCommand,
    WriteChapterUseCase,
)

__all__ = [
    "WriteChapterUseCase",
    "WriteChapterCommand",
    "ReviewChapterUseCase",
    "ReviewChapterCommand",
    "MergeRipplesUseCase",
]
