"""Phase 15.0 T2.3: schemas.py 6 tests.

覆盖 6 个 schema 都能 apply_schema 成功 + unknown 抛 KeyError.
"""
from __future__ import annotations

import pytest

from infra.persistence.connection import get_connection
from infra.persistence.schemas import SCHEMAS, apply_schema, registered_schema_names


def _table_list(conn):
    """返回当前 db 的 table name 集合 (排除 sqlite_internal)."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {r["name"] for r in rows}


class TestApplySchema:
    @pytest.mark.parametrize(
        "name", ["ripple", "cost", "budget", "reading", "workflow", "relationship"]
    )
    def test_apply_schema_creates_tables(self, name):
        conn = get_connection(":memory:")
        try:
            apply_schema(name, conn)
            tables = _table_list(conn)
            # 至少要有一个 table (RIPPLE_SCHEMA 多表, 其他 1 个)
            assert len(tables) >= 1
            # DDL 用 IF NOT EXISTS, 重复 apply 不报错
            apply_schema(name, conn)
            tables2 = _table_list(conn)
            assert tables == tables2
        finally:
            conn.close()

    def test_apply_schema_ripple_creates_expected_tables(self):
        """ripple 应该有 ripple_impact_scores + ripples 表."""
        conn = get_connection(":memory:")
        try:
            apply_schema("ripple", conn)
            tables = _table_list(conn)
            assert "ripple_impact_scores" in tables
            assert "ripples" in tables
        finally:
            conn.close()

    def test_apply_schema_reading_creates_expected_tables(self):
        """reading 应该有 hooks + coolpoints 表."""
        conn = get_connection(":memory:")
        try:
            apply_schema("reading", conn)
            tables = _table_list(conn)
            assert "hooks" in tables
            assert "coolpoints" in tables
        finally:
            conn.close()

    def test_apply_schema_unknown_raises(self):
        conn = get_connection(":memory:")
        try:
            with pytest.raises(KeyError) as exc_info:
                apply_schema("unknown_schema", conn)
            assert "unknown_schema" in str(exc_info.value)
        finally:
            conn.close()

    def test_registered_schema_names(self):
        names = registered_schema_names()
        assert "ripple" in names
        assert "cost" in names
        assert "budget" in names
        assert "reading" in names
        assert "workflow" in names
        assert "relationship" in names
        assert names == sorted(names)  # 按字母排序

    def test_schemas_dict_contains_all_six(self):
        assert len(SCHEMAS) >= 6
        for required in ("ripple", "cost", "budget", "reading", "workflow", "relationship"):
            assert required in SCHEMAS
            assert isinstance(SCHEMAS[required], list)
            assert len(SCHEMAS[required]) >= 1
            assert all(isinstance(ddl, str) for ddl in SCHEMAS[required])
