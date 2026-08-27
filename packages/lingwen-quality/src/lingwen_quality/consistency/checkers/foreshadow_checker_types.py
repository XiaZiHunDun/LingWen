"""ForeshadowChecker 公共类型/Protocol（拆分自 foreshadow_checker.py）。

包含：
- ``_get_ripple_state_and_grace`` — Ripple 状态/宽限常量懒加载包装
- ``_RippleRegistryLike`` — Ripple Registry 最小接口 Protocol
- ``ForeshadowIssue`` — 单章节伏笔缺失记录
- ``PlotThread`` — 伏笔条目数据类

下游消费者统一从 ``lingwen_quality.consistency.checkers.foreshadow_checker``
导入（re-export），保持兼容性。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

# TODO(Phase18): Replace infra.world_model with proper domain entity (Story / Ripple)
# in packages/lingwen-quality (Phase 17.9). Tracked in plan §Task 17.9 + 18.1.
# Lazy-imported so that the module remains importable even if infra.world_model is not
# available (e.g. when only lingwen-quality is installed standalone).
try:  # pragma: no cover - optional legacy import
    from lingwen_core.domain.ripple import (
        RESOLUTION_GRACE_CH,  # noqa: F401
        RippleState,
    )
except ImportError:
    RippleState = None  # type: ignore[assignment]
    RESOLUTION_GRACE_CH = 5  # sensible default (chapters)


def _get_ripple_state_and_grace():
    return RippleState, RESOLUTION_GRACE_CH


class _RippleRegistryLike(Protocol):
    """Ripple Registry 最小接口 (Protocol 解耦)"""

    def list_all(self) -> tuple: ...


@dataclass
class ForeshadowIssue:
    chapter: str
    foreshadow_text: str
    level: str
    severity: str
    description: str


@dataclass
class PlotThread:
    """伏笔"""
    id: str
    content: str
    introduced_chapter: int
    expected_resolve_chapter: int
    actual_resolve_chapter: Optional[int] = None
    status: str = "unresolved"  # unresolved, resolved, overdue
    resolve_type: Optional[str] = None  # full, partial, wrong


__all__ = [
    "_get_ripple_state_and_grace",
    "_RippleRegistryLike",
    "ForeshadowIssue",
    "PlotThread",
]
