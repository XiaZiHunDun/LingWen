"""studio_api · 依赖注入容器

Phase 18.3 — 把 LLM / EventStorePort / Use-cases 注入到 FastAPI 路由。

所有 get_*() 是 FastAPI Depends() 工厂函数，单例缓存。
"""

from __future__ import annotations

from functools import lru_cache

from lingwen_core.ports import (
    EmbeddingPort,
    EventStorePort,
    InMemoryEventStore,
    LLMPort,
)
from lingwen_core.use_cases import (
    MergeRipplesUseCase,
    ReviewChapterUseCase,
    WriteChapterUseCase,
)


@lru_cache(maxsize=1)
def get_event_store() -> EventStorePort:
    """事件存储单例（Phase 18.3 用内存版；Phase 19 接 lingwen_storage SQLite）。

    所有 use-case 共享同一 store，确保事件溯源一致性。
    """
    return InMemoryEventStore()


@lru_cache(maxsize=1)
def get_llm() -> LLMPort:
    """LLM 单例（Phase 18.3 用 stub；Phase 19 接 lingwen_llm 真实 provider）。

    Stub 返回 prompt 回显，避免真实 API 成本。
    """
    from lingwen_core.ports import EchoLLM

    return EchoLLM()


@lru_cache(maxsize=1)
def get_embedding() -> EmbeddingPort:
    """嵌入模型单例（Phase 18.3 用 SHA-256 hash 占位）。"""
    from lingwen_core.ports import HashEmbedding

    return HashEmbedding()


@lru_cache(maxsize=1)
def get_write_chapter_use_case() -> WriteChapterUseCase:
    """写章节用例单例 — 注入 LLMPort + EventStorePort。"""
    return WriteChapterUseCase(llm=get_llm(), store=get_event_store())


@lru_cache(maxsize=1)
def get_review_chapter_use_case() -> ReviewChapterUseCase:
    """审核章节用例单例 — 注入 checkers + EventStorePort。"""
    from lingwen_core.ports import AlwaysPassChecker

    # Phase 18.3 只用占位 checker；Phase 19 接 lingwen-quality 真实 checker
    checkers: list = [AlwaysPassChecker()]
    return ReviewChapterUseCase(checkers=checkers, store=get_event_store())


@lru_cache(maxsize=1)
def get_merge_ripples_use_case() -> MergeRipplesUseCase:
    """涟漪合并用例单例 — 注入 EventStorePort。"""
    return MergeRipplesUseCase(store=get_event_store())


# FastAPI Depends() wrappers（避免路由代码 lru_cache 类型冲突）
def event_store_dep() -> EventStorePort:
    return get_event_store()


def llm_dep() -> LLMPort:
    return get_llm()


def write_chapter_dep() -> WriteChapterUseCase:
    return get_write_chapter_use_case()


def review_chapter_dep() -> ReviewChapterUseCase:
    return get_review_chapter_use_case()


def merge_ripples_dep() -> MergeRipplesUseCase:
    return get_merge_ripples_use_case()
