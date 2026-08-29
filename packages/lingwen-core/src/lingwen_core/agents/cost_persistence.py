"""Cost 持久化 — Phase 8.5

Doc 4 §11 Phase 8.5: SQLite 持久化 CostRecord 列表 (mirror ReadingPowerDB pattern).

设计:
- 单表 cost_records (id PK, scenario, tier, input_tokens, output_tokens,
  cost_usd, timestamp) + 3 索引 (scenario, tier, timestamp)
  (Phase 8.22: 加 timestamp 索引, 优化 WHERE timestamp >= ? 性能,
   rows > 1k 时显著; 当前 ~50 rows 不卡, 0 行为破坏)
- 复用 CostRecord frozen dataclass (in-memory CostTracker 一致)
- 路径: infra/.state/cost_tracker.db (gitignored, 跟 reading_power.db 错开)
- 初始化: lazy _init_db (调 record/records/cost_*_methods 时触发)
- 复用 compute_cost (model_tiers.py) 算 cost_usd, 不重新实现
- Phase 8.23: 加 cost_by_day(since) — 按 UTC 日期聚合 USD, 给 dashboard
  trend chart; SQL DATE(timestamp) GROUP BY day ORDER BY day (无 records 返 {})

Phase 15.0 T2.8: 直接实例化已弃用, 请使用 infra.persistence.registry.get("cost") singleton.

v16.5 #N.3: Migrated to SqliteStorageAdapter from lingwen_storage.
Public API unchanged.
"""
from __future__ import annotations

import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional

from lingwen_llm.providers.cost_tracker import CostRecord
from lingwen_llm.providers.model_tiers import ModelTier, compute_cost
from lingwen_storage.sqlite_storage_adapter import SqliteStorageAdapter

# 默认 DB 路径: infra/.state/cost_tracker.db (gitignored)
_DB_PATH = Path(__file__).parent.parent / ".state" / "cost_tracker.db"


class CostTrackerDB:
    """SQLite 持久化 CostRecord (Phase 8.5)

    单表 cost_records (id PK, scenario, tier, input_tokens, output_tokens,
    cost_usd, timestamp). 镜像 ReadingPowerDB 模式 (sqlite3 + Row factory +
    _connect context manager + lazy _init_db).

    Phase 15.0 T2.8: 直接实例化已弃用, 请使用 infra.persistence.registry.get("cost") singleton.

    v16.5 #N.3: storage layer now SqliteStorageAdapter from lingwen_storage.
    Public API preserved.
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
            "Phase 15.0 T2.8: CostTrackerDB 直接实例化已弃用, "
            "请使用 infra.persistence.registry.get('cost') singleton. "
            "DB 路径统一在 infra/persistence/paths.py 定义.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._storage = SqliteStorageAdapter(str(self.db_path))
        if init_if_missing:
            self._ensure_db_path()

    def _ensure_db_path(self) -> None:
        """确保 DB 父目录存在 (mirror ReadingPowerDB)"""
        if str(self.db_path) != ":memory:" and not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def init_db(self) -> None:
        """初始化表 + 索引 (CREATE IF NOT EXISTS — 幂等)"""
        def _do(conn) -> None:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS cost_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scenario TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    cost_usd REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_cost_records_scenario
                    ON cost_records(scenario);
                CREATE INDEX IF NOT EXISTS idx_cost_records_tier
                    ON cost_records(tier);
                CREATE INDEX IF NOT EXISTS idx_cost_records_timestamp
                    ON cost_records(timestamp);
            """)
        self._storage.with_transaction(_do)

    def record(
        self,
        scenario: str,
        tier: ModelTier,
        input_tokens: int,
        output_tokens: int,
    ) -> CostRecord:
        """记录一次 LLM 调用 + 算 cost_usd → 返回 CostRecord

        调 compute_cost (model_tiers.py) 算 cost, 跟 in-memory CostTracker
        行为一致 — 同一份 (scenario, tier, in, out) → 同一份 CostRecord.
        """
        self.init_db()  # 懒初始化
        cost = compute_cost(input_tokens, output_tokens, tier)
        rec = CostRecord(
            scenario=scenario,
            tier=tier,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

        def _do(conn) -> None:
            conn.execute(
                """INSERT INTO cost_records
                   (scenario, tier, input_tokens, output_tokens, cost_usd, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    rec.scenario,
                    rec.tier.value,
                    rec.input_tokens,
                    rec.output_tokens,
                    rec.cost_usd,
                    rec.timestamp.isoformat(),
                ),
            )

        self._storage.with_transaction(_do)
        return rec

    def records(self) -> list[CostRecord]:
        """全部记录 (按 id 升序 = 时间顺序)"""
        self.init_db()

        def _do(conn):
            return conn.execute(
                """SELECT scenario, tier, input_tokens, output_tokens, cost_usd, timestamp
                   FROM cost_records ORDER BY id"""
            ).fetchall()

        rows = self._storage.with_connection(_do)
        return [
            CostRecord(
                scenario=r["scenario"],
                tier=ModelTier(r["tier"]),
                input_tokens=r["input_tokens"],
                output_tokens=r["output_tokens"],
                cost_usd=r["cost_usd"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
            )
            for r in rows
        ]

    def total_cost(self, since: Optional[datetime] = None) -> float:
        """总成本 (USD). Phase 8.16: since 透传 (additive, default None 走旧 SQL)."""
        self.init_db()

        def _do(conn):
            if since is None:
                return conn.execute(
                    "SELECT COALESCE(SUM(cost_usd), 0.0) as total FROM cost_records"
                ).fetchone()
            return conn.execute(
                "SELECT COALESCE(SUM(cost_usd), 0.0) as total "
                "FROM cost_records WHERE timestamp >= ?",
                (since.isoformat(),),
            ).fetchone()

        row = self._storage.with_connection(_do)
        return float(row["total"])

    def cost_by_scenario(self, since: Optional[datetime] = None) -> dict[str, float]:
        """按 scenario 聚合成本 (USD). Phase 8.16: since 透传 (additive)."""
        self.init_db()

        def _do(conn):
            if since is None:
                return conn.execute(
                    """SELECT scenario, SUM(cost_usd) as total
                       FROM cost_records GROUP BY scenario"""
                ).fetchall()
            return conn.execute(
                """SELECT scenario, SUM(cost_usd) as total
                   FROM cost_records WHERE timestamp >= ?
                   GROUP BY scenario""",
                (since.isoformat(),),
            ).fetchall()

        rows = self._storage.with_connection(_do)
        return {r["scenario"]: float(r["total"]) for r in rows}

    def cost_by_tier(self, since: Optional[datetime] = None) -> dict[ModelTier, float]:
        """按 tier 聚合成本 (USD). Phase 8.16: since 透传 (additive)."""
        self.init_db()

        def _do(conn):
            if since is None:
                return conn.execute(
                    """SELECT tier, SUM(cost_usd) as total
                       FROM cost_records GROUP BY tier"""
                ).fetchall()
            return conn.execute(
                """SELECT tier, SUM(cost_usd) as total
                   FROM cost_records WHERE timestamp >= ?
                   GROUP BY tier""",
                (since.isoformat(),),
            ).fetchall()

        rows = self._storage.with_connection(_do)
        return {ModelTier(r["tier"]): float(r["total"]) for r in rows}

    def cost_by_day(self, since: Optional[datetime] = None) -> dict[str, float]:
        """Phase 8.23: 按 UTC 日期 (YYYY-MM-DD) 聚合 cost_usd, 给 dashboard trend chart.
        跟 cost_by_scenario/tier 同 since 透传 (additive, default None 走旧 path).

        SQLite DATE(timestamp) 函数从 'YYYY-MM-DD HH:MM:SS' 字符串抽 date 部分
        (假设 UTC, 跟 cost_records 默认 CURRENT_TIMESTAMP 行为一致).
        ORDER BY day 保返回按日期升序 (跟 in-memory CostTracker.cost_by_day 行为对齐).

        Returns:
            dict[date_str, total_usd] — date_str 'YYYY-MM-DD', 按日期升序.
        """
        self.init_db()

        def _do(conn):
            if since is None:
                return conn.execute(
                    """SELECT DATE(timestamp) as day, SUM(cost_usd) as total
                       FROM cost_records GROUP BY day ORDER BY day"""
                ).fetchall()
            return conn.execute(
                """SELECT DATE(timestamp) as day, SUM(cost_usd) as total
                   FROM cost_records WHERE timestamp >= ?
                   GROUP BY day ORDER BY day""",
                (since.isoformat(),),
            ).fetchall()

        rows = self._storage.with_connection(_do)
        return {r["day"]: float(r["total"]) for r in rows}

    def cost_by_day_per_tier(
        self, since: Optional[datetime] = None
    ) -> dict[str, dict[str, float]]:
        """Phase 9.28 F12: cross-dim day × tier aggregation for per-tier trend chart.

        Returns nested dict: { 'YYYY-MM-DD': { 'haiku': usd, 'sonnet': usd, ... }, ... }
        ORDER BY day, tier (date keys ascending).
        """
        self.init_db()

        def _do(conn):
            if since is None:
                return conn.execute(
                    """SELECT DATE(timestamp) as day, tier, SUM(cost_usd) as total
                       FROM cost_records GROUP BY day, tier ORDER BY day, tier"""
                ).fetchall()
            return conn.execute(
                """SELECT DATE(timestamp) as day, tier, SUM(cost_usd) as total
                   FROM cost_records WHERE timestamp >= ?
                   GROUP BY day, tier ORDER BY day, tier""",
                (since.isoformat(),),
            ).fetchall()

        rows = self._storage.with_connection(_do)
        result: dict[str, dict[str, float]] = {}
        for row in rows:
            day = row["day"]
            tier = row["tier"]
            if day not in result:
                result[day] = {}
            result[day][tier] = float(row["total"])
        return result


__all__ = ["CostTrackerDB"]