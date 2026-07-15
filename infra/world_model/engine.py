"""灵文涟漪引擎 (Phase 1.5 — RippleEngine 6 方法)

Doc 1 §3.4 (涟漪机制 v1.0) — 挖坑/扩散/平复 核心算法。

RippleEngine 不持有状态 (stateless service),所有状态变更通过
`dataclasses.replace` 返回新 Ripple,registry 替换原记录。

不导出 (后续阶段):
- LLM 抽取 ripple 描述 (Phase 2)
- Ripple ↔ Subplot 跨包联动 (Phase 2+)
- 跨卷 ripple 谱系 (Phase 3+)
- `pacing_checker` 集成 `wavefront` (Phase 2+,detector wiring)
"""
from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Protocol

from infra.world_model.data_structures import (
    NodeId,
    ResolutionMode,
    Ripple,
    RippleState,
)
from infra.world_model.lifecycle import (
    MAX_OPEN_RIPPLOTS,
    RESOLUTION_GRACE_CH,
    can_transition,
)

if TYPE_CHECKING:
    from infra.world_model.queries import detect_unresolved_ripples


class _RegistryLike(Protocol):
    """最小 registry 接口,RippleEngine 不耦合具体 RippleRegistry 实现。

    实际 RippleRegistry 在 registry.py 实施 (1.5.h)。本 Protocol 让 engine
    可独立测试 + 解耦。
    """

    def add_ripple(self, ripple: Ripple) -> None: ...
    def get_ripple(self, ripple_id: str) -> Ripple | None: ...
    def update_ripple(self, ripple: Ripple) -> None: ...
    def list_active(self) -> tuple[Ripple, ...]: ...


class RippleEngine:
    """涟漪 6 方法:挖坑/扩散/平复/崩塌风险/波前查询"""

    def register(
        self,
        registry: _RegistryLike,
        ripple_id: str,
        origin_event: str,
        origin_ch: int,
        planned_resolve_ch: int,
        affected_nodes: tuple[NodeId, ...] = (),
        decay_rate: float = 0.2,
    ) -> Ripple:
        """挖坑:注册新 ripple (state=OPEN),wavefront=[origin_ch]

        校验:
        - planned_resolve_ch > origin_ch (否则 ValueError)
        - registry.add_ripple 自动校验重复 + 10-limit
        """
        if planned_resolve_ch <= origin_ch:
            raise ValueError(
                f"planned_resolve_ch ({planned_resolve_ch}) must be > origin_ch ({origin_ch})"
            )
        ripple = Ripple(
            ripple_id=ripple_id,
            origin_event=origin_event,
            origin_ch=origin_ch,
            affected_nodes=affected_nodes,
            state=RippleState.OPEN,
            wavefront=(origin_ch,),
            decay_rate=decay_rate,
            planned_resolve_ch=planned_resolve_ch,
        )
        registry.add_ripple(ripple)
        return ripple

    def propagate(
        self,
        registry: _RegistryLike,
        ripple_id: str,
        current_ch: int,
        affected_nodes: tuple[NodeId, ...] = (),
        affected_relations: tuple = (),
    ) -> Ripple:
        """扩散:append current_ch to wavefront (dedup)

        状态语义:OPEN → PROPAGATING (首次 propagate);PROPAGATING 重复 propagate
        只更新 wavefront,不重置 state。RESOLVING/RESOLVED 状态拒绝 (调用方应
        用 start_resolution / resolve)。

        Args:
            affected_relations: 占位 (Ripple.affected_relations 字段已就位,本 phase 不深入)
        """
        ripple = self._get_or_raise(registry, ripple_id)
        if ripple.state not in (RippleState.OPEN, RippleState.PROPAGATING):
            raise ValueError(
                f"cannot propagate ripple {ripple_id!r} from state {ripple.state.value!r} "
                f"(only OPEN|PROPAGATING allowed)"
            )
        new_wavefront = (
            ripple.wavefront
            if current_ch in ripple.wavefront
            else ripple.wavefront + (current_ch,)
        )
        new_ripple = dataclasses.replace(
            ripple,
            state=RippleState.PROPAGATING,
            wavefront=new_wavefront,
            affected_nodes=affected_nodes or ripple.affected_nodes,
            affected_relations=affected_relations or ripple.affected_relations,
        )
        registry.update_ripple(new_ripple)
        return new_ripple

    def start_resolution(self, registry: _RegistryLike, ripple_id: str) -> Ripple:
        """平复开始:OPEN|PROPAGATING → RESOLVING"""
        ripple = self._get_or_raise(registry, ripple_id)
        if not can_transition(ripple, RippleState.RESOLVING):
            raise ValueError(
                f"cannot start_resolution ripple {ripple_id!r} from state {ripple.state.value!r}"
            )
        new_ripple = dataclasses.replace(ripple, state=RippleState.RESOLVING)
        registry.update_ripple(new_ripple)
        return new_ripple

    def resolve(
        self,
        registry: _RegistryLike,
        ripple_id: str,
        current_ch: int,
        mode: ResolutionMode,
    ) -> Ripple:
        """平复:任意非 RESOLVED → RESOLVED,set resolved_ch=current_ch"""
        ripple = self._get_or_raise(registry, ripple_id)
        if not can_transition(ripple, RippleState.RESOLVED):
            raise ValueError(
                f"cannot resolve ripple {ripple_id!r} from state {ripple.state.value!r}"
            )
        new_ripple = dataclasses.replace(
            ripple,
            state=RippleState.RESOLVED,
            resolved_ch=current_ch,
        )
        registry.update_ripple(new_ripple)
        return new_ripple

    def compute_collapse_risk(
        self,
        registry: _RegistryLike,
        current_ch: int,
        grace: int = RESOLUTION_GRACE_CH,
    ) -> float:
        """崩塌风险:stale_ripples / MAX_OPEN_RIPPLOTS,clamped [0, 1]

        Doc 1 §3.4 rule:
        - 累计未平复 > 10 → 崩塌风险 > 0.7
        - 崩塌风险 > 0.8 → 系统报警

        当前实现用 stale 数 (current_ch > planned_resolve_ch + grace) 作为
        简化代理。Phase 2+ 可加 decay_rate 加权。
        """
        stale_count = sum(
            1
            for r in registry.list_active()
            if r.state != RippleState.RESOLVED
            and r.planned_resolve_ch is not None
            and current_ch > r.planned_resolve_ch + grace
        )
        return min(1.0, stale_count / MAX_OPEN_RIPPLOTS)

    def get_active_wavefront(self, ripple: Ripple, current_ch: int) -> tuple[int, ...]:
        """活动波前:wavefront ∩ [origin_ch, current_ch]

        返回截至 current_ch 时,所有已激活的 wavefront 章节。
        """
        return tuple(w for w in ripple.wavefront if ripple.origin_ch <= w <= current_ch)

    def _get_or_raise(self, registry: _RegistryLike, ripple_id: str) -> Ripple:
        ripple = registry.get_ripple(ripple_id)
        if ripple is None:
            raise ValueError(f"ripple {ripple_id!r} not found in registry")
        return ripple


__all__ = ["RippleEngine"]
