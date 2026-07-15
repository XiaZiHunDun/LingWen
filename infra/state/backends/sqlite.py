"""
SQLite 状态后端

基于 SQLite 的状态存储实现

Phase 15.0 T2.8: DeprecationWarning — 引导 caller 切到
`infra.persistence.registry.get("workflow")` (singleton).
"""

import json
import sqlite3
import warnings
from pathlib import Path
from typing import Any, Optional

from .base import StateBackend


class SQLiteBackend(StateBackend):
    """
    SQLite 状态后端

    适用于生产环境，高并发场景
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
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        # 确保目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workflow_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def get(self, key: str) -> Optional[Any]:
        """获取指定键的值"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT value FROM workflow_state WHERE key = ?", (key,)
        ).fetchone()
        conn.close()

        if row is None:
            return None

        value_str = row["value"]
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

        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            INSERT OR REPLACE INTO workflow_state (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, value_str))
        conn.commit()
        conn.close()

    def delete(self, key: str) -> bool:
        """删除指定键"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute(
            "DELETE FROM workflow_state WHERE key = ?", (key,)
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def list_keys(self, prefix: Optional[str] = None) -> list[str]:
        """列出所有键"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row

        if prefix:
            rows = conn.execute(
                "SELECT key FROM workflow_state WHERE key LIKE ?",
                (f"{prefix}%",)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT key FROM workflow_state"
            ).fetchall()

        conn.close()
        return [row["key"] for row in rows]
