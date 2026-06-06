"""Budget 持久化 — Phase 8.12

Per-run / per-day / per-week budget persistence (append-only `budgets` table).
Reuses infra/.state/cost_tracker.db (跟 cost_records 共存,避免双 db 文件).

设计:
- 单表 budgets (id PK, scope, usd, run_id, set_at) + 2 索引 (scope+set_at, run_id)
- Append-only: set 插新行, "current" = `ORDER BY id DESC LIMIT 1 WHERE scope=?`
- Window semantics: 'day' = UTC 00:00-23:59, 'week' = Mon-Sun
- 'run' scope 不需 window, 用 run_id 隔离

Why single DB 跟 cost_records 共存:
- 跟 Phase 8.5 cost_records 表并存, 单一 file 简化 ops
- gitignored infra/.state/cost_tracker.db 路径已就位

Backward compat: scope='run' 跟 Phase 8.8 _current_budget_usd 等价 (in-memory)
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator, Optional

from infra.ai_service.cost_tracker import CostBudgetExceeded

# 默认 DB 路径: 复用 cost_tracker.db (gitignored)
_DB_PATH = Path(__file__).parent.parent / ".state" / "cost_tracker.db"


@dataclass(frozen=True)
class BudgetEntry:
    """Budget 持久化条目 (append-only)"""
    id: int
    scope: str  # 'run' | 'day' | 'week'
    usd: float
    run_id: Optional[str]
    set_at: datetime  # UTC


def _is_within_window(set_at: datetime, scope: str, now: datetime) -> bool:
    """检查 set_at 是否在 scope 对应 window 内 (UTC)."""
    if scope == "day":
        return set_at.date() == now.date()
    elif scope == "week":
        # Mon-Sun: 推到本周一 00:00
        days_since_monday = now.weekday()
        week_start = (now - timedelta(days=days_since_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return set_at >= week_start
    return True  # 'run' 不需 window check


class BudgetService:
    """SQLite 持久化 Budget (Phase 8.12)

    3 档 scope (run / day / week), append-only 历史,
    per-run 用 run_id 隔离, per-day/per-week 用 UTC Calendar window.
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        init_if_missing: bool = True,
    ) -> None:
        self.db_path = db_path or _DB_PATH
        if init_if_missing:
            self._ensure_db_path()

    def _ensure_db_path(self) -> None:
        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.db_path), timeout=5)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self) -> None:
        """初始化 budgets 表 + 2 索引 (幂等 CREATE IF NOT EXISTS)"""
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scope TEXT NOT NULL CHECK(scope IN ('run', 'day', 'week')),
                    usd REAL NOT NULL CHECK(usd >= 0),
                    run_id TEXT,
                    set_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_budgets_scope_set_at
                    ON budgets(scope, set_at DESC);
                CREATE INDEX IF NOT EXISTS idx_budgets_run_id
                    ON budgets(run_id);
            """)

    def set(
        self,
        scope: str,
        usd: float,
        run_id: Optional[str] = None,
    ) -> BudgetEntry:
        """插一条新 budget (append-only)"""
        if scope not in ("run", "day", "week"):
            raise ValueError(f"scope must be 'run'/'day'/'week', got {scope!r}")
        if usd < 0:
            raise ValueError(f"usd must be non-negative, got {usd}")
        self.init_db()
        set_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO budgets (scope, usd, run_id, set_at) VALUES (?, ?, ?, ?)",
                (scope, usd, run_id, set_at),
            )
            new_id = cursor.lastrowid
        return BudgetEntry(
            id=new_id,
            scope=scope,
            usd=usd,
            run_id=run_id,
            set_at=datetime.fromisoformat(set_at),
        )

    def get_current(
        self,
        scope: str,
        run_id: Optional[str] = None,
    ) -> Optional[BudgetEntry]:
        """返该 scope 最新一条 (None if 0 行)"""
        self.init_db()
        if scope == "run" and run_id is not None:
            sql = (
                "SELECT id, scope, usd, run_id, set_at FROM budgets "
                "WHERE scope = ? AND run_id = ? ORDER BY id DESC LIMIT 1"
            )
            params: tuple = (scope, run_id)
        else:
            sql = (
                "SELECT id, scope, usd, run_id, set_at FROM budgets "
                "WHERE scope = ? ORDER BY id DESC LIMIT 1"
            )
            params = (scope,)
        with self._connect() as conn:
            row = conn.execute(sql, params).fetchone()
        if row is None:
            return None
        return BudgetEntry(
            id=row["id"],
            scope=row["scope"],
            usd=row["usd"],
            run_id=row["run_id"],
            set_at=datetime.fromisoformat(row["set_at"]),
        )

    def check_all_scopes(
        self,
        total_cost_usd: float,
        current_run_id: Optional[str] = None,
    ) -> None:
        """检查 3 档 budget, 任一超阈 raise CostBudgetExceeded(scope=...)

        Priority: per-run > per-day > per-week (run 优先因为最严苛)
        Window: per-day/per-week 用 UTC Calendar (set_at 必须在 window 内)
        """
        now = datetime.now(timezone.utc)
        # 1. Check per-run (current_run_id 必传)
        if current_run_id is not None:
            run_budget = self.get_current("run", run_id=current_run_id)
            if run_budget is not None and total_cost_usd > run_budget.usd:
                raise CostBudgetExceeded(
                    used_usd=total_cost_usd,
                    budget_usd=run_budget.usd,
                    scope="run",
                )
        # 2. Check per-day (window 内)
        day_budget = self.get_current("day")
        if (
            day_budget is not None
            and _is_within_window(day_budget.set_at, "day", now)
            and total_cost_usd > day_budget.usd
        ):
            raise CostBudgetExceeded(
                used_usd=total_cost_usd,
                budget_usd=day_budget.usd,
                scope="day",
            )
        # 3. Check per-week (window 内)
        week_budget = self.get_current("week")
        if (
            week_budget is not None
            and _is_within_window(week_budget.set_at, "week", now)
            and total_cost_usd > week_budget.usd
        ):
            raise CostBudgetExceeded(
                used_usd=total_cost_usd,
                budget_usd=week_budget.usd,
                scope="week",
            )

    def list_runs(self, limit: int = 20) -> list[str]:
        """返最近 N 个 distinct run_id (按最近 set_at 倒序)"""
        self.init_db()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT run_id, MAX(id) AS last_id FROM budgets
                WHERE scope = 'run' AND run_id IS NOT NULL
                GROUP BY run_id
                ORDER BY last_id DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [r["run_id"] for r in rows]


__all__ = ["BudgetService", "BudgetEntry"]
