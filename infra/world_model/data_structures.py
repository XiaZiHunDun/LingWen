"""灵文世界模型 · 核心数据结构 (Phase 19+ Sub1 — canonical re-exports)

Phase 1.1 — Doc 1 (灵文理论框架 v1.0) 实施层。

核心模型:
- NodeId/NodeType: 关键点标识
- KeyPoint: 关键点状态
- Relation: 关键点之间的关系
- PhysicalLine/MentalLine: 物理线/心理线
- Ripple: 剧情波浪 (挖坑→扩散→平复)
- WorldSnapshot: 一章一个版本的世界快照

Phase 1.2 (Doc 3): 加 active_subplots 字段 (lazy import 避免循环依赖)

Phase 1.5 (Doc 1 §3.4): Ripple 扩展 — 加 state / wavefront / decay_rate /
affected_relations / planned_resolve_ch 5 字段,backward-compatible with Phase 1.1
JSON (from_dict 用 .get(key, default) 兜底)。

Phase 19+ Sub1: 本文件所有业务实体 (KeyPoint / Relation / PhysicalLine /
MentalLine / WorldSnapshot / NodeId / NodeType / Ripple / RippleState /
ResolutionMode / MAX_OPEN_RIPPLOTS) 全部 canonical re-export from
``lingwen_core.domain.*``。本文件不再持有任何领域实体定义 — 仅保留
``PlotStatus`` Enum (轻量枚举,不属于 DDD aggregate 的一部分,放在此处做
back-compat 给 ``infra.world_model.PlotStatus`` 路径使用)。
"""
from __future__ import annotations

from enum import Enum

# Phase 19+ Sub1: All domain entities canonical alignment.
# Re-exports from lingwen_core.domain.* so consumers via
# `infra.world_model.data_structures.X` and via `lingwen_core.domain.X`
# resolve to the SAME class object. Closes Phase 18 v18 carryover chain
# (class-identity divergence was flagged as deferred in T1-T3 verification).
from lingwen_core.domain.chapter import MentalLine, PhysicalLine
from lingwen_core.domain.common import KeyPoint, NodeId, NodeType, Relation
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


class PlotStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSING = "closing"
    CLOSED = "closed"
    ABANDONED = "abandoned"


__all__ = [
    # Common (Phase 1.1)
    "NodeId",
    "NodeType",
    "KeyPoint",
    "Relation",
    # Chapter lines (Phase 1.1)
    "PhysicalLine",
    "MentalLine",
    # Ripple (Phase 1.5)
    "Ripple",
    "RippleState",
    "ResolutionMode",
    "MAX_OPEN_RIPPLOTS",
    "RippleOpenedEvent",
    "RippleStateChangedEvent",
    "RippleResolvedEvent",
    # WorldSnapshot (Phase 1.1 + 1.2 + 19+)
    "WorldSnapshot",
    # Subplot status enum (infra-local — lightweight, not domain)
    "PlotStatus",
]
