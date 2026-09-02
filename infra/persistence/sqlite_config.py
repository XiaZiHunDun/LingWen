"""统一 SQLite PRAGMA 配置

Phase 15.0 P3-E8: 收敛3套SQLite包装的PRAGMA设置，确保一致性。

默认配置：
- journal_mode=WAL: 支持并发读写
- synchronous=FULL: 完整同步，保证数据安全
- foreign_keys=ON: 启用外键约束
- busy_timeout=5000: 5秒超时重试

使用方式：
    from infra.persistence.sqlite_config import apply_sqlite_pragmas

    conn = SqliteStorageAdapter(db_path)._open()  # via connection helper
    apply_sqlite_pragmas(conn)

v16.5 #N.4: drop direct ``import sqlite3``. The connection parameter is
typed as ``ConnectionPort``; ``conn.execute(...)`` works on the
``SqliteConnection`` wrapper because ``__getattr__`` delegates to the
underlying ``sqlite3.Connection``.
"""

from __future__ import annotations

from lingwen_shared.ports.storage import ConnectionPort

DEFAULT_PRAGMAS = {
    "journal_mode": "WAL",
    "synchronous": "FULL",
    "foreign_keys": "ON",
    "busy_timeout": "5000",
}


def apply_sqlite_pragmas(conn: ConnectionPort, pragmas: dict | None = None) -> None:
    """应用 SQLite PRAGMA 设置

    Args:
        conn: SQLite 连接对象（实现 ``ConnectionPort``）
        pragmas: 自定义 PRAGMA 配置，默认为 DEFAULT_PRAGMAS
    """
    if pragmas is None:
        pragmas = DEFAULT_PRAGMAS
    for key, value in pragmas.items():
        conn.execute(f"PRAGMA {key}={value}")


def get_pragma_value(conn: ConnectionPort, pragma_name: str) -> str:
    """获取当前 PRAGMA 值

    Args:
        conn: SQLite 连接对象
        pragma_name: PRAGMA 名称

    Returns:
        PRAGMA 值
    """
    result = conn.execute(f"PRAGMA {pragma_name}").fetchone()
    return result[0] if result else ""


def verify_pragmas(conn: ConnectionPort) -> dict:
    """验证所有默认 PRAGMA 是否已正确设置

    Args:
        conn: SQLite 连接对象

    Returns:
        包含每个 PRAGMA 名称、期望值和实际值的字典
    """
    result = {}
    for pragma_name, expected in DEFAULT_PRAGMAS.items():
        actual = get_pragma_value(conn, pragma_name)
        result[pragma_name] = {
            "expected": expected,
            "actual": str(actual),
            "matched": str(actual) == expected,
        }
    return result
