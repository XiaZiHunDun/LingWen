"""Tests for world_model.snapshot_diff (Phase 2.6 — SnapshotDiff).

Doc 1 §3.4 + Doc 3 联动:
- diff_snapshots(prev, curr): 检测 5 类别变化 (node/relation/ripple/subplot/mood) + 2 delta (physical/mental)
- diff_ripples: 单独导出,常用 (state 变化 + wavefront 增删)
- diff_subplots: 单独导出
- has_state_transition: 便捷查询

主键约定:
- NODE: str(NodeId) (e.g. "CHARACTER:林尘")
- RELATION: "src→dst" 字符串
- RIPPLE: ripple_id
- SUBPLOT: plot_id
- MOOD: "world_mood" (单一值)

MODIFIED 字段:tuple[(field, before, after), ...]
"""
from __future__ import annotations

from datetime import datetime

import pytest

from infra.world_model.data_structures import (
    KeyPoint,
    MentalLine,
    NodeId,
    NodeType,
    PhysicalLine,
    Ripple,
    RippleState,
    WorldSnapshot,
)
from infra.world_model.snapshot_diff import (
    ChangeKind,
    EntityKind,
    SnapshotChange,
    diff_ripples,
    diff_snapshots,
    diff_subplots,
    has_state_transition,
)

# === Helpers ===

def _make_snap(
    chapter: int = 1,
    nodes: dict | None = None,
    active_ripples: tuple[Ripple, ...] = (),
    active_subplots: tuple = (),
    world_mood: str = "neutral",
    physical: PhysicalLine | None = None,
    mental: MentalLine | None = None,
    relations: tuple = (),
) -> WorldSnapshot:
    return WorldSnapshot(
        snapshot_id=f"snap_ch{chapter:04d}",
        chapter=chapter,
        timestamp=datetime(2026, 6, 3, 12, 0, 0),
        nodes=nodes or {},
        relations=relations,
        physical=physical or PhysicalLine(ch=chapter),
        mental=mental or MentalLine(ch=chapter),
        active_ripples=active_ripples,
        active_subplots=active_subplots,
        world_mood=world_mood,
    )


def _ripple(ripple_id: str, state: RippleState = RippleState.OPEN, ch: int = 10) -> Ripple:
    return Ripple(
        ripple_id=ripple_id,
        origin_event="e",
        origin_ch=ch,
        state=state,
        planned_resolve_ch=ch + 100,
    )


def _node(name: str) -> NodeId:
    return NodeId(NodeType.CHARACTER, name)


# === TestEmptyDiff ===

class TestEmptyDiff:
    def test_identical_snapshots_no_diff(self):
        s1 = _make_snap(chapter=10, world_mood="tense")
        s2 = _make_snap(chapter=10, world_mood="tense")
        # hash will differ (timestamp identical → same), but logic diff is empty
        # Actually hash is computed from content, so identical content = identical hash
        # But __post_init__ re-computes hash on each instance, so two separate _make_snap
        # calls may produce same hash. We just check diff_snapshots returns no LOGICAL changes.
        changes = diff_snapshots(s1, s2)
        assert changes == ()

    def test_empty_snapshots_no_diff(self):
        s1 = _make_snap(chapter=1)
        s2 = _make_snap(chapter=1)
        assert diff_snapshots(s1, s2) == ()


# === TestNodeDiff ===

class TestNodeDiff:
    def test_node_added(self):
        s1 = _make_snap(chapter=10)
        s2 = _make_snap(
            chapter=10,
            nodes={_node("林尘"): KeyPoint(id=NodeId(NodeType.CHARACTER, "林尘"), attrs={"role": "主角"})},
        )
        changes = diff_snapshots(s1, s2)
        assert len(changes) == 1
        c = changes[0]
        assert c.kind == ChangeKind.ADDED
        assert c.entity == EntityKind.NODE
        assert c.entity_id == "character:林尘"

    def test_node_removed(self):
        s1 = _make_snap(
            chapter=10,
            nodes={_node("林尘"): KeyPoint(id=NodeId(NodeType.CHARACTER, "林尘"), attrs={"role": "主角"})},
        )
        s2 = _make_snap(chapter=10)
        changes = diff_snapshots(s1, s2)
        assert len(changes) == 1
        c = changes[0]
        assert c.kind == ChangeKind.REMOVED
        assert c.entity == EntityKind.NODE


# === TestRippleDiff ===

class TestRippleDiff:
    def test_ripple_added(self):
        s1 = _make_snap(chapter=10)
        s2 = _make_snap(chapter=10, active_ripples=(_ripple("r1"),))
        changes = diff_snapshots(s1, s2)
        ripple_changes = [c for c in changes if c.entity == EntityKind.RIPPLE]
        assert len(ripple_changes) == 1
        assert ripple_changes[0].kind == ChangeKind.ADDED
        assert ripple_changes[0].entity_id == "r1"

    def test_ripple_removed(self):
        s1 = _make_snap(chapter=10, active_ripples=(_ripple("r1"),))
        s2 = _make_snap(chapter=10)
        changes = diff_snapshots(s1, s2)
        ripple_changes = [c for c in changes if c.entity == EntityKind.RIPPLE]
        assert len(ripple_changes) == 1
        assert ripple_changes[0].kind == ChangeKind.REMOVED

    def test_ripple_state_change_modified(self):
        """OPEN → PROPAGATING 状态变化 → MODIFIED + field_changes"""
        s1 = _make_snap(chapter=50, active_ripples=(_ripple("r1", RippleState.OPEN),))
        s2 = _make_snap(
            chapter=50,
            active_ripples=(_ripple("r1", RippleState.PROPAGATING),),
        )
        changes = diff_snapshots(s1, s2)
        ripple_changes = [c for c in changes if c.entity == EntityKind.RIPPLE]
        assert len(ripple_changes) == 1
        c = ripple_changes[0]
        assert c.kind == ChangeKind.MODIFIED
        # field_changes 应含 ("state", OPEN, PROPAGATING)
        state_change = next(
            (fc for fc in c.field_changes if fc[0] == "state"), None
        )
        assert state_change is not None
        assert state_change[1] == RippleState.OPEN
        assert state_change[2] == RippleState.PROPAGATING

    def test_ripple_resolved_marked_resolved(self):
        """OPEN → RESOLVED 状态变化 → MODIFIED + state 字段变化"""
        s1 = _make_snap(chapter=200, active_ripples=(_ripple("r1", RippleState.OPEN),))
        s2 = _make_snap(
            chapter=200,
            active_ripples=(_ripple("r1", RippleState.RESOLVED),),
        )
        changes = diff_ripples(s1, s2)
        assert len(changes) == 1
        assert changes[0].kind == ChangeKind.MODIFIED
        assert any(fc[0] == "state" for fc in changes[0].field_changes)

    def test_diff_ripples_filters_to_ripple_only(self):
        """diff_ripples 只返回 ripple 类别,排除 node/subplot/mood"""
        s1 = _make_snap(
            chapter=10,
            nodes={_node("林尘"): KeyPoint(id=NodeId(NodeType.CHARACTER, "林尘"), attrs={"role": "主角"})},
            active_ripples=(_ripple("r1"),),
        )
        s2 = _make_snap(
            chapter=10,
            active_ripples=(_ripple("r2"),),
        )
        changes = diff_ripples(s1, s2)
        assert all(c.entity == EntityKind.RIPPLE for c in changes)
        assert len(changes) == 2  # r1 removed + r2 added


# === TestMoodDiff ===

class TestMoodDiff:
    def test_mood_change_modified(self):
        s1 = _make_snap(chapter=10, world_mood="neutral")
        s2 = _make_snap(chapter=10, world_mood="tense")
        changes = diff_snapshots(s1, s2)
        mood_changes = [c for c in changes if c.entity == EntityKind.MOOD]
        assert len(mood_changes) == 1
        c = mood_changes[0]
        assert c.kind == ChangeKind.MODIFIED
        assert c.entity_id == "world_mood"
        assert c.field_changes == (("value", "neutral", "tense"),)


# === TestHasStateTransition ===

class TestHasStateTransition:
    def test_finds_state_transition(self):
        s1 = _make_snap(chapter=10, active_ripples=(_ripple("r1", RippleState.OPEN),))
        s2 = _make_snap(
            chapter=10,
            active_ripples=(_ripple("r1", RippleState.PROPAGATING),),
        )
        changes = diff_ripples(s1, s2)
        assert has_state_transition(
            changes, "r1", RippleState.OPEN, RippleState.PROPAGATING
        ) is True

    def test_returns_false_for_wrong_transition(self):
        s1 = _make_snap(chapter=10, active_ripples=(_ripple("r1", RippleState.OPEN),))
        s2 = _make_snap(
            chapter=10,
            active_ripples=(_ripple("r1", RippleState.PROPAGATING),),
        )
        changes = diff_ripples(s1, s2)
        # r1 没有 OPEN→RESOLVED 转换
        assert has_state_transition(
            changes, "r1", RippleState.OPEN, RippleState.RESOLVED
        ) is False

    def test_returns_false_for_missing_ripple(self):
        changes = ()
        assert has_state_transition(
            changes, "ghost", RippleState.OPEN, RippleState.RESOLVED
        ) is False


# === TestMultipleEntities ===

class TestMultipleEntities:
    def test_mixed_changes_all_categories(self):
        """node + ripple + subplot + mood 都有变化 → 至少 4 changes"""
        s1 = _make_snap(chapter=10)
        s2 = _make_snap(
            chapter=10,
            nodes={_node("林尘"): KeyPoint(id=NodeId(NodeType.CHARACTER, "林尘"), attrs={"role": "主角"})},
            active_ripples=(_ripple("r1"),),
            world_mood="tense",
        )
        changes = diff_snapshots(s1, s2)
        kinds = {c.entity for c in changes}
        assert EntityKind.NODE in kinds
        assert EntityKind.RIPPLE in kinds
        assert EntityKind.MOOD in kinds


# === TestChangeMetadata ===

class TestChangeMetadata:
    def test_snapshot_change_is_frozen(self):
        """frozen dataclass 不可变"""
        c = SnapshotChange(
            kind=ChangeKind.ADDED,
            entity=EntityKind.RIPPLE,
            entity_id="r1",
        )
        with pytest.raises((AttributeError, Exception)):
            c.kind = ChangeKind.REMOVED  # type: ignore[misc]

    def test_change_kinds_enum_values(self):
        assert ChangeKind.ADDED.value == "added"
        assert ChangeKind.REMOVED.value == "removed"
        assert ChangeKind.MODIFIED.value == "modified"

    def test_entity_kinds_enum_values(self):
        assert EntityKind.RIPPLE.value == "ripple"
        assert EntityKind.SUBPLOT.value == "subplot"
        assert EntityKind.MOOD.value == "mood"
