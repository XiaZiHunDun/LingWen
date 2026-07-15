"""断点续跑 - 创建/列出/恢复/删除

通过快照整个 workflow_state + agent_tasks 实现回滚
"""
import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple

from . import db, state

logger = logging.getLogger(__name__)


def create_checkpoint(note: str = "") -> str:
    """创建断点快照

    Args:
        note: 断点说明

    Returns:
        checkpoint_id
    """
    db.init_sqlite()

    # 获取锁以确保读取一致快照
    if not db._acquire_lock():
        logger.warning("无法获取锁，快照可能不一致")
        return ""

    try:
        checkpoint_id = datetime.now().strftime("cp_%Y%m%d_%H%M%S")

        phase = state.get_state("current_phase", "N/A")
        step = state.get_state("current_step", "N/A")

        # 获取完整状态快照（在单一事务内）
        conn = sqlite3.connect(str(db.DB_PATH), timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("BEGIN IMMEDIATE")
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute("SELECT * FROM workflow_state")
            state_data = [dict(row) for row in cur.fetchall()]

            cur = conn.execute("SELECT * FROM agent_tasks ORDER BY created_at DESC")
            task_data = [dict(row) for row in cur.fetchall()]

            snapshot = {
                "phase": phase,
                "step": step,
                "state": state_data,
                "tasks": task_data,
                "workflow_file": str(db.WORKFLOW_FILE)
            }

            conn.execute("""
                INSERT INTO checkpoints (checkpoint_id, phase, step, snapshot, note)
                VALUES (?, ?, ?, ?, ?)
            """, (checkpoint_id, phase, step, json.dumps(snapshot, ensure_ascii=False), note))
            conn.commit()
        finally:
            conn.close()

        return checkpoint_id
    finally:
        db._release_lock()


def list_checkpoints() -> List[Dict]:
    """列出所有断点

    Returns:
        断点列表
    """
    db.init_sqlite()

    conn = sqlite3.connect(str(db.DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            "SELECT checkpoint_id, phase, step, note, created_at FROM checkpoints ORDER BY created_at DESC"
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def restore_checkpoint(checkpoint_id: str) -> Tuple[bool, str]:
    """从断点恢复

    Args:
        checkpoint_id: 断点ID

    Returns:
        (成功标志, 消息)
    """
    db.init_sqlite()

    # 获取锁以确保恢复操作原子性
    if not db._acquire_lock():
        return False, "无法获取锁，另一个进程正在恢复"

    try:
        # 先读取快照
        conn = sqlite3.connect(str(db.DB_PATH))
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute(
                "SELECT snapshot FROM checkpoints WHERE checkpoint_id = ?",
                (checkpoint_id,)
            )
            row = cur.fetchone()
            if not row:
                return False, f"Checkpoint not found: {checkpoint_id}"

            snapshot = json.loads(row['snapshot'])
        finally:
            conn.close()

        # 然后执行恢复（在锁内）
        conn = sqlite3.connect(str(db.DB_PATH))
        conn.execute("BEGIN IMMEDIATE")
        try:
            # 清空现有状态
            conn.execute("DELETE FROM workflow_state")
            conn.execute("DELETE FROM agent_tasks")

            # 恢复状态数据
            for item in snapshot.get("state", []):
                conn.execute("""
                    INSERT INTO workflow_state (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (item['key'], item['value']))

            # 恢复任务数据
            for task in snapshot.get("tasks", []):
                conn.execute("""
                    INSERT INTO agent_tasks
                    (task_id, task_name, agent, status, heartbeat_at, task_id_external, dispatched_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task['task_id'],
                    task['task_name'],
                    task.get('agent', ''),
                    task.get('status', 'pending'),
                    task.get('heartbeat_at'),
                    task.get('task_id_external'),
                    task.get('dispatched_at'),
                    task.get('created_at', datetime.now().isoformat())
                ))

            conn.commit()
            return True, f"Restored checkpoint {checkpoint_id}"
        except Exception as e:
            conn.rollback()
            return False, f"Restore failed: {e}"
        finally:
            conn.close()
    finally:
        db._release_lock()


def delete_checkpoint(checkpoint_id: str) -> bool:
    """删除断点

    Args:
        checkpoint_id: 断点ID

    Returns:
        True成功
    """
    db.init_sqlite()

    conn = sqlite3.connect(str(db.DB_PATH))
    try:
        conn.execute("DELETE FROM checkpoints WHERE checkpoint_id = ?", (checkpoint_id,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()
