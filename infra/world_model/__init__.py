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

核心导出:
- WorldSnapshot / KeyPoint / Relation / NodeId / NodeType
- PhysicalLine / MentalLine / Ripple / RippleState / ResolutionMode
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

from .data_structures import (
    MAX_OPEN_RIPPLOTS,
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


def subplots_count(snapshot: "WorldSnapshot") -> int:
    """统计 WorldSnapshot 中 active subplot 数 (Phase 1.2 工具方法)"""
    return len(snapshot.active_subplots)


def add_subplot(snapshot: "WorldSnapshot", plot) -> "WorldSnapshot":
    """向 WorldSnapshot 添加一个 subplot,返回新快照 (不可变)

    Args:
        snapshot: 原快照
        plot: Plot 对象 (来自 infra.subplot)

    Returns:
        含新 subplot 的新 WorldSnapshot
    """
    from dataclasses import replace
    return replace(snapshot, active_subplots=(*snapshot.active_subplots, plot))


def get_active_subplots(snapshot: "WorldSnapshot"):
    """返回 WorldSnapshot 中所有 status == ACTIVE 的 subplot (Phase 1.2 工具方法)"""
    from infra.subplot.data_structures import PlotStatus
    return tuple(p for p in snapshot.active_subplots if p.status == PlotStatus.ACTIVE)


__all__ = [
    # Data structures (Phase 1.1)
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
