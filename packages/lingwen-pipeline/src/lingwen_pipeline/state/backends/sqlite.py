"""
SQLite 状态后端

基于 SQLite 的状态存储实现

Phase 15.0 T2.8: DeprecationWarning — 引导 caller 切到
`infra.persistence.registry.get("workflow")` (singleton).

v16.5 #N.3: Migrated to SqliteStorageAdapter from lingwen_storage.
Public API unchanged (SQLiteBackend(db_path=...) + get/set/delete/list_keys).
"""

import json
import warnings
from pathlib import Path
from typing import Any, Optional

from lingwen_storage.sqlite_storage_adapter import SqliteStorageAdapter

from .base import StateBackend


class SQLiteBackend(StateBackend):
    """
    SQLite 状态后端

    适用于生产环境，高并发场景

    v16.5 #N.3: storage layer now SqliteStorageAdapter from lingwen_storage
    (previously direct sqlite3). Public API preserved.
    """

    def __init__(self, db_path: str = ".state/workflow.db"):
        """
        初始化 SQLite 后端

        Args:
            db_path: 数据库路径（相对于项目根目录）
        """
        warnings.warn(
            "Phase 15.0 T2.8: SQLiteBackend 已弃用, 请使用 "
            "infra.persistence.registry.get('workflow') singleton. "
            "DB 路径统一在 infra/persistence/paths.py 定义.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.db_path = Path(db_path)
        self._storage = SqliteStorageAdapter(str(self.db_path))
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        # 确保目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        def _do(conn) -> None:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_state (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        self._storage.with_transaction(_do)

    def get(self, key: str) -> Optional[Any]:
        """获取指定键的值"""
        def _do(conn):
            row = conn.execute(
                "SELECT value FROM workflow_state WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row is not None else None

        value_str = self._storage.with_connection(_do)

        if value_str is None:
            return None

        try:
            return json.loads(value_str)
        except json.JSONDecodeError:
            return value_str

    def set(self, key: str, value: Any) -> None:
        """设置指定键的值"""
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, ensure_ascii=False)
        elif isinstance(value, str):
            value_str = value
        else:
            value_str = str(value)

        def _do(conn) -> None:
            conn.execute("""
                INSERT OR REPLACE INTO workflow_state (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value_str))

        self._storage.with_transaction(_do)

    def delete(self, key: str) -> bool:
        """删除指定键"""
        def _do(conn) -> int:
            cursor = conn.execute(
                "DELETE FROM workflow_state WHERE key = ?", (key,)
            )
            return cursor.rowcount

        deleted_count = self._storage.with_transaction(_do)
        return deleted_count > 0

    def list_keys(self, prefix: Optional[str] = None) -> list[str]:
        """列出所有键"""
        def _do(conn):
            if prefix:
                return conn.execute(
                    "SELECT key FROM workflow_state WHERE key LIKE ?",
                    (f"{prefix}%",)
                ).fetchall()
            return conn.execute(
                "SELECT key FROM workflow_state"
            ).fetchall()

        rows = self._storage.with_connection(_do)
        return [row["key"] for row in rows]
