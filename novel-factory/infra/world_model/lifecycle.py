"""灵文涟漪生命周期 (Phase 1.5 — RippleEngine 状态机)

Doc 1 §3.4 (涟漪机制 v1.0) — Ripple 4 状态 + 平复模式 + 硬限制常量。

4 状态转换规则 (Doc 1 §3.4):
  OPEN (挖坑)        → PROPAGATING (扩散) / RESOLVING (平复) / RESOLVED (终态)
  PROPAGATING (扩散) → RESOLVING (平复) / RESOLVED (终态)
  RESOLVING (平复中) → RESOLVED (终态)
  RESOLVED (终态)    → set()  # terminal

不导出 (后续阶段):
- LLM 抽取 ripple 描述 (Phase 2)
- 跨卷 ripple 谱系 (Phase 3+)
"""
from __future__ import annotations

from infra.world_model.data_structures import (
    MAX_OPEN_RIPPLOTS as MAX_OPEN_RIPPLOTS,  # re-export
)
from infra.world_model.data_structures import (
    Ripple,
    RippleState,
)

# Doc 1 §3.4 硬限制:未平复 Ripple > 10 → 崩塌风险 > 0.7 → > 0.8 报警
# 计入:OPEN + PROPAGATING + RESOLVING (RESOLVED 终态不计入)
# MAX_OPEN_RIPPLOTS 在 data_structures.py 定义 (10),这里 re-export

RESOLUTION_GRACE_CH = 5      # planned_resolve_ch 可超 current_ch + 5
COLLAPSE_RISK_THRESHOLD = 0.8  # > 0.8 系统报警


VALID_TRANSITIONS: dict[RippleState, set[RippleState]] = {
    RippleState.OPEN:        {RippleState.PROPAGATING, RippleState.RESOLVING, RippleState.RESOLVED},
    RippleState.PROPAGATING: {RippleState.RESOLVING, RippleState.RESOLVED},
    RippleState.RESOLVING:   {RippleState.RESOLVED},
    RippleState.RESOLVED:    set(),  # terminal
}


def can_transition(ripple: Ripple, new_state: RippleState) -> bool:
    """检查 ripple 状态 → new_state 转换是否合法

    Args:
        ripple: 当前 Ripple (frozen)
        new_state: 目标状态

    Returns:
        True if 状态转换合法
    """
    return new_state in VALID_TRANSITIONS[ripple.state]


def is_terminal(state: RippleState) -> bool:
    """状态是否终态 (RESOLVED = terminal,无出边)"""
    return state == RippleState.RESOLVED


__all__ = [
    "VALID_TRANSITIONS",
    "MAX_OPEN_RIPPLOTS",
    "RESOLUTION_GRACE_CH",
    "COLLAPSE_RISK_THRESHOLD",
    "can_transition",
    "is_terminal",
]
