"""灵文支线查询 (Phase 1.2)

Doc 3 (主线/支线模型 v1.0) §5.2: 3 个辅助查询函数。

提供:
- can_open_new_subplot(registry): 是否能开新支线
- suggest_subplot_to_close(registry): 建议关闭的 subplot_id
- detect_constraint_saturation(registry, current_ch): 检测约束饱和
"""
from __future__ import annotations

import re
from typing import Optional

from infra.subplot.data_structures import (
    MAX_ACTIVE_SUBPLOTS,
    PlotStatus,
    PlotType,
)
from infra.subplot.registry import PlotRegistry

# 约束饱和: 未来 5 章内触发 ≥ 3 个 constraint
_SATURATION_WINDOW = 5
_SATURATION_THRESHOLD = 3

# 解析 constraint 字符串中的章号: "ch52: 描述" / "第55章: 描述" / "ch 52: ..."
_CH_PATTERN_EN = re.compile(r"ch\s*(\d+)", re.IGNORECASE)
_CH_PATTERN_CN = re.compile(r"第\s*(\d+)\s*章")


def _parse_chapter_from_constraint(s: str) -> Optional[int]:
    """从 constraint 字符串中解析章号,支持 'chXX' / '第XX章' / 'ch XX'"""
    m = _CH_PATTERN_EN.search(s)
    if m:
        return int(m.group(1))
    m = _CH_PATTERN_CN.search(s)
    if m:
        return int(m.group(1))
    return None


def can_open_new_subplot(registry: PlotRegistry) -> bool:
    """当前 active subplot 数 < MAX_ACTIVE_SUBPLOTS 即可开新支线"""
    return registry.count_active_subplots() < MAX_ACTIVE_SUBPLOTS


def suggest_subplot_to_close(registry: PlotRegistry) -> Optional[str]:
    """建议关闭的 subplot_id — 最早 active 的 (按 birth_ch 最小)

    Returns:
        plot_id if 找到候选,None if 没有 active subplot
    """
    candidates = [
        p for p in registry.list_active_subplots()
        if p.birth_ch > 0  # 排除无 birth_ch 的 (无法判断早晚)
    ]
    if not candidates:
        return None
    oldest = min(candidates, key=lambda p: p.birth_ch)
    return oldest.plot_id


def detect_constraint_saturation(
    registry: PlotRegistry,
    current_ch: int,
) -> Optional[str]:
    """检测约束饱和 — 未来 5 章内 ≥ 3 个 constraint 触发

    解析每条 constraint 的章号,统计 active subplot 中
    `current_ch < ch <= current_ch + _SATURATION_WINDOW` 范围内的数量。
    任一 active subplot 满足阈值 → 返回其 plot_id。

    Returns:
        plot_id if 找到 saturation,None otherwise
    """
    window_end = current_ch + _SATURATION_WINDOW

    for plot in registry.list_active_subplots():
        upcoming_count = 0
        for constraint in plot.constraints_generated:
            ch_num = _parse_chapter_from_constraint(constraint)
            if ch_num is None:
                continue
            if current_ch < ch_num <= window_end:
                upcoming_count += 1
                if upcoming_count >= _SATURATION_THRESHOLD:
                    return plot.plot_id

    return None


__all__ = [
    "can_open_new_subplot",
    "suggest_subplot_to_close",
    "detect_constraint_saturation",
]
