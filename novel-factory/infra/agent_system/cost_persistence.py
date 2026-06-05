"""Cost 持久化 — Phase 8.5

Doc 4 §11 Phase 8.5: SQLite 持久化 CostRecord 列表 (mirror ReadingPowerDB pattern).

设计:
- 单表 cost_records (id PK, scenario, tier, input_tokens, output_tokens,
  cost_usd, timestamp) + 2 索引 (scenario, tier)
- 复用 CostRecord frozen dataclass (in-memory CostTracker 一致)
- 路径: infra/.state/cost_tracker.db (gitignored, 跟 reading_power.db 错开)
- 初始化: lazy _init_db (调 record/records/cost_*_methods 时触发)
- 复用 compute_cost (model_tiers.py) 算 cost_usd, 不重新实现
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from infra.ai_service.cost_tracker import CostRecord
from infra.ai_service.model_tiers import ModelTier, compute_cost

# 默认 DB 路径: infra/.state/cost_tracker.db (gitignored)
_DB_PATH = Path(__file__).parent.parent / ".state" / "cost_tracker.db"


class CostTrackerDB:
    """SQLite 持久化 CostRecord (Phase 8.5)

    单表 cost_records (id PK, scenario, tier, input_tokens, output_tokens,
    cost_usd, timestamp). 镜像 ReadingPowerDB 模式 (sqlite3 + Row factory +
    _connect context manager + lazy _init_db).
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
        """确保 DB 父目录存在 (mirror ReadingPowerDB)"""
        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """DB 连接 context manager (mirror ReadingPowerDB)"""
        conn = sqlite3.connect(str(self.db_path), timeout=5)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self) -> None:
        """初始化表 + 索引 (CREATE IF NOT EXISTS — 幂等)"""
        with self._connect() as conn:
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
            """)

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
        with self._connect() as conn:
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
        return rec

    def records(self) -> list[CostRecord]:
        """全部记录 (按 id 升序 = 时间顺序)"""
        self.init_db()
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT scenario, tier, input_tokens, output_tokens, cost_usd, timestamp
                   FROM cost_records ORDER BY id"""
            ).fetchall()
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

    def total_cost(self) -> float:
        """总成本 (USD)"""
        self.init_db()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(cost_usd), 0.0) as total FROM cost_records"
            ).fetchone()
        return float(row["total"])

    def cost_by_scenario(self) -> dict[str, float]:
        """按 scenario 聚合成本 (USD)"""
        self.init_db()
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT scenario, SUM(cost_usd) as total
                   FROM cost_records GROUP BY scenario"""
            ).fetchall()
        return {r["scenario"]: float(r["total"]) for r in rows}

    def cost_by_tier(self) -> dict[ModelTier, float]:
        """按 tier 聚合成本 (USD)"""
        self.init_db()
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT tier, SUM(cost_usd) as total
                   FROM cost_records GROUP BY tier"""
            ).fetchall()
        return {ModelTier(r["tier"]): float(r["total"]) for r in rows}


__all__ = ["CostTrackerDB"]
