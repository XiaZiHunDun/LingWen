"""灵文世界模型 (Phase 1.1)

Doc 1 (灵文理论框架 v1.0) 实施层第一期。

核心导出:
- WorldSnapshot / KeyPoint / Relation / NodeId / NodeType
- PhysicalLine / MentalLine / Ripple
- KeyPointGraph — N² 矛盾检测
- SnapshotStore — JSON 持久化
- Contradiction / ContradictionKind

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
]
