"""灵文支线模型 (Phase 1.2)

Doc 3 (主线/支线模型 v1.0) 实施层第一期。

核心导出:
- Plot / PlotType / PlotPurpose / PlotStatus
- MAX_ACTIVE_SUBPLOTS = 5 (硬限制)
- PlotRegistry (CRUD + 持久化 + 状态机校验)
- lifecycle: 6 状态转换 + 7 阶段模型
- queries: can_open_new_subplot / suggest_subplot_to_close / detect_constraint_saturation

不导出 (后续阶段):
- SIDE plot 完整管理 (Phase 1.5+)
- Ripple 关联的完整机制 (delegated to Doc 1 Phase 1.5+)
- 3-volume / L1/L2/L3 大纲 (属于 outline_master)
- 5-limit 紧急豁免 (climax periods may allow 6)
"""
from .data_structures import (
    MAX_ACTIVE_SUBPLOTS,
    Plot,
    PlotPurpose,
    PlotStatus,
    PlotType,
)

__all__ = [
    "MAX_ACTIVE_SUBPLOTS",
    "Plot",
    "PlotPurpose",
    "PlotStatus",
    "PlotType",
    "PlotRegistry",
    "VALID_TRANSITIONS",
    "CLOSING_MIN_CHAPTERS",
    "STAGES",
    "STAGE_TYPICAL_RANGES",
    "can_open_new_subplot",
    "suggest_subplot_to_close",
    "detect_constraint_saturation",
]
