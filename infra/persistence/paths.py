"""Phase 15.0 T2.4: 6 个 DB 路径常量.

集中 179 处散落的 `db_path = ...` 字符串, 改为单点定义。

设计:
- 相对 LingWen 项目根, 用 `pathlib.Path`
- **不强制文件存在** — caller 自己判断 (registry.get 时也不强制)
- 预算 / cost 共用 cost_tracker.db (per spec §现状审计)
"""
from __future__ import annotations

from pathlib import Path

# 项目根 = LingWen/ (本文件在 infra/persistence/, 上溯 2 级)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 6 个 DB 路径常量 (统一 `.state/` 目录)
RIPPLE_DB: Path = PROJECT_ROOT / ".state" / "ripple.db"
COST_TRACKER_DB: Path = PROJECT_ROOT / ".state" / "cost_tracker.db"
WORKFLOW_DB: Path = PROJECT_ROOT / ".state" / "workflow.db"
READING_POWER_DB: Path = PROJECT_ROOT / ".state" / "reading_power.db"
RELATIONSHIP_DB: Path = PROJECT_ROOT / ".state" / "social_engine" / "relationship_network.db"
CROSS_VOLUME_DB: Path = PROJECT_ROOT / ".state" / "cross_volume.db"  # 兼容别名


__all__ = [
    "PROJECT_ROOT",
    "RIPPLE_DB",
    "COST_TRACKER_DB",
    "WORKFLOW_DB",
    "READING_POWER_DB",
    "RELATIONSHIP_DB",
    "CROSS_VOLUME_DB",
]
