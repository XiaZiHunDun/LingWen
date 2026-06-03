"""灵文世界模型 (Phase 1.1 + 1.2)

Doc 1 (灵文理论框架 v1.0) 实施层。
Phase 1.2 (Doc 3) 扩展: WorldSnapshot 加 active_subplots 字段。

核心导出:
- WorldSnapshot / KeyPoint / Relation / NodeId / NodeType
- PhysicalLine / MentalLine / Ripple
- KeyPointGraph — N² 矛盾检测
- SnapshotStore — JSON 持久化
- Contradiction / ContradictionKind
- (1.2) subplots_count / add_subplot / get_active_subplots 工具方法

不导出 (后续阶段):
- RippleEngine (1.5+)
- SnapshotDiff (跨章节检测, 1.5+)
- LLM 关键点抽取 prompt (1.3+)
"""

from .data_structures import (
    KeyPoint,
    MentalLine,
    NodeId,
    NodeType,
    PhysicalLine,
    PlotStatus,
    Relation,
    Ripple,
    WorldSnapshot,
)
from .key_point_graph import (
    Contradiction,
    ContradictionKind,
    KeyPointGraph,
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
]
