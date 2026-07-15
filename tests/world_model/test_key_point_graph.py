"""Tests for world_model.key_point_graph.

Phase 1.1.c — RED tests for KeyPointGraph N² contradiction detection.

N² scan is O(N²) on number of nodes (~100 max), so 1 chapter scan
should finish in <10ms. The first phase detector should catch at least:

1. active character located_in a destroyed location
2. destroyed character (entity) appearing in active relations
3. destroyed artifact owned by active character (only if weight > 0)
4. no false positives on legitimate states
"""
from __future__ import annotations

from datetime import datetime

import pytest

from infra.world_model.data_structures import (
    KeyPoint,
    NodeId,
    NodeType,
    Relation,
    WorldSnapshot,
)
from infra.world_model.key_point_graph import (
    Contradiction,
    ContradictionKind,
    KeyPointGraph,
)


def _kp(type_: NodeType, name: str, status: str = "active") -> KeyPoint:
    return KeyPoint(id=NodeId(type_, name), status=status)


def _rel(src_type: NodeType, src: str, dst_type: NodeType, dst: str, rel_type: str) -> Relation:
    return Relation(
        src=NodeId(src_type, src),
        dst=NodeId(dst_type, dst),
        type=rel_type,
    )


class TestKeyPointGraphBasic:
    def test_empty_graph_has_no_contradictions(self):
        g = KeyPointGraph()
        assert list(g.detect_contradictions()) == []

    def test_add_node_then_get(self):
        g = KeyPointGraph()
        kp = _kp(NodeType.CHARACTER, "林尘")
        g.add_node(kp)
        assert g.get_node(NodeId(NodeType.CHARACTER, "林尘")) == kp

    def test_add_relation_then_get(self):
        g = KeyPointGraph()
        g.add_node(_kp(NodeType.CHARACTER, "林尘"))
        g.add_node(_kp(NodeType.LOCATION, "星月宗"))
        rel = _rel(NodeType.CHARACTER, "林尘", NodeType.LOCATION, "星月宗", "located_in")
        g.add_relation(rel)
        assert g.relations_of(NodeId(NodeType.CHARACTER, "林尘")) == [rel]

    def test_node_count_and_relation_count(self):
        g = KeyPointGraph()
        g.add_node(_kp(NodeType.CHARACTER, "林尘"))
        g.add_node(_kp(NodeType.LOCATION, "星月宗"))
        g.add_relation(_rel(NodeType.CHARACTER, "林尘", NodeType.LOCATION, "星月宗", "located_in"))
        assert g.node_count() == 2
        assert g.relation_count() == 1

    def test_get_missing_node_returns_none(self):
        g = KeyPointGraph()
        assert g.get_node(NodeId(NodeType.CHARACTER, "不存在")) is None


class TestContradictionDetected:
    def test_active_character_located_in_destroyed_location(self):
        """玄幻常见: 角色"在玄域",但玄域已毁于 N 章前"""
        g = KeyPointGraph()
        g.add_node(_kp(NodeType.CHARACTER, "林尘"))  # active
        g.add_node(_kp(NodeType.LOCATION, "玄域", status="destroyed"))
        g.add_relation(_rel(NodeType.CHARACTER, "林尘", NodeType.LOCATION, "玄域", "located_in"))
        cs = list(g.detect_contradictions())
        assert len(cs) == 1
        c = cs[0]
        assert c.kind == ContradictionKind.LOCATED_IN_DESTROYED
        assert c.node_a == NodeId(NodeType.CHARACTER, "林尘")
        assert c.node_b == NodeId(NodeType.LOCATION, "玄域")

    def test_destroyed_character_has_active_knows_relation(self):
        """师父已死,但还"认识"某人 (weight=1)"""
        g = KeyPointGraph()
        g.add_node(_kp(NodeType.CHARACTER, "师父", status="destroyed"))
        g.add_node(_kp(NodeType.CHARACTER, "林尘"))
        g.add_relation(_rel(NodeType.CHARACTER, "师父", NodeType.CHARACTER, "林尘", "knows"))
        cs = list(g.detect_contradictions())
        assert len(cs) == 1
        assert cs[0].kind == ContradictionKind.DESTROYED_NODE_HAS_ACTIVE_RELATION

    def test_destroyed_artifact_owned_by_active_character(self):
        """断剑已毁,但还"被主角拥有" — 矛盾"""
        g = KeyPointGraph()
        g.add_node(_kp(NodeType.ARTIFACT, "断剑", status="destroyed"))
        g.add_node(_kp(NodeType.CHARACTER, "林尘"))
        g.add_relation(_rel(NodeType.CHARACTER, "林尘", NodeType.ARTIFACT, "断剑", "owns"))
        cs = list(g.detect_contradictions())
        assert len(cs) == 1
        assert cs[0].kind == ContradictionKind.DESTROYED_NODE_HAS_ACTIVE_RELATION

    def test_transformed_node_can_have_active_relations(self):
        """status="transformed" 不算 destroyed,应允许 active 关系"""
        g = KeyPointGraph()
        g.add_node(_kp(NodeType.ARTIFACT, "断剑", status="transformed"))
        g.add_node(_kp(NodeType.CHARACTER, "林尘"))
        g.add_relation(_rel(NodeType.CHARACTER, "林尘", NodeType.ARTIFACT, "断剑", "owns"))
        cs = list(g.detect_contradictions())
        assert cs == []

    def test_destroyed_to_destroyed_relation_is_ok(self):
        """两个 destroyed 节点之间有关系,不算矛盾 (历史遗物关系)"""
        g = KeyPointGraph()
        g.add_node(_kp(NodeType.CHARACTER, "师父", status="destroyed"))
        g.add_node(_kp(NodeType.LOCATION, "故土", status="destroyed"))
        g.add_relation(_rel(NodeType.CHARACTER, "师父", NodeType.LOCATION, "故土", "located_in"))
        cs = list(g.detect_contradictions())
        assert cs == []

    def test_concept_can_be_destroyed_without_relations(self):
        """CONCEPT 类型 destroyed 但无关系,不算矛盾"""
        g = KeyPointGraph()
        g.add_node(_kp(NodeType.CONCEPT, "旧道", status="destroyed"))
        cs = list(g.detect_contradictions())
        assert cs == []


class TestContradictionDataclass:
    def test_contradiction_to_string_includes_kind_and_nodes(self):
        c = Contradiction(
            kind=ContradictionKind.LOCATED_IN_DESTROYED,
            node_a=NodeId(NodeType.CHARACTER, "林尘"),
            node_b=NodeId(NodeType.LOCATION, "玄域"),
        )
        s = str(c)
        # ContradictionKind 是 str enum, 值是 "located_in_destroyed"
        assert "located_in_destroyed" in s
        assert "林尘" in s
        assert "玄域" in s


class TestFromSnapshot:
    def test_build_graph_from_snapshot(self):
        snap = WorldSnapshot(
            snapshot_id="ch0001",
            chapter=1,
            timestamp=datetime(2026, 1, 1),
            nodes={
                NodeId(NodeType.CHARACTER, "林尘"): _kp(NodeType.CHARACTER, "林尘"),
                NodeId(NodeType.LOCATION, "玄域"): _kp(NodeType.LOCATION, "玄域", status="destroyed"),
            },
            relations=(
                _rel(NodeType.CHARACTER, "林尘", NodeType.LOCATION, "玄域", "located_in"),
            ),
        )
        g = KeyPointGraph.from_snapshot(snap)
        assert g.node_count() == 2
        assert g.relation_count() == 1
        cs = list(g.detect_contradictions())
        assert len(cs) == 1
