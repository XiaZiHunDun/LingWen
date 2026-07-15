"""Phase 15.0 T2.3: DDL schema 注册中心.

集中 6 个 storage 类的初始 DDL, 让 schema 升级时只查一处。

设计原则:
- **不替代** `RippleStorage._apply_schema_migrations` 等类内的 additive migration。
  SCHEMAS 仅含**初始 DDL** (CREATE TABLE IF NOT EXISTS), 增量迁移仍由原类控制。
- **不导入** 真实 storage 类 (避免循环 import + 副作用)。DDL 直接内联。
- 测试通过对比: 调用 apply_schema 后 pragma table_list 跟原 storage 初始化后一致。
"""
from __future__ import annotations

import sqlite3
from typing import Dict, List

# 6 个 storage 的初始 DDL. 内容来自对应的 _init_db / _apply_schema_migrations 起始段.
SCHEMAS: Dict[str, List[str]] = {
    "ripple": [
        """
        CREATE TABLE IF NOT EXISTS ripple_impact_scores (
            ripple_id TEXT PRIMARY KEY,
            impact_score REAL NOT NULL DEFAULT 0.0
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ripples (
            id TEXT PRIMARY KEY,
            trigger_volume INTEGER NOT NULL,
            trigger_chapter INTEGER NOT NULL,
            affected_nodes TEXT NOT NULL,
            affected_edges TEXT NOT NULL,
            proposed_actions TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """,
    ],
    "cost": [
        """
        CREATE TABLE IF NOT EXISTS cost_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            agent TEXT NOT NULL,
            operation TEXT NOT NULL,
            tokens_in INTEGER NOT NULL DEFAULT 0,
            tokens_out INTEGER NOT NULL DEFAULT 0,
            cost_usd REAL NOT NULL DEFAULT 0.0,
            project TEXT,
            metadata TEXT
        )
        """,
    ],
    "budget": [
        """
        CREATE TABLE IF NOT EXISTS budget_allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project TEXT NOT NULL,
            window_start TEXT NOT NULL,
            window_end TEXT NOT NULL,
            allocated_usd REAL NOT NULL,
            spent_usd REAL NOT NULL DEFAULT 0.0
        )
        """,
    ],
    "reading": [
        """
        CREATE TABLE IF NOT EXISTS hooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter INTEGER NOT NULL,
            position INTEGER NOT NULL,
            hook_type TEXT NOT NULL,
            description TEXT NOT NULL,
            resolved_in_chapter INTEGER,
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS coolpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter INTEGER NOT NULL,
            tension_level INTEGER NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """,
    ],
    "workflow": [
        """
        CREATE TABLE IF NOT EXISTS workflow_runs (
            id TEXT PRIMARY KEY,
            project TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            metadata TEXT
        )
        """,
    ],
    "relationship": [
        """
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            char_a TEXT NOT NULL,
            char_b TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            strength REAL NOT NULL DEFAULT 0.5,
            last_updated TEXT NOT NULL,
            UNIQUE(char_a, char_b)
        )
        """,
    ],
}


def apply_schema(name: str, conn: sqlite3.Connection) -> None:
    """对给定 connection 执行 name 对应 schema 的所有 DDL.

    Args:
        name: SCHEMAS key (ripple/cost/budget/reading/workflow/relationship)
        conn: 已打开的 sqlite3.Connection

    Raises:
        KeyError: name 不在 SCHEMAS 中
    """
    if name not in SCHEMAS:
        raise KeyError(
            f"schema '{name}' 未注册. 已注册: {sorted(SCHEMAS.keys())}"
        )
    for ddl in SCHEMAS[name]:
        conn.executescript(ddl)


def registered_schema_names() -> List[str]:
    """返回所有已注册 schema 名 (按字母排序)."""
    return sorted(SCHEMAS.keys())


__all__ = ["SCHEMAS", "apply_schema", "registered_schema_names"]
