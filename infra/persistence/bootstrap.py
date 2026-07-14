"""Phase 15.0 T2.5: 6 storage 注册到 registry.

集中 6 个 storage 类的 `register()` 调用, 避免散落到 6 个调用方。

设计:
- **不在 import 时副作用** — caller 显式调 `register_all()` 一次。
- 6 storage 接收 db_path 参数, registry 透传。
- 失败 case (例如 class 不存在) 走 try/except + warning, 不影响其他 storage。

用法:
    from infra.persistence.bootstrap import register_all
    from infra.persistence.registry import get

    register_all()
    storage = get("ripple")
"""
from __future__ import annotations

import warnings
from typing import Callable, Dict, List, Tuple

from infra.persistence.paths import (
    COST_TRACKER_DB,
    READING_POWER_DB,
    RELATIONSHIP_DB,
    RIPPLE_DB,
    WORKFLOW_DB,
)
from infra.persistence.registry import register


# 6 个 storage 注册声明 (name, class_loader, db_path)
# class_loader 走 lazy import 避免 bootstrap 本身触发 storage 副作用
def _load_ripple_storage() -> type:
    from infra.cross_volume.storage import RippleStorage

    return RippleStorage


def _load_cost_tracker_db() -> type:
    from infra.agent_system.cost_persistence import CostTrackerDB

    return CostTrackerDB


def _load_budget_persistence() -> type:
    from infra.agent_system.budget_persistence import BudgetService

    return BudgetService


def _load_reading_power_db() -> type:
    from infra.reading_power.db import ReadingPowerDB

    return ReadingPowerDB


def _load_workflow_db() -> type:
    from infra.state.database import WorkflowDB

    return WorkflowDB


def _load_relationship_tracker() -> type:
    from infra.agent_system.social_engine.relationship_tracker import (
        RelationshipTracker,
    )

    return RelationshipTracker


# 集中声明
_REGISTRATIONS: List[Tuple[str, Callable[[], type], object]] = [
    ("ripple", _load_ripple_storage, RIPPLE_DB),
    ("cost", _load_cost_tracker_db, COST_TRACKER_DB),
    ("budget", _load_budget_persistence, COST_TRACKER_DB),  # 共用 cost db
    ("reading", _load_reading_power_db, READING_POWER_DB),
    ("workflow", _load_workflow_db, WORKFLOW_DB),
    ("relationship", _load_relationship_tracker, RELATIONSHIP_DB),
]


def register_all() -> Dict[str, str]:
    """注册 6 个 storage 到 registry.

    Returns:
        {name: "ok" | "fail: reason"} 用于 caller 诊断。
    """
    results: Dict[str, str] = {}
    for name, loader, db_path in _REGISTRATIONS:
        try:
            cls = loader()
            register(name, cls, db_path=str(db_path))
            results[name] = "ok"
        except Exception as e:  # noqa: BLE001 — 走 warning, 不破坏其他注册
            results[name] = f"fail: {type(e).__name__}: {e}"
            warnings.warn(
                f"Phase 15.0 T2.5: register '{name}' failed: {e}",
                stacklevel=2,
            )
    return results


__all__ = ["register_all", "_REGISTRATIONS"]
