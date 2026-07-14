"""统一 SQLite PRAGMA 配置

Phase 15.0 P3-E8: 收敛3套SQLite包装的PRAGMA设置，确保一致性。

默认配置：
- journal_mode=WAL: 支持并发读写
- synchronous=FULL: 完整同步，保证数据安全
- foreign_keys=ON: 启用外键约束
- busy_timeout=5000: 5秒超时重试

使用方式：
    from infra.persistence.sqlite_config import apply_sqlite_pragmas

    conn = sqlite3.connect(db_path)
    apply_sqlite_pragmas(conn)
"""
import sqlite3


DEFAULT_PRAGMAS = {
    "journal_mode": "WAL",
    "synchronous": "FULL",
    "foreign_keys": "ON",
    "busy_timeout": "5000",
}


def apply_sqlite_pragmas(conn: sqlite3.Connection, pragmas: dict = None) -> None:
    """应用 SQLite PRAGMA 设置

    Args:
        conn: SQLite 连接对象
        pragmas: 自定义 PRAGMA 配置，默认为 DEFAULT_PRAGMAS
    """
    if pragmas is None:
        pragmas = DEFAULT_PRAGMAS
    for key, value in pragmas.items():
        conn.execute(f"PRAGMA {key}={value}")


def get_pragma_value(conn: sqlite3.Connection, pragma_name: str) -> str:
    """获取当前 PRAGMA 值

    Args:
        conn: SQLite 连接对象
        pragma_name: PRAGMA 名称

    Returns:
        PRAGMA 值
    """
    result = conn.execute(f"PRAGMA {pragma_name}").fetchone()
    return result[0] if result else ""


def verify_pragmas(conn: sqlite3.Connection) -> dict:
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