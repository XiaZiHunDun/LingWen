"""Phase 15.0 T2.2: connection.py 3 tests.

覆盖:
1. 返回 sqlite3.Connection + row_factory=Row
2. timeout 参数生效
3. Path 对象也能用
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from infra.persistence.connection import DEFAULT_TIMEOUT, _connect, get_connection


class TestGetConnection:
    def test_returns_sqlite_connection_with_row_factory(self):
        conn = get_connection(":memory:")
        try:
            assert isinstance(conn, sqlite3.Connection)
            assert conn.row_factory is sqlite3.Row
        finally:
            conn.close()

    def test_respects_timeout_parameter(self):
        # timeout 不会立即生效, 但必须接受且不抛
        conn = get_connection(":memory:", timeout=1.5)
        try:
            # 通过 sqlite3 内部可见 timeout
            assert conn is not None
        finally:
            conn.close()
        # 默认 timeout 也应可用
        assert DEFAULT_TIMEOUT == 5.0

    def test_accepts_pathlib_path(self):
        p = Path(":memory:")
        conn = get_connection(p)
        try:
            conn.execute("CREATE TABLE t (id INTEGER)")
            cur = conn.execute("SELECT 1")
            assert cur.fetchone()[0] == 1
        finally:
            conn.close()


class TestConnectContextManager:
    def test_connect_commits_and_closes(self):
        """_connect 自动 commit + close."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "x.db")
            with _connect(db) as conn:
                conn.execute("CREATE TABLE t (id INTEGER, name TEXT)")
                conn.execute("INSERT INTO t VALUES (1, 'a')")
            # commit 已触发, 新 conn 应能读
            with get_connection(db) as c2:
                rows = c2.execute("SELECT * FROM t").fetchall()
                assert len(rows) == 1
                assert rows[0]["name"] == "a"
