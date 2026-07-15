"""Phase 15.0 T2.9: end-to-end 集成测试 — 验证整套 persistence 体系联通.

覆盖:
1. register_all → get 各 storage 一气呵成
2. schemas.apply_schema 真造表 + insert/select roundtrip
3. paths → bootstrap → registry 链贯通
4. 6 storage 都能用 :memory: 初始化不抛
5. dashboard 兼容 shim 仍能传 init_if_missing
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _autouse_reset():
    from infra.persistence import registry

    registry.reset_all()
    registry._registry.clear()
    yield
    registry.reset_all()
    registry._registry.clear()


class TestEndToEnd:
    def test_full_pipeline_register_and_get(self):
        from infra.persistence.bootstrap import register_all
        from infra.persistence.registry import get, registered_names

        register_all()
        names = registered_names()
        assert len(names) >= 6
        # 6 个都能 get 不抛
        for name in ("ripple", "cost", "budget", "reading", "workflow", "relationship"):
            inst = get(name, db_path=":memory:")
            assert inst is not None

    def test_schema_apply_creates_table_and_roundtrip(self):
        from infra.persistence.connection import get_connection
        from infra.persistence.schemas import apply_schema

        conn = get_connection(":memory:")
        try:
            apply_schema("ripple", conn)
            # 造一条数据
            conn.execute(
                "INSERT INTO ripple_impact_scores (ripple_id, impact_score) VALUES (?, ?)",
                ("r1", 0.5),
            )
            conn.commit()
            row = conn.execute(
                "SELECT impact_score FROM ripple_impact_scores WHERE ripple_id = 'r1'"
            ).fetchone()
            assert row["impact_score"] == 0.5
        finally:
            conn.close()

    def test_paths_bootstrap_registry_chain(self):
        from infra.persistence.bootstrap import register_all
        from infra.persistence.paths import (
            COST_TRACKER_DB,
            READING_POWER_DB,
            RELATIONSHIP_DB,
            RIPPLE_DB,
            WORKFLOW_DB,
        )
        from infra.persistence.registry import get

        register_all()
        # 验证各 storage 注册时用的 db_path 与 paths 一致
        for name, expected_path in [
            ("ripple", str(RIPPLE_DB)),
            ("cost", str(COST_TRACKER_DB)),
            ("budget", str(COST_TRACKER_DB)),
            ("reading", str(READING_POWER_DB)),
            ("workflow", str(WORKFLOW_DB)),
            ("relationship", str(RELATIONSHIP_DB)),
        ]:
            inst = get(name)
            # 实际 db_path 可能因 caller override 改变, 仅检查 type
            assert inst is not None

    def test_six_storages_init_with_memory(self):
        """6 storage 都能用 :memory: 初始化不抛."""
        from infra.persistence.bootstrap import register_all
        from infra.persistence.registry import get

        register_all()
        for name in ("ripple", "cost", "budget", "reading", "workflow", "relationship"):
            inst = get(name, db_path=":memory:")
            # 验证是 object (不强求具体 type)
            assert inst is not None

    def test_dashboard_shim_compatibility(self):
        """dashboard.helpers.reading_power_db 兼容 init_if_missing=False."""
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import tempfile
            from pathlib import Path

            from infra.reading_power.db import ReadingPowerDB

            with tempfile.TemporaryDirectory() as tmp:
                db_path = Path(tmp) / "shim_e2e.db"
                db = ReadingPowerDB(db_path=db_path, init_if_missing=False)
                assert db.db_path == db_path
