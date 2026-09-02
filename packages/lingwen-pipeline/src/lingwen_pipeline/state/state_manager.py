#!/usr/bin/env python3
"""
SQLite State Manager - replaces workflow_state.json
Provides atomic state operations with transaction support

Phase 15.0 T2.8: DeprecationWarning — 推荐切到 infra.persistence.registry.get("workflow").

v16.5 #N.3: Migrated to SqliteStorageAdapter from lingwen_storage.
Public API preserved (StateManager(db_path=...), _get_conn(), _transaction(),
get_current_step(), advance_step(), record_task(), get_task_status(),
get_all_tasks(), get_audit_log()).
"""

import fcntl
import json
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from lingwen_storage.sqlite_storage_adapter import SqliteStorageAdapter


class StateManager:
    """SQLite-based workflow state manager with atomic operations

    v16.5 #N.3: storage layer now SqliteStorageAdapter from lingwen_storage
    (previously direct sqlite3). fcntl.flock retained around transaction to
    preserve R3-001 cross-process write serialization semantics.
    """

    def __init__(self, db_path: Optional[str] = None):
        warnings.warn(
            "Phase 15.0 T2.8: StateManager 已弃用, 推荐使用 "
            "infra.persistence.registry.get('workflow') singleton.",
            DeprecationWarning,
            stacklevel=2,
        )
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / ".state" / "workflow.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_path = self.db_path.with_suffix(".lock")
        self._storage = SqliteStorageAdapter(str(self.db_path))
        self._init_db()

    def _init_db(self):
        """Initialize database with schema"""
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path) as f:
            schema = f.read()

        def _do(conn) -> None:
            conn.executescript(schema)

        self._storage.with_transaction(_do)

    @contextmanager
    def _get_conn(self):
        """Get connection with row factory (delegated to SqliteStorageAdapter)."""
        with self._storage._connection_cm() as conn:
            yield conn

    @contextmanager
    def _transaction(self):
        """Exclusive transaction with flock protection.

        v16.5 #N.3: connection lifecycle delegated to SqliteStorageAdapter
        via private _transaction_cm. fcntl.flock retained for cross-process
        serialization (R3-001) — SqliteStorageAdapter handles in-process
        BEGIN/COMMIT/ROLLBACK.
        """
        # Acquire file lock first
        lock_file = open(self._lock_path, "w")
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            with self._storage._transaction_cm() as conn:
                yield conn
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()

    def _fetch_current_step_from_conn(self, conn) -> dict:
        """Read workflow step keys from an open connection (must be under flock)."""
        rows = conn.execute(
            "SELECT key, value FROM workflow_state WHERE key IN ('current_step', 'current_phase', 'version')"
        ).fetchall()
        result = {row["key"]: row["value"] for row in rows}
        return {
            "current_step": result.get("current_step", "STEP_00"),
            "phase": result.get("current_phase", "PHASE_0_INIT"),
            "version": result.get("version", "v8.2"),
        }

    def get_current_step(self) -> dict:
        """Get current workflow step and phase"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT key, value FROM workflow_state WHERE key IN ('current_step', 'current_phase', 'version')"
            ).fetchall()
            result = {}
            for row in rows:
                result[row["key"]] = row["value"]
            if result:
                return {
                    "current_step": result.get("current_step", "STEP_00"),
                    "phase": result.get("current_phase", "PHASE_0_INIT"),
                    "version": result.get("version", "v8.2"),
                }
            return {"current_step": "STEP_00", "phase": "PHASE_0_INIT", "version": "v8.2"}

    def advance_step(self, step: str, phase: Optional[str] = None) -> dict:
        """Atomically advance to a new step"""
        with self._transaction() as conn:
            old = self._fetch_current_step_from_conn(conn)

            if phase is None:
                phase = old.get("phase", "PHASE_UNKNOWN")

            conn.execute(
                """
                INSERT OR REPLACE INTO workflow_state (key, value, updated_at)
                VALUES ('current_step', ?, CURRENT_TIMESTAMP)
            """,
                (step,),
            )
            if phase:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO workflow_state (key, value, updated_at)
                    VALUES ('current_phase', ?, CURRENT_TIMESTAMP)
                """,
                    (phase,),
                )

            conn.execute(
                """
                INSERT INTO audit_log (action, old_value, new_value, changed_by)
                VALUES (?, ?, ?, 'StateManager')
            """,
                ("advance_step", json.dumps(old), json.dumps({"step": step, "phase": phase})),
            )

            return {"old": old, "new": {"current_step": step, "phase": phase}}

    def record_task(self, task_id: str, agent: str, status: str, task_name: Optional[str] = None) -> dict:
        """Record a new task or update existing task status"""
        with self._transaction() as conn:
            existing = conn.execute("SELECT id FROM task WHERE id = ?", (task_id,)).fetchone()

            if existing:
                old_status = conn.execute("SELECT status FROM task WHERE id = ?", (task_id,)).fetchone()
                old_status = old_status["status"] if old_status else None

                conn.execute(
                    """
                    UPDATE task SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
                """,
                    (status, task_id),
                )

                conn.execute(
                    """
                    INSERT INTO audit_log (task_id, action, result, old_value, new_value, changed_by)
                    VALUES (?, 'update_task', ?, ?, ?, 'StateManager')
                """,
                    (task_id, status, json.dumps({"status": old_status}), json.dumps({"status": status})),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO task (id, task_name, agent, status)
                    VALUES (?, ?, ?, ?)
                """,
                    (task_id, task_name or task_id, agent, status),
                )

                conn.execute(
                    """
                    INSERT INTO audit_log (task_id, action, result, new_value, changed_by)
                    VALUES (?, 'create_task', ?, ?, 'StateManager')
                """,
                    (task_id, status, json.dumps({"task_id": task_id, "agent": agent, "status": status})),
                )

            return {"task_id": task_id, "agent": agent, "status": status}

    def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get task status by ID"""
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM task WHERE id = ?", (task_id,)).fetchone()
            if row:
                return dict(row)
            return None

    def get_all_tasks(self, status: Optional[str] = None) -> list[dict]:
        """Get all tasks, optionally filtered by status"""
        with self._get_conn() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM task WHERE status = ? ORDER BY created_at", (status,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM task ORDER BY created_at").fetchall()
            return [dict(row) for row in rows]

    def get_audit_log(self, task_id: Optional[str] = None, limit: int = 100) -> list[dict]:
        """Get audit log entries"""
        with self._get_conn() as conn:
            if task_id:
                rows = conn.execute(
                    "SELECT * FROM audit_log WHERE task_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (task_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,)
                ).fetchall()
            return [dict(row) for row in rows]
