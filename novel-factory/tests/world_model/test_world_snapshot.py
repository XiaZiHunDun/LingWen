"""Tests for world_model.data_structures.

Phase 1.1.a — RED tests for NodeId, KeyPoint, Relation, PhysicalLine,
MentalLine, Ripple, WorldSnapshot. Cover immutability (frozen) and
to_dict / from_dict roundtrip so that JSON persistence and inter-process
exchange both work.

Phase 1.5.a — Ripple extended with state/wavefront/decay_rate/affected_relations/
planned_resolve_ch fields (Doc 1 §3.4). Backward-compatible with legacy JSON.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from infra.world_model.data_structures import (
    KeyPoint,
    MentalLine,
    NodeId,
    NodeType,
    PhysicalLine,
    PlotStatus,
    Relation,
    ResolutionMode,
    Ripple,
    RippleState,
    WorldSnapshot,
)


class TestNodeId:
    def test_node_id_is_frozen(self):
        nid = NodeId(NodeType.CHARACTER, "林尘")
        with pytest.raises(FrozenInstanceError):
            nid.name = "其他人"  # type: ignore[misc]

    def test_node_id_str_format(self):
        nid = NodeId(NodeType.CHARACTER, "林尘")
        assert str(nid) == "character:林尘"

    def test_node_id_equality(self):
        a = NodeId(NodeType.CHARACTER, "林尘")
        b = NodeId(NodeType.CHARACTER, "林尘")
        c = NodeId(NodeType.LOCATION, "林尘")
        assert a == b
        assert hash(a) == hash(b)
        assert a != c


class TestKeyPoint:
    def test_keypoint_default_status_is_active(self):
        kp = KeyPoint(id=NodeId(NodeType.CHARACTER, "林尘"))
        assert kp.status == "active"

    def test_keypoint_to_dict_roundtrip(self):
        kp = KeyPoint(
            id=NodeId(NodeType.CHARACTER, "林尘"),
            attrs={"age": 18, "realm": "炼气"},
            status="active",
            first_ch=1,
            last_ch=10,
        )
        d = kp.to_dict()
        restored = KeyPoint.from_dict(d)
        assert restored == kp

    def test_keypoint_to_dict_uses_string_node_id(self):
        kp = KeyPoint(id=NodeId(NodeType.CHARACTER, "林尘"))
        d = kp.to_dict()
        assert d["id"] == "character:林尘"
        assert d["type"] == "character"


class TestRelation:
    def test_relation_to_dict_roundtrip(self):
        rel = Relation(
            src=NodeId(NodeType.CHARACTER, "林尘"),
            dst=NodeId(NodeType.LOCATION, "星月宗"),
            type="located_in",
            weight=1.0,
            first_ch=1,
            last_ch=10,
        )
        d = rel.to_dict()
        restored = Relation.from_dict(d)
        assert restored == rel

    def test_relation_default_weight(self):
        rel = Relation(
            src=NodeId(NodeType.CHARACTER, "林尘"),
            dst=NodeId(NodeType.CHARACTER, "师父"),
            type="knows",
        )
        assert rel.weight == 1.0


class TestPhysicalLine:
    def test_physical_line_to_dict_roundtrip(self):
        pl = PhysicalLine(
            ch=5,
            actions=["入山", "遇敌"],
            locations=[NodeId(NodeType.LOCATION, "玄域")],
            events=["裂爪兽出现"],
            constraints=["受轻伤"],
        )
        d = pl.to_dict()
        restored = PhysicalLine.from_dict(d)
        assert restored == pl

    def test_physical_line_default_empty(self):
        pl = PhysicalLine(ch=1)
        assert pl.actions == []
        assert pl.locations == []
        assert pl.events == []


class TestMentalLine:
    def test_mental_line_to_dict_roundtrip(self):
        ml = MentalLine(
            ch=5,
            thoughts=["疑惑"],
            emotions={NodeId(NodeType.CHARACTER, "林尘"): "tense"},
            arc_progress={NodeId(NodeType.CHARACTER, "林尘"): 0.3},
            growth_signals=["开始怀疑师父"],
        )
        d = ml.to_dict()
        restored = MentalLine.from_dict(d)
        assert restored == ml


class TestRipple:
    def test_ripple_default_unresolved(self):
        r = Ripple(
            ripple_id="ripple_001",
            origin_event="星月之子身世",
            origin_ch=10,
            affected_nodes=[NodeId(NodeType.CHARACTER, "林尘")],
        )
        assert r.resolved_ch is None
        assert r.collapse_risk == 0.0

    def test_ripple_to_dict_roundtrip(self):
        r = Ripple(
            ripple_id="ripple_001",
            origin_event="星月之子身世",
            origin_ch=10,
            affected_nodes=(
                NodeId(NodeType.CHARACTER, "林尘"),
                NodeId(NodeType.FACTION, "星月宗"),
            ),
            resolved_ch=200,
            collapse_risk=0.2,
        )
        d = r.to_dict()
        restored = Ripple.from_dict(d)
        assert restored == r

    # === Phase 1.5.a — extended fields ===

    def test_ripple_state_default_open(self):
        r = Ripple(ripple_id="r1", origin_event="e", origin_ch=1)
        assert r.state == RippleState.OPEN

    def test_ripple_wavefront_default_empty(self):
        r = Ripple(ripple_id="r1", origin_event="e", origin_ch=1)
        assert r.wavefront == ()

    def test_ripple_decay_rate_default_0_2(self):
        r = Ripple(ripple_id="r1", origin_event="e", origin_ch=1)
        assert r.decay_rate == 0.2

    def test_ripple_affected_relations_default_empty(self):
        r = Ripple(ripple_id="r1", origin_event="e", origin_ch=1)
        assert r.affected_relations == ()

    def test_ripple_planned_resolve_ch_default_none(self):
        r = Ripple(ripple_id="r1", origin_event="e", origin_ch=1)
        assert r.planned_resolve_ch is None

    def test_ripple_extended_to_dict_roundtrip(self):
        r = Ripple(
            ripple_id="r1",
            origin_event="e",
            origin_ch=10,
            state=RippleState.PROPAGATING,
            wavefront=(10, 50, 100),
            decay_rate=0.3,
            affected_relations=(
                Relation(
                    src=NodeId(NodeType.CHARACTER, "林尘"),
                    dst=NodeId(NodeType.CHARACTER, "暗皇"),
                    type="opposed_to",
                    first_ch=10,
                ),
            ),
            planned_resolve_ch=200,
        )
        d = r.to_dict()
        assert d["state"] == "propagating"
        assert d["wavefront"] == [10, 50, 100]
        assert d["decay_rate"] == 0.3
        assert d["planned_resolve_ch"] == 200
        restored = Ripple.from_dict(d)
        assert restored == r

    def test_ripple_legacy_from_dict_omits_new_fields(self):
        """旧 JSON (Phase 1.1 持久化文件) 不含新字段,Ripple.from_dict 必须兼容"""
        legacy = {
            "ripple_id": "ripple_legacy",
            "origin_event": "e",
            "origin_ch": 1,
            "affected_nodes": [],
            "resolved_ch": None,
            "collapse_risk": 0.0,
        }
        r = Ripple.from_dict(legacy)
        assert r.ripple_id == "ripple_legacy"
        assert r.state == RippleState.OPEN  # default
        assert r.wavefront == ()  # default
        assert r.decay_rate == 0.2  # default
        assert r.affected_relations == ()  # default
        assert r.planned_resolve_ch is None  # default


class TestPlotStatus:
    def test_plot_status_values(self):
        # PlotStatus 是 Phase 1.3 才会用, 这里只保证枚举稳定
        assert PlotStatus.ACTIVE.value == "active"
        assert PlotStatus.CLOSED.value == "closed"
        assert PlotStatus.ABANDONED.value == "abandoned"


class TestWorldSnapshot:
    def _build_snapshot(self) -> WorldSnapshot:
        return WorldSnapshot(
            snapshot_id="ch0001_v1",
            chapter=1,
            timestamp=datetime(2026, 5, 21, 10, 0, 0),
            nodes={
                NodeId(NodeType.CHARACTER, "林尘"): KeyPoint(
                    id=NodeId(NodeType.CHARACTER, "林尘"),
                    attrs={"age": 18},
                ),
                NodeId(NodeType.LOCATION, "星月宗"): KeyPoint(
                    id=NodeId(NodeType.LOCATION, "星月宗"),
                ),
            },
            relations=(
                Relation(
                    src=NodeId(NodeType.CHARACTER, "林尘"),
                    dst=NodeId(NodeType.LOCATION, "星月宗"),
                    type="located_in",
                ),
            ),
            physical=PhysicalLine(ch=1, actions=["入门"]),
            mental=MentalLine(ch=1, thoughts=["期待"]),
            active_ripples=(),
            world_mood="neutral",
        )

    def test_world_snapshot_to_dict_roundtrip(self):
        snap = self._build_snapshot()
        d = snap.to_dict()
        restored = WorldSnapshot.from_dict(d)
        # relations/ripples 是 tuple (用于 frozen dataclass),但 dict
        # 走 from_dict 回来时也是 tuple,相等性应成立
        assert restored == snap

    def test_world_snapshot_consistency_hash_changes_with_content(self):
        snap1 = self._build_snapshot()
        hash1 = snap1.compute_consistency_hash()

        # 修改一个 node
        snap2_nodes = dict(snap1.nodes)
        snap2_nodes[NodeId(NodeType.CHARACTER, "林尘")] = KeyPoint(
            id=NodeId(NodeType.CHARACTER, "林尘"),
            attrs={"age": 19},  # 改了
        )
        snap2 = WorldSnapshot(
            snapshot_id=snap1.snapshot_id,
            chapter=snap1.chapter,
            timestamp=snap1.timestamp,
            nodes=snap2_nodes,
            relations=snap1.relations,
            physical=snap1.physical,
            mental=snap1.mental,
            active_ripples=snap1.active_ripples,
            world_mood=snap1.world_mood,
        )
        hash2 = snap2.compute_consistency_hash()

        # frozen dataclass 不能直接 reassign consistency_hash,
        # 但新实例应该产生新 hash
        assert hash1 != hash2
        assert len(hash1) == 16  # 16-char prefix of sha256
        assert len(hash2) == 16

    def test_world_snapshot_to_dict_serializes_timestamp(self):
        snap = self._build_snapshot()
        d = snap.to_dict()
        assert isinstance(d["timestamp"], str)
        assert "2026-05-21" in d["timestamp"]
