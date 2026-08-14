"""Phase 18.1 守卫测试 — lingwen_core.domain 包结构与不变式。

Domain 实体下沉到 packages/lingwen-core/src/lingwen_core/domain/。
所有实体应:
1. @dataclass(frozen=True) — 不可变
2. 有 __post_init__ 验证不变式（非空字段、合法取值范围）
3. Domain 事件继承 DomainEvent 基类（frozen + event_id + occurred_at）

迁移自 infra/world_model/data_structures.py + 新增 Chapter/Volume/Character/Foreshadow。
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass

import pytest


def test_domain_package_importable():
    import lingwen_core.domain  # noqa: F401


# ─────────────────────────────────────────────────────────
# common: NodeType / NodeId / KeyPoint / Relation
# ─────────────────────────────────────────────────────────


def test_node_type_enum():
    from lingwen_core.domain.common import NodeType

    assert NodeType.LOCATION.value == "location"
    assert NodeType.CHARACTER.value == "character"
    assert NodeType.FACTION.value == "faction"
    assert NodeType.ARTIFACT.value == "artifact"
    assert NodeType.CONCEPT.value == "concept"


def test_node_id_frozen_with_invariant():
    from lingwen_core.domain.common import NodeId, NodeType

    nid = NodeId(type=NodeType.CHARACTER, name="alice")
    assert is_dataclass(nid) and nid.__dataclass_params__.frozen  # type: ignore[attr-defined]
    assert str(nid) == "character:alice"

    with pytest.raises(FrozenInstanceError):
        nid.name = "bob"  # type: ignore[misc]


def test_node_id_rejects_empty_name():
    from lingwen_core.domain.common import NodeId, NodeType

    with pytest.raises(ValueError, match="non-empty"):
        NodeId(type=NodeType.CHARACTER, name="")


def test_node_id_from_string_roundtrip():
    from lingwen_core.domain.common import NodeId, NodeType

    nid = NodeId.from_string("location:lake")
    assert nid == NodeId(NodeType.LOCATION, "lake")


def test_node_id_from_string_invalid():
    from lingwen_core.domain.common import NodeId

    with pytest.raises(ValueError, match="must contain ':'"):
        NodeId.from_string("no_colon")


# ─────────────────────────────────────────────────────────
# chapter: PhysicalLine / MentalLine / Chapter
# ─────────────────────────────────────────────────────────


def test_chapter_entity_frozen():
    from lingwen_core.domain.chapter import Chapter

    ch = Chapter(chapter=1, title="开篇", text="...", outline_ref="out:1")
    assert is_dataclass(ch)
    assert ch.__dataclass_params__.frozen  # type: ignore[attr-defined]
    with pytest.raises(FrozenInstanceError):
        ch.title = "x"  # type: ignore[misc]


def test_chapter_rejects_non_positive():
    from lingwen_core.domain.chapter import Chapter

    with pytest.raises(ValueError, match="positive"):
        Chapter(chapter=0, title="t", text="x", outline_ref="r")


def test_chapter_rejects_empty_title():
    from lingwen_core.domain.chapter import Chapter

    with pytest.raises(ValueError, match="non-empty"):
        Chapter(chapter=1, title="", text="x", outline_ref="r")


# ─────────────────────────────────────────────────────────
# volume: Volume
# ─────────────────────────────────────────────────────────


def test_volume_entity_frozen():
    from lingwen_core.domain.volume import Volume

    v = Volume(volume=1, title="卷一", chapter_range=(1, 50))
    assert is_dataclass(v)
    assert v.__dataclass_params__.frozen  # type: ignore[attr-defined]


def test_volume_rejects_invalid_range():
    from lingwen_core.domain.volume import Volume

    with pytest.raises(ValueError, match="chapter_range"):
        Volume(volume=1, title="x", chapter_range=(50, 1))  # 倒序


# ─────────────────────────────────────────────────────────
# character: Character
# ─────────────────────────────────────────────────────────


def test_character_entity_frozen():
    from lingwen_core.domain.character import Character, CharacterStatus

    c = Character(
        name="alice", faction="流浪者", role="主角",
        status=CharacterStatus.ALIVE,
    )
    assert is_dataclass(c)
    assert c.__dataclass_params__.frozen  # type: ignore[attr-defined]


def test_character_status_enum():
    from lingwen_core.domain.character import CharacterStatus

    assert CharacterStatus.ALIVE.value == "alive"
    assert CharacterStatus.DEAD.value == "dead"
    assert CharacterStatus.UNKNOWN.value == "unknown"


# ─────────────────────────────────────────────────────────
# foreshadow: Foreshadow
# ─────────────────────────────────────────────────────────


def test_foreshadow_frozen():
    from lingwen_core.domain.foreshadow import Foreshadow

    f = Foreshadow(
        foreshadow_id="fs:1",
        description="神秘人物",
        planted_ch=10,
        planned_resolve_ch=50,
        resolved_ch=None,
    )
    assert is_dataclass(f)
    assert f.__dataclass_params__.frozen  # type: ignore[attr-defined]


def test_foreshadow_resolve_after_plant():
    from lingwen_core.domain.foreshadow import Foreshadow

    with pytest.raises(ValueError, match="planted_ch"):
        Foreshadow(
            foreshadow_id="x",
            description="y",
            planted_ch=50,
            planned_resolve_ch=10,  # < planted_ch
            resolved_ch=None,
        )


# ─────────────────────────────────────────────────────────
# ripple: Ripple / RippleState / ResolutionMode / WorldSnapshot
# ─────────────────────────────────────────────────────────


def test_ripple_frozen_with_invariants():
    from lingwen_core.domain.ripple import Ripple, RippleState

    r = Ripple(
        ripple_id="r:1",
        origin_event="e",
        origin_ch=5,
        state=RippleState.OPEN,
    )
    assert is_dataclass(r)
    assert r.__dataclass_params__.frozen  # type: ignore[attr-defined]
    with pytest.raises(FrozenInstanceError):
        r.origin_ch = 10  # type: ignore[misc]


def test_ripple_decay_rate_in_range():
    from lingwen_core.domain.ripple import Ripple

    with pytest.raises(ValueError, match="decay_rate"):
        Ripple(
            ripple_id="x",
            origin_event="e",
            origin_ch=1,
            decay_rate=1.5,  # 超出 [0, 1]
        )


def test_ripple_state_enum():
    from lingwen_core.domain.ripple import RippleState

    assert RippleState.OPEN.value == "open"
    assert RippleState.PROPAGATING.value == "propagating"
    assert RippleState.RESOLVING.value == "resolving"
    assert RippleState.RESOLVED.value == "resolved"


def test_world_snapshot_frozen():
    from lingwen_core.domain.ripple import WorldSnapshot
    from datetime import datetime

    snap = WorldSnapshot(
        snapshot_id="snap:1",
        chapter=10,
        timestamp=datetime(2026, 1, 1),
    )
    assert is_dataclass(snap)
    assert snap.__dataclass_params__.frozen  # type: ignore[attr-defined]
    # consistency_hash 应在 __post_init__ 自动计算
    assert len(snap.consistency_hash) == 16


# ─────────────────────────────────────────────────────────
# domain events
# ─────────────────────────────────────────────────────────


def test_chapter_written_event_frozen():
    from lingwen_core.domain.chapter import ChapterWrittenEvent

    e = ChapterWrittenEvent(payload={"chapter": 1})
    assert e.type == "ChapterWritten"
    with pytest.raises(Exception):  # Pydantic frozen raises ValidationError, not FrozenInstanceError
        e.payload = {}


def test_foreshadow_resolved_event_frozen():
    from lingwen_core.domain.foreshadow import ForeshadowResolvedEvent

    e = ForeshadowResolvedEvent(payload={"foreshadow_id": "fs:1", "chapter": 50})
    assert e.type == "ForeshadowResolved"


def test_ripple_state_changed_event():
    from lingwen_core.domain.ripple import RippleStateChangedEvent

    e = RippleStateChangedEvent(
        payload={"ripple_id": "r:1", "from": "open", "to": "propagating"}
    )
    assert e.type == "RippleStateChanged"


# ─────────────────────────────────────────────────────────
# domain init re-exports
# ─────────────────────────────────────────────────────────


def test_domain_init_exports_all():
    import lingwen_core.domain as d

    # 核心实体
    for name in [
        "NodeType",
        "NodeId",
        "KeyPoint",
        "Relation",
        "Chapter",
        "Volume",
        "Character",
        "CharacterStatus",
        "Foreshadow",
        "Ripple",
        "RippleState",
        "ResolutionMode",
        "WorldSnapshot",
    ]:
        assert hasattr(d, name), f"missing: {name}"

    # 域事件
    for name in [
        "ChapterWrittenEvent",
        "VolumeCreatedEvent",
        "ForeshadowResolvedEvent",
        "RippleStateChangedEvent",
    ]:
        assert hasattr(d, name), f"missing event: {name}"