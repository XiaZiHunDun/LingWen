"""灵文世界模型 (Phase 1.1 + 1.2 + 1.5 + 2.3 + 2.6)

Doc 1 (灵文理论框架 v1.0) 实施层。
Phase 1.2 (Doc 3) 扩展: WorldSnapshot 加 active_subplots 字段。
Phase 1.5 (Doc 1 §3.4) 扩展: Ripple 5 字段 + RippleState/ResolutionMode enums +
RippleEngine (6 方法) + RippleRegistry (CRUD + 10-limit + JSON 持久化) +
3 query helpers (detect_unresolved_ripples / predict_collapse_risk /
suggest_resolution_chapter)。
Phase 2.3 扩展: Ripple ↔ Subplot 跨包联动 (link_subplot_to_ripple +
apply_ripple_resolution)。
Phase 2.6 扩展: SnapshotDiff (5 类别 + Ripple state 变化检测)。

Phase 19+ Sub1: Domain entity re-exports now canonical from
``lingwen_core.domain.*`` (see ``data_structures``). Behavior services
(engine, lifecycle, links, queries, registry, snapshot_diff,
snapshot_store, key_point_graph, subplot helpers) remain in this package
unchanged.

核心导出:
- WorldSnapshot / KeyPoint / Relation / NodeId / NodeType (canonical)
- PhysicalLine / MentalLine / Ripple / RippleState / ResolutionMode (canonical)
- KeyPointGraph — N² 矛盾检测
- SnapshotStore — JSON 持久化
- Contradiction / ContradictionKind
- (1.2) subplots_count / add_subplot / get_active_subplots 工具方法
- (1.5) RippleEngine / RippleRegistry / 3 exceptions
- (1.5) 3 query helpers + MAX_OPEN_RIPPLOTS + RESOLUTION_GRACE_CH
- (2.3) LinkAction / link_subplot_to_ripple / apply_ripple_resolution
- (2.6) SnapshotChange / ChangeKind / EntityKind / diff_snapshots / diff_ripples / diff_subplots / has_state_transition

不导出 (后续阶段):
- LLM 关键点抽取 prompt (1.3+)
- LLM `new_ripples/resolved_ripples` 抽取模板 (Phase 2 实际在 prompt_engineering)
- 真实 LLM 集成
"""

# PHASE-COMPAT: Domain entities re-exported from canonical
# (lingwen_core.domain.*) — see data_structures.py which is now a
# canonical-only re-export module.
from lingwen_core.domain.chapter import MentalLine, PhysicalLine
from lingwen_core.domain.common import KeyPoint, NodeId, NodeType, Relation
from lingwen_core.domain.ripple import (
    MAX_OPEN_RIPPLOTS,
    ResolutionMode,
    Ripple,
    RippleState,
    WorldSnapshot,
)

# Phase 1.2 helpers — moved to infra.subplot.helpers (Phase 19+ Sub1 Task 5).
# Re-exported here for backward compat with existing consumers
# (`from infra.world_model import add_subplot, ...`).
from infra.subplot.helpers import (  # noqa: E402, F401
    add_subplot,
    get_active_subplots,
    subplots_count,
)

# PlotStatus (lightweight enum, infra-local — not part of DDD aggregate)
from .data_structures import PlotStatus

# Behavior services (NOT in PHASE-COMPAT shim scope)
from .engine import RippleEngine
from .key_point_graph import (
    Contradiction,
    ContradictionKind,
    KeyPointGraph,
)
from .lifecycle import (
    COLLAPSE_RISK_THRESHOLD,
    RESOLUTION_GRACE_CH,
    VALID_TRANSITIONS,
    can_transition,
    is_terminal,
)
from .links import (
    LinkAction,
    apply_ripple_resolution,
    link_subplot_to_ripple,
)
from .queries import (
    detect_unresolved_ripples,
    predict_collapse_risk,
    suggest_resolution_chapter,
)
from .registry import (
    DuplicateRippleIdError,
    OpenRippleLimitExceeded,
    RippleNotFoundError,
    RippleRegistry,
)
from .snapshot_diff import (
    ChangeKind,
    EntityKind,
    SnapshotChange,
    diff_ripples,
    diff_snapshots,
    diff_subplots,
    has_state_transition,
)
from .snapshot_store import (
    SnapshotIntegrityError,
    SnapshotNotFoundError,
    SnapshotStore,
)

__all__ = [
    # Data structures (Phase 1.1) — canonical re-exports
    "KeyPoint",
    "MentalLine",
    "NodeId",
    "NodeType",
    "PhysicalLine",
    "PlotStatus",
    "Relation",
    "Ripple",
    "WorldSnapshot",
    "Contradiction",
    "ContradictionKind",
    "KeyPointGraph",
    "SnapshotStore",
    "SnapshotNotFoundError",
    "SnapshotIntegrityError",
    # Phase 1.2 helpers
    "subplots_count",
    "add_subplot",
    "get_active_subplots",
    # Phase 1.5 — Ripple (Doc 1 §3.4)
    "RippleState",
    "ResolutionMode",
    "MAX_OPEN_RIPPLOTS",
    "RESOLUTION_GRACE_CH",
    "COLLAPSE_RISK_THRESHOLD",
    "VALID_TRANSITIONS",
    "can_transition",
    "is_terminal",
    "RippleEngine",
    "RippleRegistry",
    "RippleNotFoundError",
    "DuplicateRippleIdError",
    "OpenRippleLimitExceeded",
    "detect_unresolved_ripples",
    "predict_collapse_risk",
    "suggest_resolution_chapter",
    # Phase 2.3 — Ripple ↔ Subplot 联动
    "LinkAction",
    "link_subplot_to_ripple",
    "apply_ripple_resolution",
]
