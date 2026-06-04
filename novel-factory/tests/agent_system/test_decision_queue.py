"""Tests for infra.agent_system.decision_queue (Phase 4.2)

Doc 4 (GoT 适配设计 v1.0) §10: 决策点管理
- 7 种 DecisionKind (outline_judgment, volume_judgment, chapter_iteration_judgment,
  publish_judgment, subplot_open, subplot_close, style_pick)
- HumanDecisionQueue: 增删查 + 排序 (priority desc + due_at asc) + 持久化
- HumanDecision: frozen dataclass (含 status 转换 PENDING → RESOLVED/DEFERRED/CANCELLED)
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from infra.agent_system.decision_queue import (
    DecisionKind,
    DecisionStatus,
    HumanDecision,
    HumanDecisionQueue,
    create_decision,
)

# === Test fixtures ===

def _mk_decision(
    kind: DecisionKind = DecisionKind.OUTLINE_JUDGMENT,
    priority: int = 5,
    due_at: datetime | None = None,
    node_id: str = "outline_judge",
    options: tuple[str, ...] = ("approve", "revise"),
    prompt: str = "大纲是否通过?",
) -> HumanDecision:
    return create_decision(
        decision_kind=kind,
        node_id=node_id,
        prompt=prompt,
        options=options,
        priority=priority,
        due_at=due_at,
    )


# === TestHumanDecisionBasic ===

class TestHumanDecisionBasic:
    """HumanDecision dataclass 基础 + factory"""

    def test_create_decision_returns_frozen_dataclass(self):
        d = _mk_decision()
        assert d.decision_id  # uuid 短串
        assert d.decision_kind == DecisionKind.OUTLINE_JUDGMENT
        assert d.status == DecisionStatus.PENDING
        assert d.options == ("approve", "revise")
        assert d.priority == 5

    def test_create_decision_generates_unique_ids(self):
        a = _mk_decision()
        b = _mk_decision()
        assert a.decision_id != b.decision_id

    def test_decision_is_frozen(self):
        d = _mk_decision()
        with pytest.raises(Exception):  # FrozenInstanceError
            d.priority = 99  # type: ignore[misc]

    def test_create_decision_with_due_at(self):
        due = datetime(2026, 6, 10, 12, 0, 0)
        d = _mk_decision(due_at=due)
        assert d.due_at == due

    def test_create_decision_default_due_at_is_none(self):
        d = _mk_decision()
        assert d.due_at is None

    def test_decision_to_dict(self):
        d = _mk_decision()
        data = d.to_dict()
        assert data["decision_id"] == d.decision_id
        assert data["decision_kind"] == d.decision_kind.value
        assert data["status"] == d.status.value

    def test_decision_from_dict_roundtrip(self):
        d = _mk_decision()
        data = d.to_dict()
        d2 = HumanDecision.from_dict(data)
        assert d2.decision_id == d.decision_id
        assert d2.decision_kind == d.decision_kind
        assert d2.priority == d.priority

    def test_all_seven_kinds_createable(self):
        """Doc 4 §10 列出 7 种决策点,全部能创建"""
        for kind in DecisionKind:
            d = _mk_decision(kind=kind)
            assert d.decision_kind == kind


# === TestQueueAddAndGet ===

class TestQueueAddAndGet:
    """HumanDecisionQueue.add + get 基础"""

    def test_add_stores_decision(self):
        q = HumanDecisionQueue()
        d = _mk_decision()
        q.add(d)
        assert q.get(d.decision_id) == d

    def test_get_missing_raises_key_error(self):
        q = HumanDecisionQueue()
        with pytest.raises(KeyError):
            q.get("nonexistent_xyz")

    def test_contains_operator(self):
        q = HumanDecisionQueue()
        d = _mk_decision()
        q.add(d)
        assert d.decision_id in q
        assert "nope" not in q

    def test_add_duplicate_id_is_idempotent(self):
        """重复 add 同 id 不应抛错,只保留第一次"""
        q = HumanDecisionQueue()
        d = _mk_decision()
        q.add(d)
        q.add(d)  # 不抛错
        assert q.pending_count() == 1


# === TestQueuePendingSorting ===

class TestQueuePendingSorting:
    """pending() 按 priority desc + due_at asc 排序"""

    def test_pending_returns_only_pending(self):
        q = HumanDecisionQueue()
        d1 = _mk_decision(priority=5)
        d2 = _mk_decision(priority=10)
        q.add(d1)
        q.add(d2)
        pending = q.pending()
        assert d1 in pending
        assert d2 in pending
        assert len(pending) == 2

    def test_pending_sort_priority_desc(self):
        q = HumanDecisionQueue()
        low = _mk_decision(priority=1)
        high = _mk_decision(priority=10)
        mid = _mk_decision(priority=5)
        q.add(low)
        q.add(high)
        q.add(mid)
        ordered = q.pending()
        assert ordered[0] == high
        assert ordered[1] == mid
        assert ordered[2] == low

    def test_pending_sort_due_at_asc_within_same_priority(self):
        q = HumanDecisionQueue()
        early = _mk_decision(priority=5, due_at=datetime(2026, 6, 5, 0, 0, 0))
        late = _mk_decision(priority=5, due_at=datetime(2026, 6, 10, 0, 0, 0))
        q.add(late)
        q.add(early)
        ordered = q.pending()
        assert ordered[0] == early
        assert ordered[1] == late

    def test_pending_excludes_resolved(self):
        q = HumanDecisionQueue()
        d = _mk_decision(priority=5)
        q.add(d)
        q.resolve(d.decision_id, "approve")
        assert q.pending() == []

    def test_pending_excludes_deferred(self):
        q = HumanDecisionQueue()
        d = _mk_decision(priority=5)
        q.add(d)
        q.defer(d.decision_id, reason="not now")
        assert d.decision_id not in [p.decision_id for p in q.pending()]


# === TestQueueResolve ===

class TestQueueResolve:
    """resolve() 标记 RESOLVED + 记录选项"""

    def test_resolve_changes_status(self):
        q = HumanDecisionQueue()
        d = _mk_decision()
        q.add(d)
        resolved = q.resolve(d.decision_id, "approve")
        assert resolved.status == DecisionStatus.RESOLVED
        assert resolved.resolution == "approve"

    def test_resolve_records_resolved_by(self):
        q = HumanDecisionQueue()
        d = _mk_decision()
        q.add(d)
        resolved = q.resolve(d.decision_id, "approve", resolved_by="editor")
        assert resolved.resolved_by == "editor"

    def test_resolve_records_resolved_at(self):
        q = HumanDecisionQueue()
        d = _mk_decision()
        q.add(d)
        resolved = q.resolve(d.decision_id, "approve")
        assert resolved.resolved_at is not None

    def test_resolve_unknown_raises_key_error(self):
        q = HumanDecisionQueue()
        with pytest.raises(KeyError):
            q.resolve("nonexistent_xyz", "approve")

    def test_resolve_invalid_option_raises(self):
        """option 不在 options 中 → ValueError"""
        q = HumanDecisionQueue()
        d = _mk_decision(options=("approve", "revise"))
        q.add(d)
        with pytest.raises(ValueError):
            q.resolve(d.decision_id, "bad_option")

    def test_resolve_already_resolved_raises(self):
        """重复 resolve → ValueError"""
        q = HumanDecisionQueue()
        d = _mk_decision()
        q.add(d)
        q.resolve(d.decision_id, "approve")
        with pytest.raises(ValueError):
            q.resolve(d.decision_id, "revise")


# === TestQueueDeferAndCancel ===

class TestQueueDeferAndCancel:
    """defer() / cancel() 状态转换"""

    def test_defer_changes_status(self):
        q = HumanDecisionQueue()
        d = _mk_decision()
        q.add(d)
        deferred = q.defer(d.decision_id, reason="等主编意见")
        assert deferred.status == DecisionStatus.DEFERRED

    def test_defer_records_reason(self):
        q = HumanDecisionQueue()
        d = _mk_decision()
        q.add(d)
        deferred = q.defer(d.decision_id, reason="下周再审")
        assert deferred.reason == "下周再审"

    def test_cancel_changes_status(self):
        q = HumanDecisionQueue()
        d = _mk_decision()
        q.add(d)
        cancelled = q.cancel(d.decision_id)
        assert cancelled.status == DecisionStatus.CANCELLED

    def test_cancel_excludes_from_pending(self):
        q = HumanDecisionQueue()
        d = _mk_decision()
        q.add(d)
        q.cancel(d.decision_id)
        assert q.pending_count() == 0


# === TestQueuePersistence ===

class TestQueuePersistence:
    """JSON 持久化 (state_dir/decisions.json)"""

    def test_persistence_roundtrip(self, tmp_path: Path):
        # 写
        q1 = HumanDecisionQueue(state_dir=str(tmp_path))
        d1 = _mk_decision(priority=7)
        d2 = _mk_decision(priority=3, kind=DecisionKind.STYLE_PICK)
        q1.add(d1)
        q1.add(d2)
        q1.save()

        # 读
        q2 = HumanDecisionQueue(state_dir=str(tmp_path))
        assert q2.pending_count() == 2
        ids = {d.decision_id for d in q2.pending()}
        assert d1.decision_id in ids
        assert d2.decision_id in ids

    def test_persistence_preserves_resolved_status(self, tmp_path: Path):
        q1 = HumanDecisionQueue(state_dir=str(tmp_path))
        d = _mk_decision()
        q1.add(d)
        q1.resolve(d.decision_id, "approve")
        q1.save()

        q2 = HumanDecisionQueue(state_dir=str(tmp_path))
        loaded = q2.get(d.decision_id)
        assert loaded.status == DecisionStatus.RESOLVED
        assert loaded.resolution == "approve"

    def test_persistence_file_path_default(self, tmp_path: Path):
        q = HumanDecisionQueue(state_dir=str(tmp_path))
        d = _mk_decision()
        q.add(d)
        q.save()
        expected = tmp_path / "decisions.json"
        assert expected.exists()

    def test_persistence_handles_missing_file(self, tmp_path: Path):
        """无文件 → 空 queue,不抛错"""
        q = HumanDecisionQueue(state_dir=str(tmp_path))
        assert q.pending_count() == 0

    def test_persistence_handles_corrupt_file(self, tmp_path: Path):
        """损坏文件 → 空 queue,记录 warning,不抛错"""
        path = tmp_path / "decisions.json"
        path.write_text("{not valid json")
        q = HumanDecisionQueue(state_dir=str(tmp_path))
        assert q.pending_count() == 0


# === TestQueueStats ===

class TestQueueStats:
    """队列统计 (pending_count / by_status)"""

    def test_pending_count_starts_zero(self):
        q = HumanDecisionQueue()
        assert q.pending_count() == 0

    def test_pending_count_after_add(self):
        q = HumanDecisionQueue()
        q.add(_mk_decision())
        q.add(_mk_decision())
        assert q.pending_count() == 2

    def test_total_count_includes_all_statuses(self):
        q = HumanDecisionQueue()
        d1 = _mk_decision()
        d2 = _mk_decision()
        d3 = _mk_decision()
        q.add(d1)
        q.add(d2)
        q.add(d3)
        q.resolve(d1.decision_id, "approve")
        q.cancel(d2.decision_id)
        # d3 still pending
        assert q.pending_count() == 1
        assert q.total_count() == 3

    def test_count_by_status(self):
        q = HumanDecisionQueue()
        d1 = _mk_decision()
        d2 = _mk_decision()
        d3 = _mk_decision()
        d4 = _mk_decision()
        q.add(d1)
        q.add(d2)
        q.add(d3)
        q.add(d4)
        q.resolve(d1.decision_id, "approve")
        q.defer(d2.decision_id, reason="r")
        q.cancel(d3.decision_id)
        # d4 pending
        stats = q.count_by_status()
        assert stats[DecisionStatus.PENDING.value] == 1
        assert stats[DecisionStatus.RESOLVED.value] == 1
        assert stats[DecisionStatus.DEFERRED.value] == 1
        assert stats[DecisionStatus.CANCELLED.value] == 1
