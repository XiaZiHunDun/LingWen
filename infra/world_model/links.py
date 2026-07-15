"""灵文 Ripple ↔ Subplot 联动 (Phase 2.3)

Doc 1 §3.4 + Doc 3 联动:Ripple RESOLVED 时,联动其相关 subplot。

核心 API:
- link_subplot_to_ripple(plot, ripple, link_kind) → Plot
  - 把 ripple.ripple_id 加入 plot.related_ripples (idempotent)
  - 不修改原 plot,返回新 Plot
- apply_ripple_resolution(ripple_reg, subplot_reg, ripple_id, current_ch, auto_close)
  - 涟漪 RESOLVED 时,查找所有 related subplot
  - ACTIVE → CLOSING 转换 (per Phase 1.2 状态机)
  - auto_close=False: dry-run,只记录不改
  - 跳过终态 (CLOSED / ABANDONED)
  - 跳过非法转换 (PAUSED → CLOSING 等)
- LinkAction frozen dataclass 记录每次转换
- _SubplotRegistryLike Protocol 抽象 (解耦具体 Registry)

不实施 (后续阶段):
- 跨包事务 (atomic commit/rollback,Phase 3+)
- 异步联动 (Phase 3+)
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Optional, Protocol

# Note: 不导入 infra.subplot.data_structures 或 infra.subplot.lifecycle
# 这两个模块都依赖 infra.world_model → 循环 import
# 改用 lazy import inside function bodies

if TYPE_CHECKING:
    from infra.subplot.data_structures import Plot, PlotStatus
    from infra.world_model.data_structures import Ripple
    from infra.world_model.registry import RippleRegistry


# CLOSING_MIN_CHAPTERS 在 infra.subplot.lifecycle (值为 2)
# 在运行时 lazy import 读取
def _get_closing_min_chapters() -> int:
    from infra.subplot.lifecycle import CLOSING_MIN_CHAPTERS
    return CLOSING_MIN_CHAPTERS


@dataclass(frozen=True)
class LinkAction:
    """单次 ripple → subplot 联动动作记录

    Args:
        plot_id: 受影响的 plot
        from_status: 转换前状态
        to_status: 转换后状态 (auto_close=False 时为计划目标)
        reason: 触发原因 (e.g. "ripple r1 resolved")
    """

    plot_id: str
    from_status: Any  # PlotStatus (避免循环)
    to_status: Any  # PlotStatus
    reason: str


class _SubplotRegistryLike(Protocol):
    """Subplot Registry 最小接口 (Protocol 解耦)

    使用 update_status 而非 update_plot,获得状态机校验 +
    CLOSING_MIN_CHAPTERS 强制,避免绕过 phase 1.2 的合法性检查。
    """

    def list_all(self) -> tuple[Plot, ...]: ...
    def get_plot(self, plot_id: str) -> Optional[Plot]: ...
    def update_status(
        self,
        plot_id: str,
        new_status: "PlotStatus",
        current_ch: int,
        close_ch: Optional[int] = None,
    ) -> "Plot": ...


# ============ 核心 API ============

def link_subplot_to_ripple(
    plot: "Plot", ripple: "Ripple", link_kind: str = "primary"
) -> "Plot":
    """加入 ripple_id 到 plot.related_ripples (idempotent)

    Args:
        plot: 原 Plot (不可变)
        ripple: Ripple 实例 (只需 ripple_id)
        link_kind: 链接类型 (primary / secondary), 保留字段,当前未使用

    Returns:
        含新 ripple_id 的新 Plot (原 plot 不变)

    Note:
        link_kind 是为未来多 ripple 关联设计,当前 Plot.related_ripples
        仅存 id 列表,无法区分 primary/secondary。如需扩展,可改为
        tuple[(ripple_id, link_kind), ...]。
    """
    if ripple.ripple_id in plot.related_ripples:
        return plot  # 幂等:已存在则原样返回
    return replace(
        plot, related_ripples=(*plot.related_ripples, ripple.ripple_id)
    )


def apply_ripple_resolution(
    ripple_registry: "RippleRegistry",
    subplot_registry: _SubplotRegistryLike,
    ripple_id: str,
    current_ch: int,
    auto_close: bool = True,
) -> tuple[LinkAction, ...]:
    """涟漪 RESOLVED 时,联动其 related subplot

    联动规则:
    1. 找到 ripple (RippleNotFoundError if missing)
    2. 遍历所有 subplot
    3. 只处理 related_ripples 含 ripple_id 的 plot
    4. 跳过终态 (CLOSED / ABANDONED) — 幂等
    5. 跳过非法转换 (PAUSED → CLOSING 等) — 安全
    6. ACTIVE → CLOSING 合法转换,记录 LinkAction
    7. auto_close=False 时,记录 action 但不更新 registry (dry-run)

    Args:
        ripple_registry: RippleRegistry 实例
        subplot_registry: 任何实现 _SubplotRegistryLike 的对象
        ripple_id: 目标 ripple
        current_ch: 当前章节号 (用于计算 close_ch = current_ch + 2)
        auto_close: True (默认) 实际更新状态;False 仅记录 (dry-run)

    Returns:
        LinkAction 元组 (按遍历顺序)

    Raises:
        RippleNotFoundError: ripple_id 未注册
    """
    # Lazy import 避开 subplot.data_structures ↔ world_model 循环
    from infra.subplot.data_structures import PlotStatus

    # 1. 校验 ripple 存在 (无 ripple → RippleNotFoundError)
    ripple_registry.require_ripple(ripple_id)

    closing_min = _get_closing_min_chapters()

    actions: list[LinkAction] = []

    for plot in subplot_registry.list_all():
        # 3. 只处理 related 涟漪
        if ripple_id not in plot.related_ripples:
            continue

        # 4. 跳过终态
        if plot.status in (PlotStatus.CLOSED, PlotStatus.ABANDONED):
            continue

        # 5. 只处理 ACTIVE (其他非合法转换状态)
        if plot.status != PlotStatus.ACTIVE:
            continue

        # 6. ACTIVE → CLOSING 合法转换
        new_close_ch = current_ch + closing_min

        action = LinkAction(
            plot_id=plot.plot_id,
            from_status=plot.status,
            to_status=PlotStatus.CLOSING,
            reason=(
                f"ripple {ripple_id} resolved"
                + (" (dry-run)" if not auto_close else "")
            ),
        )

        if auto_close:
            subplot_registry.update_status(
                plot.plot_id,
                PlotStatus.CLOSING,
                current_ch=current_ch,
                close_ch=new_close_ch,
            )

        actions.append(action)

    return tuple(actions)


__all__ = [
    "LinkAction",
    "link_subplot_to_ripple",
    "apply_ripple_resolution",
]
