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

v16.5 #N.3: Migrated to SqliteStorageAdapter from lingwen_storage.
Replaces direct sqlite3.connect() + local _connect contextmanager
with storage.with_connection/with_transaction (callback-based).
Public API unchanged (BudgetService(db_path=..., init_if_missing=...)).
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from lingwen_llm.providers.cost_tracker import CostBudgetExceeded
from lingwen_llm.providers.model_tiers import ModelTier
from lingwen_storage.sqlite_storage_adapter import SqliteStorageAdapter

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


@dataclass(frozen=True)
class TierBudgetEntry:
    """Per-tier budget persistence entry (append-only) — Phase 8.15.

    Mirror BudgetEntry 但用 ModelTier 替 scope. 跟现 'run/day/week' budget
    独立表 `budgets_by_tier` 共存, 0 共享列 (除 id PK + usd + set_at).
    """
    id: int
    tier: ModelTier
    usd: float
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

    v16.5 #N.3: storage layer now SqliteStorageAdapter from lingwen_storage
    (previously direct sqlite3). Public API preserved.
    """

    def __init__(
        self,
        db_path=None,
        init_if_missing: bool = True,
    ) -> None:
        if isinstance(db_path, str):
            db_path = Path(db_path)
        self.db_path = db_path or _DB_PATH
        warnings.warn(
            "Phase 15.0 T2.8: BudgetService 直接实例化已弃用, "
            "请使用 infra.persistence.registry.get('budget') singleton. "
            "DB 路径统一在 infra/persistence/paths.py 定义.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._storage = SqliteStorageAdapter(str(self.db_path))
        if init_if_missing:
            self._ensure_db_path()

    def _ensure_db_path(self) -> None:
        if str(self.db_path) != ":memory:" and not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def init_db(self) -> None:
        """初始化 budgets 表 + 2 索引 (幂等 CREATE IF NOT EXISTS)

        Phase 8.15: 同时建 budgets_by_tier 表 + idx (per-tier budget).
        旧 budgets 表 0 改, 0 删行/列. CREATE IF NOT EXISTS 幂等.
        """
        def _do(conn) -> None:
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
                CREATE TABLE IF NOT EXISTS budgets_by_tier (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tier TEXT NOT NULL CHECK(tier IN ('haiku', 'sonnet', 'opus')),
                    usd REAL NOT NULL CHECK(usd >= 0),
                    set_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_budgets_by_tier_tier
                    ON budgets_by_tier(tier, id DESC);
            """)
        self._storage.with_transaction(_do)

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

        def _do(conn) -> int:
            cursor = conn.execute(
                "INSERT INTO budgets (scope, usd, run_id, set_at) VALUES (?, ?, ?, ?)",
                (scope, usd, run_id, set_at),
            )
            return cursor.lastrowid

        new_id = self._storage.with_transaction(_do)
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

        def _do(conn):
            return conn.execute(sql, params).fetchone()

        row = self._storage.with_connection(_do)
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

        def _do(conn):
            return conn.execute(
                """
                SELECT run_id, MAX(id) AS last_id FROM budgets
                WHERE scope = 'run' AND run_id IS NOT NULL
                GROUP BY run_id
                ORDER BY last_id DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()

        rows = self._storage.with_connection(_do)
        return [r["run_id"] for r in rows]

    # === Phase 8.15: Per-Tier Budget (parallel to run/day/week) ===

    def set_by_tier(
        self,
        tier: ModelTier,
        usd: float,
    ) -> TierBudgetEntry:
        """插一条新 tier budget (append-only) — Phase 8.15.

        Mirror `set` 但用 ModelTier 替 scope. 跟 run/day/week 0 共享行.
        """
        if usd < 0:
            raise ValueError(f"usd must be non-negative, got {usd}")
        self.init_db()
        set_at = datetime.now(timezone.utc).isoformat()

        def _do(conn) -> int:
            cursor = conn.execute(
                "INSERT INTO budgets_by_tier (tier, usd, set_at) VALUES (?, ?, ?)",
                (tier.value, usd, set_at),
            )
            return cursor.lastrowid

        new_id = self._storage.with_transaction(_do)
        return TierBudgetEntry(
            id=new_id,
            tier=tier,
            usd=usd,
            set_at=datetime.fromisoformat(set_at),
        )

    def get_by_tier(
        self,
        tier: ModelTier,
    ) -> Optional[TierBudgetEntry]:
        """返该 tier 最新一条 (None if 0 行) — Phase 8.15.

        Mirror `get_current` 但用 ModelTier 替 scope.
        """
        self.init_db()

        def _do(conn):
            return conn.execute(
                "SELECT id, tier, usd, set_at FROM budgets_by_tier "
                "WHERE tier = ? ORDER BY id DESC LIMIT 1",
                (tier.value,),
            ).fetchone()

        row = self._storage.with_connection(_do)
        if row is None:
            return None
        return TierBudgetEntry(
            id=row["id"],
            tier=ModelTier(row["tier"]),
            usd=row["usd"],
            set_at=datetime.fromisoformat(row["set_at"]),
        )

    def list_by_tiers(self) -> list[TierBudgetEntry]:
        """返每 tier 最新一条 (current per tier) — Phase 8.15.

        SQL: 子查询 MAX(id) GROUP BY tier 取每 tier current id,
        跟 Phase 8.12 list_runs 同 pattern.
        """
        self.init_db()

        def _do(conn):
            return conn.execute(
                """
                SELECT b.id, b.tier, b.usd, b.set_at
                FROM budgets_by_tier b
                INNER JOIN (
                    SELECT tier, MAX(id) AS max_id FROM budgets_by_tier GROUP BY tier
                ) m ON b.tier = m.tier AND b.id = m.max_id
                ORDER BY b.id DESC
                """,
            ).fetchall()

        rows = self._storage.with_connection(_do)
        return [
            TierBudgetEntry(
                id=row["id"],
                tier=ModelTier(row["tier"]),
                usd=row["usd"],
                set_at=datetime.fromisoformat(row["set_at"]),
            )
            for row in rows
        ]

    def check_all_tiers(
        self,
        cost_by_tier: dict[ModelTier, float],
    ) -> None:
        """检查 3 tier budget, 第 1 个超阈 raise CostBudgetExceeded(scope='tier', tier=...).

        顺序: haiku → sonnet → opus (Enum 迭代顺序, deterministic).
        跟 Phase 8.12 check_all_scopes 同 pattern: 显 for tier in ModelTier:,
        raise 早于 scheduler 兜底, record 已在 raise 前.

        Args:
            cost_by_tier: {tier: used_usd} 当前累计 (从 CostTracker.cost_by_tier() 拿)

        Raises:
            CostBudgetExceeded: 第 1 个超阈 raise (scope='tier', tier=ModelTier.X)
        """
        for tier in ModelTier:  # haiku, sonnet, opus (Enum 顺序, deterministic)
            entry = self.get_by_tier(tier)
            if entry is None or entry.usd <= 0:
                continue  # 未设跳过
            used = cost_by_tier.get(tier, 0.0)
            if used > entry.usd:
                raise CostBudgetExceeded(
                    used_usd=used,
                    budget_usd=entry.usd,
                    scope="tier",
                    tier=tier,
                )


__all__ = ["BudgetService", "BudgetEntry", "TierBudgetEntry"]