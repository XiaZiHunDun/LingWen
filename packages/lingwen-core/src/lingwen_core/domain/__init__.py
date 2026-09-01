"""灵文核心 · Domain — 业务实体与域事件包

Phase 18.1 — Domain 实体下沉。

所有业务逻辑（use-cases）应只依赖本包提供的 dataclass 与事件，
不直接 import 底层持久化（SQLite / JSON）或外部类型。

模块分布:
- common: NodeType / NodeId / KeyPoint / Relation (跨子域共享)
- chapter: Chapter / PhysicalLine / MentalLine + 章节事件
- volume: Volume + 卷事件
- character: Character / CharacterStatus
- foreshadow: Foreshadow + 伏笔事件
- ripple: Ripple / RippleState / ResolutionMode / WorldSnapshot + 涟漪事件
- subplot: Plot / PlotType / PlotPurpose / PlotStatus + MAX_ACTIVE_SUBPLOTS
"""
from __future__ import annotations

from lingwen_core.domain.chapter import (
    Chapter,
    ChapterReviewedEvent,
    ChapterWrittenEvent,
    MentalLine,
    PhysicalLine,
)
from lingwen_core.domain.character import Character, CharacterStatus
from lingwen_core.domain.common import KeyPoint, NodeId, NodeType, Relation
from lingwen_core.domain.foreshadow import (
    Foreshadow,
    ForeshadowPlantedEvent,
    ForeshadowResolvedEvent,
)
from lingwen_core.domain.ripple import (
    MAX_OPEN_RIPPLOTS,
    ResolutionMode,
    Ripple,
    RippleOpenedEvent,
    RippleResolvedEvent,
    RippleState,
    RippleStateChangedEvent,
    WorldSnapshot,
)
from lingwen_core.domain.subplot import (
    MAX_ACTIVE_SUBPLOTS,
    Plot,
    PlotPurpose,
    PlotStatus,
    PlotType,
)
from lingwen_core.domain.volume import Volume, VolumeCreatedEvent

__all__ = [
    # Common
    "NodeType",
    "NodeId",
    "KeyPoint",
    "Relation",
    # Chapter
    "Chapter",
    "PhysicalLine",
    "MentalLine",
    "ChapterWrittenEvent",
    "ChapterReviewedEvent",
    # Volume
    "Volume",
    "VolumeCreatedEvent",
    # Character
    "Character",
    "CharacterStatus",
    # Foreshadow
    "Foreshadow",
    "ForeshadowPlantedEvent",
    "ForeshadowResolvedEvent",
    # Ripple
    "Ripple",
    "RippleState",
    "ResolutionMode",
    "MAX_OPEN_RIPPLOTS",
    "RippleOpenedEvent",
    "RippleStateChangedEvent",
    "RippleResolvedEvent",
    "WorldSnapshot",
    # Subplot
    "Plot",
    "PlotType",
    "PlotPurpose",
    "PlotStatus",
    "MAX_ACTIVE_SUBPLOTS",
]
