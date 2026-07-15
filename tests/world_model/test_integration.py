"""Phase 1.1 集成测试: build → store → load → 矛盾检测。

验证端到端: 5 个节点的章节,存盘,再读出,扫描矛盾。
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from infra.world_model import (
    ContradictionKind,
    KeyPoint,
    KeyPointGraph,
    NodeId,
    NodeType,
    PhysicalLine,
    Relation,
    SnapshotStore,
    WorldSnapshot,
)


def _lin_chen() -> KeyPoint:
    return KeyPoint(id=NodeId(NodeType.CHARACTER, "林尘"), attrs={"age": 18, "realm": "炼气"})


def _master() -> KeyPoint:
    return KeyPoint(id=NodeId(NodeType.CHARACTER, "师父"), status="destroyed")


def _xuan_yu() -> KeyPoint:
    return KeyPoint(id=NodeId(NodeType.LOCATION, "玄域"), status="destroyed")


def _xing_yue_sect() -> KeyPoint:
    return KeyPoint(id=NodeId(NodeType.FACTION, "星月宗"))


def _duan_jian() -> KeyPoint:
    return KeyPoint(id=NodeId(NodeType.ARTIFACT, "断剑"))


def test_end_to_end_one_chapter(tmp_path: Path):
    """单章节: 含一个 LOCATED_IN_DESTROYED 矛盾,端到端跑通"""
    snap = WorldSnapshot(
        snapshot_id="ch0001_v1",
        chapter=1,
        timestamp=datetime(2026, 5, 21, 10, 0, 0),
        nodes={
            NodeId(NodeType.CHARACTER, "林尘"): _lin_chen(),
            NodeId(NodeType.CHARACTER, "师父"): _master(),
            NodeId(NodeType.LOCATION, "玄域"): _xuan_yu(),
            NodeId(NodeType.FACTION, "星月宗"): _xing_yue_sect(),
            NodeId(NodeType.ARTIFACT, "断剑"): _duan_jian(),
        },
        relations=(
            # 矛盾 1: 林尘 (active) located_in 玄域 (destroyed)
            Relation(
                src=NodeId(NodeType.CHARACTER, "林尘"),
                dst=NodeId(NodeType.LOCATION, "玄域"),
                type="located_in",
            ),
            # 矛盾 2: 师父 (destroyed) knows 林尘
            Relation(
                src=NodeId(NodeType.CHARACTER, "师父"),
                dst=NodeId(NodeType.CHARACTER, "林尘"),
                type="knows",
            ),
            # 合法关系: 林尘 (active) located_in 星月宗 (active)
            Relation(
                src=NodeId(NodeType.CHARACTER, "林尘"),
                dst=NodeId(NodeType.FACTION, "星月宗"),
                type="belongs_to",
            ),
            # 合法关系: 断剑 (active) owned by 林尘
            Relation(
                src=NodeId(NodeType.CHARACTER, "林尘"),
                dst=NodeId(NodeType.ARTIFACT, "断剑"),
                type="owns",
            ),
        ),
        physical=PhysicalLine(ch=1, actions=["入玄域", "师父战死"], events=["师父之死"]),
    )

    # 1. 存盘
    store = SnapshotStore(tmp_path)
    store.save(snap)

    # 2. 列章节
    assert store.list_chapters() == [1]

    # 3. 读出 (含 integrity 校验)
    loaded = store.load(1, verify_integrity=True)
    assert loaded == snap

    # 4. 扫描矛盾
    graph = KeyPointGraph.from_snapshot(loaded)
    cs = list(graph.detect_contradictions())

    # 期望: 2 个矛盾
    assert len(cs) == 2
    kinds = {c.kind for c in cs}
    assert ContradictionKind.LOCATED_IN_DESTROYED in kinds
    assert ContradictionKind.DESTROYED_NODE_HAS_ACTIVE_RELATION in kinds


def test_chapter_sequence_independent_snapshots(tmp_path: Path):
    """3 章节: 每章独立 snapshot, 互不污染"""
    store = SnapshotStore(tmp_path)

    for ch in [1, 2, 3]:
        snap = WorldSnapshot(
            snapshot_id=f"ch{ch:04d}_v1",
            chapter=ch,
            timestamp=datetime(2026, 5, 21, 10, 0, ch),
            nodes={
                NodeId(NodeType.CHARACTER, "林尘"): KeyPoint(
                    id=NodeId(NodeType.CHARACTER, "林尘"),
                    attrs={"age": 18 + ch},
                ),
            },
        )
        store.save(snap)

    # 每章的 age 应该不同
    assert store.load(1).nodes[NodeId(NodeType.CHARACTER, "林尘")].attrs["age"] == 19
    assert store.load(2).nodes[NodeId(NodeType.CHARACTER, "林尘")].attrs["age"] == 20
    assert store.load(3).nodes[NodeId(NodeType.CHARACTER, "林尘")].attrs["age"] == 21


def test_clean_chapter_no_contradictions(tmp_path: Path):
    """无矛盾的"干净"章节: 1 章节, 0 矛盾"""
    snap = WorldSnapshot(
        snapshot_id="ch0001_v1",
        chapter=1,
        timestamp=datetime(2026, 5, 21, 10, 0, 0),
        nodes={
            NodeId(NodeType.CHARACTER, "林尘"): _lin_chen(),
            NodeId(NodeType.LOCATION, "玄域"): KeyPoint(
                id=NodeId(NodeType.LOCATION, "玄域"), status="active"
            ),
        },
        relations=(
            Relation(
                src=NodeId(NodeType.CHARACTER, "林尘"),
                dst=NodeId(NodeType.LOCATION, "玄域"),
                type="located_in",
            ),
        ),
    )
    store = SnapshotStore(tmp_path)
    store.save(snap)
    loaded = store.load(1)
    graph = KeyPointGraph.from_snapshot(loaded)
    assert list(graph.detect_contradictions()) == []
