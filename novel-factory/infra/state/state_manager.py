#!/usr/bin/env python3
"""
SQLite State Manager - replaces workflow_state.json
Provides atomic state operations with transaction support
"""
import fcntl
import json
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional


class StateManager:
    """SQLite-based workflow state manager with atomic operations"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / '.state' / 'workflow.db'

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_path = self.db_path.with_suffix('.lock')
        self._init_db()

    def _init_db(self):
        """Initialize database with schema"""
        schema_path = Path(__file__).parent / 'schema.sql'
        with open(schema_path) as f:
            schema = f.read()

        conn = sqlite3.connect(str(self.db_path))
        conn.executescript(schema)
        conn.close()

    @contextmanager
    def _get_conn(self):
        """Get connection with row factory"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def _transaction(self):
        """Exclusive transaction with flock protection"""
        # Acquire file lock first
        lock_file = open(self._lock_path, 'w')
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()

    def get_current_step(self) -> dict:
        """Get current workflow step and phase"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT key, value FROM workflow_state WHERE key IN ('current_step', 'current_phase', 'version')"
            ).fetchall()
            result = {}
            for row in rows:
                result[row['key']] = row['value']
            if result:
                return {
                    'current_step': result.get('current_step', 'STEP_00'),
                    'phase': result.get('current_phase', 'PHASE_0_INIT'),
                    'version': result.get('version', 'v8.2')
                }
            return {'current_step': 'STEP_00', 'phase': 'PHASE_0_INIT', 'version': 'v8.2'}

    def advance_step(self, step: str, phase: Optional[str] = None) -> dict:
        """Atomically advance to a new step"""
        with self._transaction() as conn:
            old = self.get_current_step()

            if phase is None:
                phase = old.get('phase', 'PHASE_UNKNOWN')

            conn.execute("""
                INSERT OR REPLACE INTO workflow_state (key, value, updated_at)
                VALUES ('current_step', ?, CURRENT_TIMESTAMP)
            """, (step,))
            if phase:
                conn.execute("""
                    INSERT OR REPLACE INTO workflow_state (key, value, updated_at)
                    VALUES ('current_phase', ?, CURRENT_TIMESTAMP)
                """, (phase,))

            conn.execute("""
                INSERT INTO audit_log (action, old_value, new_value, changed_by)
                VALUES (?, ?, ?, 'StateManager')
            """, ('advance_step', json.dumps(old), json.dumps({'step': step, 'phase': phase})))

            return {'old': old, 'new': {'current_step': step, 'phase': phase}}

    def record_task(self, task_id: str, agent: str, status: str,
                   task_name: Optional[str] = None) -> dict:
        """Record a new task or update existing task status"""
        with self._transaction() as conn:
            existing = conn.execute(
                "SELECT id FROM task WHERE id = ?", (task_id,)
            ).fetchone()

            if existing:
                old_status = conn.execute(
                    "SELECT status FROM task WHERE id = ?", (task_id,)
                ).fetchone()
                old_status = old_status['status'] if old_status else None

                conn.execute("""
                    UPDATE task SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
                """, (status, task_id))

                conn.execute("""
                    INSERT INTO audit_log (task_id, action, result, old_value, new_value, changed_by)
                    VALUES (?, 'update_task', ?, ?, ?, 'StateManager')
                """, (task_id, status,
                      json.dumps({'status': old_status}),
                      json.dumps({'status': status})))
            else:
                conn.execute("""
                    INSERT INTO task (id, task_name, agent, status)
                    VALUES (?, ?, ?, ?)
                """, (task_id, task_name or task_id, agent, status))

                conn.execute("""
                    INSERT INTO audit_log (task_id, action, result, new_value, changed_by)
                    VALUES (?, 'create_task', ?, ?, 'StateManager')
                """, (task_id, status, json.dumps({'task_id': task_id, 'agent': agent, 'status': status})))

            return {'task_id': task_id, 'agent': agent, 'status': status}

    def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get task status by ID"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM task WHERE id = ?", (task_id,)
            ).fetchone()
            if row:
                return dict(row)
            return None

    def get_all_tasks(self, status: Optional[str] = None) -> list[dict]:
        """Get all tasks, optionally filtered by status"""
        with self._get_conn() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM task WHERE status = ? ORDER BY created_at",
                    (status,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM task ORDER BY created_at"
                ).fetchall()
            return [dict(row) for row in rows]

    def get_audit_log(self, task_id: Optional[str] = None, limit: int = 100) -> list[dict]:
        """Get audit log entries"""
        with self._get_conn() as conn:
            if task_id:
                rows = conn.execute(
                    "SELECT * FROM audit_log WHERE task_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (task_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [dict(row) for row in rows]
