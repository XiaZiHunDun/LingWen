"""灵文核心 · Use-cases — MergeRipples

Phase 18.2 — 涟漪合并用例。

管理 Ripple 状态机 (OPEN → PROPAGATING → RESOLVING → RESOLVED)，
禁止非法回退。
"""
from __future__ import annotations

from lingwen_core.domain import Ripple, RippleState, RippleStateChangedEvent
from lingwen_core.ports import EventStorePort


# 合法状态转移表 (from → set of allowed to)
_VALID_TRANSITIONS: dict[RippleState, set[RippleState]] = {
    RippleState.OPEN: {RippleState.PROPAGATING},
    RippleState.PROPAGATING: {RippleState.OPEN, RippleState.RESOLVING},
    RippleState.RESOLVING: {RippleState.PROPAGATING, RippleState.RESOLVED},
    RippleState.RESOLVED: set(),  # 终态
}


class MergeRipplesUseCase:
    """涟漪合并用例

    提供 merge_to_state() 推进 ripple 状态，校验合法转移。
    """

    def __init__(self, store: EventStorePort) -> None:
        self._store = store

    def merge_to_state(self, ripple: Ripple, new_state: RippleState) -> RippleStateChangedEvent:
        """把 ripple 推到新状态，发射 RippleStateChangedEvent。"""
        allowed = _VALID_TRANSITIONS.get(ripple.state, set())
        if new_state not in allowed and new_state != ripple.state:
            raise ValueError(
                f"Invalid Ripple state transition: {ripple.state.value} → {new_state.value}. "
                f"Allowed: {sorted(s.value for s in allowed)}"
            )

        event = RippleStateChangedEvent(
            payload={
                "ripple_id": ripple.ripple_id,
                "from_state": ripple.state.value,
                "to_state": new_state.value,
            }
        )
        self._store.append(event)
        return event