"""灵文涟漪查询 (Phase 1.5)

Doc 1 §3.4 — 3 个核心 query:
- detect_unresolved_ripples(registry, current_ch, grace): 未平复 + 过期
- predict_collapse_risk(registry, current_ch, grace): 崩塌风险 0-1
- suggest_resolution_chapter(ripple): 基于 decay_rate 建议平复章节

Doc 2 §十一 line 363:chapter_writing 必传 active_ripples;foreshadow_scan /
ripple_audit scenario 用本模块。

不实施 (后续阶段):
- 跨卷 ripple 谱系 (Phase 3+)
- 真实 LLM 抽取 `new_ripples/resolved_ripples` (Phase 2)
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from infra.world_model.data_structures import (
    Ripple,
    RippleState,
)
from infra.world_model.lifecycle import (
    MAX_OPEN_RIPPLOTS,
    RESOLUTION_GRACE_CH,
)

if TYPE_CHECKING:
    pass  # Protocol only


class _RegistryLike(Protocol):
    """最小 registry 接口 (解耦 RippleRegistry)"""

    def list_active(self) -> tuple[Ripple, ...]: ...


def detect_unresolved_ripples(
    registry: _RegistryLike,
    current_ch: int,
    grace: int = RESOLUTION_GRACE_CH,
) -> tuple[Ripple, ...]:
    """未平复 + 过期 ripple 列表

    条件:state != RESOLVED and current_ch > planned_resolve_ch + grace

    Doc 1 §3.4:用于 `foreshadow_scan` (Doc 2 line 80) 标记逾期未填的坑。
    """
    return tuple(
        r for r in registry.list_active()
        if r.state != RippleState.RESOLVED
        and r.planned_resolve_ch is not None
        and current_ch > r.planned_resolve_ch + grace
    )


def predict_collapse_risk(
    registry: _RegistryLike,
    current_ch: int,
    grace: int = RESOLUTION_GRACE_CH,
) -> float:
    """崩塌风险 = stale / MAX_OPEN_RIPPLOTS,clamped [0, 1]

    Doc 1 §3.4 rule:
    - 累计未平复 > 10 → 崩塌风险 > 0.7
    - 崩塌风险 > 0.8 → 系统报警 (COLLAPSE_RISK_THRESHOLD)
    """
    stale = detect_unresolved_ripples(registry, current_ch, grace=grace)
    return min(1.0, len(stale) / MAX_OPEN_RIPPLOTS)


def suggest_resolution_chapter(ripple: Ripple) -> int:
    """建议平复章节 = origin_ch + int(1.0 / max(decay_rate, 0.1))

    decay_rate 0.2 → +5ch (中点,适合中长篇 50-200 章)
    decay_rate 0.5 → +2ch (快节奏爽文,2-3 章一坑)
    decay_rate 0.1 → +10ch (多卷长篇,慢热伏笔)
    """
    return ripple.origin_ch + int(1.0 / max(ripple.decay_rate, 0.1))


__all__ = [
    "detect_unresolved_ripples",
    "predict_collapse_risk",
    "suggest_resolution_chapter",
]
