"""Phase 18.3 守卫测试 — apps/studio_api.dependencies DI 容器。

DI 容器为 use-cases 提供 LLM / EventStorePort 实例注入。
"""
from __future__ import annotations


def test_dependencies_module_importable():
    from apps.studio_api import dependencies  # noqa: F401


def test_get_event_store_returns_port():
    """get_event_store() 必须返回 EventStorePort 协议实现。"""
    from apps.studio_api.dependencies import get_event_store
    from lingwen_core.ports import EventStorePort

    store = get_event_store()
    assert isinstance(store, EventStorePort)


def test_get_llm_returns_port():
    """get_llm() 必须返回 LLMPort 协议实现。"""
    from apps.studio_api.dependencies import get_llm
    from lingwen_core.ports import LLMPort

    llm = get_llm()
    assert isinstance(llm, LLMPort)


def test_get_write_chapter_use_case():
    """get_write_chapter_use_case() 必须返回 WriteChapterUseCase。"""
    from apps.studio_api.dependencies import get_write_chapter_use_case
    from lingwen_core.use_cases import WriteChapterUseCase

    use_case = get_write_chapter_use_case()
    assert isinstance(use_case, WriteChapterUseCase)


def test_get_review_chapter_use_case():
    from apps.studio_api.dependencies import get_review_chapter_use_case
    from lingwen_core.use_cases import ReviewChapterUseCase

    use_case = get_review_chapter_use_case()
    assert isinstance(use_case, ReviewChapterUseCase)


def test_get_merge_ripples_use_case():
    from apps.studio_api.dependencies import get_merge_ripples_use_case
    from lingwen_core.use_cases import MergeRipplesUseCase

    use_case = get_merge_ripples_use_case()
    assert isinstance(use_case, MergeRipplesUseCase)


def test_use_cases_share_event_store():
    """DI 单例：所有 use-case 应共享同一个 EventStore（事件溯源一致性）。"""
    from apps.studio_api.dependencies import (
        get_event_store,
        get_merge_ripples_use_case,
        get_review_chapter_use_case,
        get_write_chapter_use_case,
    )

    shared_store = get_event_store()
    # write + review + merge 都应使用同一 store
    # 验证方法：执行 write，再 replay 事件，应能看见
    from lingwen_core.use_cases import (
        ReviewChapterCommand,
        WriteChapterCommand,
    )

    wc = get_write_chapter_use_case()
    rc = get_review_chapter_use_case()

    wc.execute(WriteChapterCommand(chapter=1, title="t", outline_ref="r", prompt="p"))
    rc.execute(ReviewChapterCommand(chapter=1, text="t", outline_ref="r"))

    events = list(shared_store.replay())
    # 至少 2 个事件 (write + review)；如果有之前的测试事件，可能更多
    assert len(events) >= 2