#!/usr/bin/env python3
"""
SQLite-based workflow state management
Provides atomic read-modify-write operations
"""
import fcntl
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class WorkflowDB:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / '.state' / 'workflow.db'

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # R3-001: 与 state_manager.py 一致,使用 fcntl.flock 防止多进程写竞争
        self._lock_path = self.db_path.with_suffix('.lock')
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_state (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_tasks (
                    task_id TEXT PRIMARY KEY,
                    task_name TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    heartbeat_at TEXT,
                    task_id_external TEXT,
                    dispatched_at TEXT,
                    error_msg TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT,
                    record_id TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    changed_by TEXT
                )
            """)
            # WAL 模式：让多 reader + 1 writer 并发不互相阻塞
            conn.execute("PRAGMA journal_mode=WAL")
            # 5s busy timeout：写冲突时自动等待而不是直接抛 SQLITE_BUSY
            conn.execute("PRAGMA busy_timeout=5000")

    @contextmanager
    def _get_conn(self):
        """Get database connection with context manager"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        # 每个连接也设置 busy_timeout（PRAGMA 是 per-connection）
        conn.execute("PRAGMA busy_timeout=5000")
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self):
        """Atomic transaction with fcntl.flock 跨进程互斥 (R3-001)

        与 infra/state/state_manager.py 的 _transaction 保持一致,
        通过 fcntl.flock 防止多进程同时写 SQLite 时的竞争条件。
        配合 BEGIN IMMEDIATE 提供 SQLite 进程内写锁,
        busy_timeout=5000 避免短冲突直接抛 SQLITE_BUSY。
        """
        lock_file = open(self._lock_path, 'w')
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except Exception:
            if conn is not None:
                conn.rollback()
            raise
        finally:
            if conn is not None:
                conn.close()
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()

    def get(self, key: str) -> Optional[dict]:
        """Get a value by key"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT value FROM workflow_state WHERE key = ?", (key,)
            ).fetchone()
            if row and row['value']:
                return json.loads(row['value'])
            return None

    def set(self, key: str, value: dict):
        """Atomically set a value"""
        with self.transaction() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO workflow_state (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, json.dumps(value, ensure_ascii=False)))

    def get_task(self, task_id: str) -> Optional[dict]:
        """Get agent task by ID"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM agent_tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            if row:
                return dict(row)
            return None

    def update_task(self, task_id: str, updates: dict):
        """Atomically update task fields"""
        with self.transaction() as conn:
            for key, value in updates.items():
                if key == 'heartbeat_at':
                    conn.execute(
                        "UPDATE agent_tasks SET heartbeat_at = ? WHERE task_id = ?",
                        (value, task_id)
                    )
                elif key == 'status':
                    conn.execute(
                        "UPDATE agent_tasks SET status = ? WHERE task_id = ?",
                        (value, task_id)
                    )

    def create_task(self, task_id: str, task_name: str, agent: str):
        """Create a new agent task"""
        with self.transaction() as conn:
            conn.execute("""
                INSERT INTO agent_tasks (task_id, task_name, agent, status, dispatched_at, heartbeat_at)
                VALUES (?, ?, ?, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (task_id, task_name, agent))

    def record_history(self, table: str, record_id: str, old: dict, new: dict):
        """Record state change to history"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO state_history (table_name, record_id, old_value, new_value, changed_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (table, record_id, json.dumps(old), json.dumps(new)))

    def get_all_tasks(self) -> list[dict]:
        """Get all agent tasks"""
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM agent_tasks ORDER BY created_at").fetchall()
            return [dict(row) for row in rows]

    def get_stale_tasks(self, threshold_minutes: int = 30) -> list[dict]:
        """Get tasks that haven't sent heartbeat within threshold"""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM agent_tasks
                WHERE status = 'running'
                AND datetime(heartbeat_at) < datetime('now', '-' || ? || ' minutes')
            """, (threshold_minutes,)).fetchall()
            return [dict(row) for row in rows]
