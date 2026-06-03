"""灵文支线生命周期 (Phase 1.2)

Doc 3 (主线/支线模型 v1.0) §4: 6 状态机 + 7 阶段模型。

提供:
- VALID_TRANSITIONS: 6 状态转换规则 (from → set[to])
- can_transition(frm, to): 校验
- is_terminal(status): 是否终态
- CLOSING_MIN_CHAPTERS = 2: CLOSING 最短章数
- STAGES: 7 阶段元组
- STAGE_TYPICAL_RANGES: 各阶段典型章数范围 (min, max)
- get_current_stage(plot, current_ch): 根据当前章节推断阶段

不实施 (后续阶段):
- 7 阶段的精细化进度计算 (Phase 1.5+,需要章节级 constraint 触发数据)
- 状态机的撤销/重做 (1.5+)
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from infra.subplot.data_structures import PlotStatus

if TYPE_CHECKING:
    from infra.subplot.data_structures import Plot


# 6 状态转换规则 (4 个非终态作为 key,CLOSED/ABANDONED 为终态不可作为 key)
VALID_TRANSITIONS: dict[PlotStatus, set[PlotStatus]] = {
    PlotStatus.DRAFT: {PlotStatus.ACTIVE, PlotStatus.ABANDONED},
    PlotStatus.ACTIVE: {PlotStatus.PAUSED, PlotStatus.CLOSING, PlotStatus.ABANDONED},
    PlotStatus.PAUSED: {PlotStatus.ACTIVE, PlotStatus.ABANDONED},
    PlotStatus.CLOSING: {PlotStatus.CLOSED, PlotStatus.ABANDONED},
}

# CLOSING 必须持续 ≥ 2 章 (Doc 3 §3.2)
CLOSING_MIN_CHAPTERS = 2

# 7 阶段模型 (按时间顺序)
STAGES: tuple[str, ...] = (
    "seed",       # 1-2 ch, 钩子引入
    "build",      # 5-15 ch, 发展
    "escalate",   # 5-10 ch, 升级
    "climax",     # 2-5 ch, 高潮
    "resolve",    # 3-5 ch, 收束
    "close",      # 1-2 ch, 标记 CLOSED
    "echo",       # 0+ ch, 偶发回响
)

# 各阶段典型章数范围 (min, max)
STAGE_TYPICAL_RANGES: dict[str, tuple[int, int]] = {
    "seed":     (1, 2),
    "build":    (5, 15),
    "escalate": (5, 10),
    "climax":   (2, 5),
    "resolve":  (3, 5),
    "close":    (1, 2),
    "echo":     (0, 0),
}

# 阶段边界 (进度百分比) — 用于 get_current_stage
# 总和 1.0,顺序与 STAGES 一致
_STAGE_PROGRESS_BOUNDS: tuple[tuple[str, float, float], ...] = (
    ("seed",     0.00, 0.05),
    ("build",    0.05, 0.40),
    ("escalate", 0.40, 0.65),
    ("climax",   0.65, 0.80),
    ("resolve",  0.80, 0.95),
    ("close",    0.95, 1.00),
)


def can_transition(frm: PlotStatus, to: PlotStatus) -> bool:
    """校验状态转换是否合法 (根据 VALID_TRANSITIONS)"""
    if frm not in VALID_TRANSITIONS:
        return False  # 终态不可转出
    return to in VALID_TRANSITIONS[frm]


def is_terminal(status: PlotStatus) -> bool:
    """是否终态 (CLOSED / ABANDONED)"""
    return status not in VALID_TRANSITIONS


def get_stage_range(stage: str) -> tuple[int, int]:
    """查询某阶段的典型章数范围 (min, max)"""
    if stage not in STAGE_TYPICAL_RANGES:
        raise ValueError(f"unknown stage: {stage!r}, expected one of {STAGES}")
    return STAGE_TYPICAL_RANGES[stage]


def get_current_stage(plot: "Plot", current_ch: int) -> str:
    """根据当前章节推断 plot 处于哪个阶段

    算法:
    - progress = (current_ch - birth_ch) / (close_ch - birth_ch)
    - progress ∈ [0, 1] → 映射到 seed/.../close
    - progress > 1.0 → echo (close 之后)
    - progress < 0 → echo (未出生)
    - 无 birth/close → echo (无信息)
    """
    if plot.birth_ch == 0 and plot.close_ch is None:
        return "echo"

    if plot.close_ch is None or plot.close_ch <= plot.birth_ch:
        return "echo"

    if current_ch < plot.birth_ch:
        return "echo"

    if current_ch > plot.close_ch:
        return "echo"

    total = plot.close_ch - plot.birth_ch
    if total <= 0:
        return "echo"

    progress = (current_ch - plot.birth_ch) / total

    for stage, lo, hi in _STAGE_PROGRESS_BOUNDS:
        if lo <= progress < hi:
            return stage
    # progress == 1.0 (close_ch-1) → 落到 close (上面的 < 不会匹配)
    if progress >= 0.95:
        return "close"
    return "echo"


__all__ = [
    "VALID_TRANSITIONS",
    "CLOSING_MIN_CHAPTERS",
    "STAGES",
    "STAGE_TYPICAL_RANGES",
    "can_transition",
    "is_terminal",
    "get_stage_range",
    "get_current_stage",
]
