"""Phase 15.0 T2.2: 共享 SQLite connection 工厂.

消除 8 个 storage 类的 `_get_connection` 7 个长一样的样板。
所有 connection 统一: `timeout=5.0` + `row_factory=sqlite3.Row`.

设计:
- 0 改 baseline: 既有的 `sqlite3.connect(str(path), timeout=5)` + Row factory
  仍兼容。
- 无副作用: 每次返回新 conn, caller 自己 commit/close。
- _connect() 上下文管理器: 包装 commit + close, 给愿意用的 caller。
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Union

DEFAULT_TIMEOUT = 5.0

PathLike = Union[str, Path]


def get_connection(db_path: PathLike, *, timeout: float = DEFAULT_TIMEOUT) -> sqlite3.Connection:
    """构造一个 SQLite connection (row_factory=Row, timeout=5).

    Args:
        db_path: db 路径 (str 或 Path), 支持 ':memory:'
        timeout: sqlite3.connect timeout, 默认 5.0s

    Returns:
        sqlite3.Connection (caller 负责 close)
    """
    conn = sqlite3.connect(str(db_path), timeout=timeout)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def _connect(db_path: PathLike, *, timeout: float = DEFAULT_TIMEOUT) -> Iterator[sqlite3.Connection]:
    """上下文管理器: 自动 commit + close.

    用法:
        with _connect("/tmp/x.db") as conn:
            conn.execute("CREATE TABLE ...")

    Raises:
        Exception: 透传 + 仍 close (caller 可放心重试).
    """
    conn = get_connection(db_path, timeout=timeout)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


__all__ = ["get_connection", "_connect", "DEFAULT_TIMEOUT", "PathLike"]
