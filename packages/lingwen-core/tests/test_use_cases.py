"""Phase 18.2 守卫测试 — lingwen_core.use_cases 包结构与事件驱动契约。

Use-cases 接受 LLMPort/EventStorePort 端口依赖，
不直接 import DB / 文件系统。返回 DomainEvent 供上游订阅。
"""

from __future__ import annotations


def test_use_cases_package_importable():
    import lingwen_core.use_cases  # noqa: F401


# ─────────────────────────────────────────────────────────
# WriteChapterUseCase
# ─────────────────────────────────────────────────────────


def test_write_chapter_use_case_class():
    """WriteChapterUseCase 必须存在并接受 LLMPort + EventStorePort。"""
    from lingwen_core.use_cases.write_chapter import WriteChapterUseCase

    use_case = WriteChapterUseCase(llm=None, store=None)  # type: ignore[arg-type]
    assert use_case is not None


def test_write_chapter_emits_event():
    """execute() 调用 llm.complete 然后 append ChapterWrittenEvent。"""
    from lingwen_core.ports import EchoLLM, InMemoryEventStore
    from lingwen_core.use_cases.write_chapter import WriteChapterCommand, WriteChapterUseCase

    llm = EchoLLM()
    store = InMemoryEventStore()
    use_case = WriteChapterUseCase(llm=llm, store=store)

    cmd = WriteChapterCommand(
        chapter=1,
        title="开篇",
        outline_ref="out:1",
        prompt="写一个开篇",
    )
    event = use_case.execute(cmd)

    # 事件已 append 到 store
    events = list(store.replay())
    assert len(events) == 1
    assert events[0].type == "ChapterWritten"

    # 事件 payload 包含 chapter info
    assert event.payload["chapter"] == 1
    assert event.payload["title"] == "开篇"
    assert "text" in event.payload
    assert event.payload["text"] == "写一个开篇"  # EchoLLM 直接回显


def test_write_chapter_rejects_invalid_command():
    """execute() 对非法命令应抛 ValueError，不写入 event store。"""
    from lingwen_core.ports import EchoLLM, InMemoryEventStore
    from lingwen_core.use_cases.write_chapter import WriteChapterCommand, WriteChapterUseCase

    use_case = WriteChapterUseCase(llm=EchoLLM(), store=InMemoryEventStore())

    import pytest

    with pytest.raises(ValueError):
        use_case.execute(
            WriteChapterCommand(
                chapter=0,  # invalid
                title="t",
                outline_ref="r",
                prompt="p",
            )
        )


# ─────────────────────────────────────────────────────────
# ReviewChapterUseCase
# ─────────────────────────────────────────────────────────


def test_review_chapter_use_case_class():
    from lingwen_core.use_cases.review_chapter import ReviewChapterUseCase

    use_case = ReviewChapterUseCase(checkers=(), store=None)  # type: ignore[arg-type]
    assert use_case is not None


def test_review_chapter_emits_event():
    """execute() 调用所有 checker，返回 ChapterReviewedEvent。"""
    from lingwen_core.ports import (
        AlwaysPassChecker,
        InMemoryEventStore,
    )
    from lingwen_core.use_cases.review_chapter import ReviewChapterCommand, ReviewChapterUseCase

    checker = AlwaysPassChecker()
    store = InMemoryEventStore()
    use_case = ReviewChapterUseCase(checkers=[checker], store=store)

    cmd = ReviewChapterCommand(chapter=1, text="some text", outline_ref="out:1")
    event = use_case.execute(cmd)

    events = list(store.replay())
    assert len(events) == 1
    assert events[0].type == "ChapterReviewed"
    assert event.payload["chapter"] == 1
    assert event.payload["issue_count"] == 0


def test_review_chapter_aggregates_issues():
    """多个 checkers 的问题应聚合到 event payload。"""
    from lingwen_core.ports import (
        AlwaysPassChecker,
        InMemoryEventStore,
    )
    from lingwen_core.use_cases.review_chapter import ReviewChapterCommand, ReviewChapterUseCase

    class IssueRaisingChecker:
        def check(self, chapter: object) -> list[object]:
            return [{"severity": "P1", "msg": "x"}, {"severity": "P0", "msg": "y"}]

    use_case = ReviewChapterUseCase(
        checkers=[AlwaysPassChecker(), IssueRaisingChecker()],  # type: ignore[list-item]
        store=InMemoryEventStore(),
    )
    cmd = ReviewChapterCommand(chapter=1, text="x", outline_ref="r")
    event = use_case.execute(cmd)
    assert event.payload["issue_count"] == 2
    assert any(i["severity"] == "P0" for i in event.payload["issues"])


# ─────────────────────────────────────────────────────────
# MergeRipplesUseCase
# ─────────────────────────────────────────────────────────


def test_merge_ripples_use_case_class():
    from lingwen_core.use_cases.merge_ripples import MergeRipplesUseCase

    use_case = MergeRipplesUseCase(store=None)  # type: ignore[arg-type]
    assert use_case is not None


def test_merge_ripples_emits_state_changed_event():
    """execute() 推进 ripple 状态 + emit RippleStateChangedEvent。"""
    from lingwen_core.domain import Ripple, RippleState
    from lingwen_core.ports import InMemoryEventStore
    from lingwen_core.use_cases.merge_ripples import MergeRipplesUseCase

    store = InMemoryEventStore()
    use_case = MergeRipplesUseCase(store=store)

    r = Ripple(
        ripple_id="r:1",
        origin_event="事件X",
        origin_ch=5,
        state=RippleState.PROPAGATING,
    )
    event = use_case.merge_to_state(r, RippleState.RESOLVING)

    assert event.type == "RippleStateChanged"
    assert event.payload["ripple_id"] == "r:1"
    assert event.payload["from_state"] == "propagating"
    assert event.payload["to_state"] == "resolving"

    events = list(store.replay())
    assert len(events) == 1
    assert events[0].type == "RippleStateChanged"


def test_merge_ripples_validates_transition():
    """不允许非法状态跃迁（如 RESOLVED → OPEN）。"""
    import pytest
    from lingwen_core.domain import Ripple, RippleState
    from lingwen_core.ports import InMemoryEventStore
    from lingwen_core.use_cases.merge_ripples import MergeRipplesUseCase

    use_case = MergeRipplesUseCase(store=InMemoryEventStore())
    r = Ripple(
        ripple_id="r:1",
        origin_event="e",
        origin_ch=1,
        state=RippleState.RESOLVED,
    )

    with pytest.raises(ValueError, match="transition"):
        use_case.merge_to_state(r, RippleState.OPEN)


# ─────────────────────────────────────────────────────────
# use_cases init
# ─────────────────────────────────────────────────────────


def test_use_cases_init_exports_all():
    import lingwen_core.use_cases as uc

    for name in [
        "WriteChapterUseCase",
        "WriteChapterCommand",
        "ReviewChapterUseCase",
        "ReviewChapterCommand",
        "MergeRipplesUseCase",
    ]:
        assert hasattr(uc, name), f"missing: {name}"
