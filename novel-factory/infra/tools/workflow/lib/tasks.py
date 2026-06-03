"""任务分发、验证、查询

对应 agent_tasks 表的 CRUD
"""
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

from . import db, events


def dispatch_task(task_name: str, agent: str, desc: str = "") -> str:
    """分发任务

    Args:
        task_name: 任务名称
        agent: Agent标识
        desc: 任务描述

    Returns:
        任务ID
    """
    db.init_sqlite()

    timestamp = datetime.now().isoformat()

    conn = sqlite3.connect(str(db.DB_PATH))
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("""
            INSERT OR REPLACE INTO agent_tasks
            (task_id, task_name, agent, status, dispatched_at, heartbeat_at, task_id_external, created_at)
            VALUES (?, ?, ?, 'pending', ?, ?, NULL, ?)
        """, (task_name, task_name, agent, timestamp, timestamp, timestamp))
        conn.commit()
        task_id = task_name
    except Exception as e:
        conn.rollback()
        task_id = f"ERROR: {e}"
    finally:
        conn.close()

    # 触发事件
    events._trigger_event("MANUAL_TRIGGER", {
        "agent": agent,
        "task": task_name,
        "desc": desc
    })

    return task_id


def verify_task(task_name: str, task_id: str, status: str = "completed") -> bool:
    """验证任务完成

    Args:
        task_name: 任务名称
        task_id: Agent返回的task_id
        status: 新状态（默认completed）

    Returns:
        True成功，False失败
    """
    db.init_sqlite()

    timestamp = datetime.now().isoformat()

    conn = sqlite3.connect(str(db.DB_PATH))
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("""
            UPDATE agent_tasks
            SET status = ?, heartbeat_at = ?, task_id_external = ?
            WHERE task_id = ?
        """, (status, timestamp, task_id, task_name))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}", file=__import__('sys').stderr)
        return False
    finally:
        conn.close()


def get_task_status(task_name: str) -> Optional[Dict]:
    """获取任务状态

    Args:
        task_name: 任务名称

    Returns:
        任务信息字典，无则返回None
    """
    db.init_sqlite()

    conn = sqlite3.connect(str(db.DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            "SELECT * FROM agent_tasks WHERE task_id = ?",
            (task_name,)
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_tasks(status: Optional[str] = None) -> List[Dict]:
    """列出任务

    Args:
        status: 按状态过滤（如 'pending', 'running', 'completed'）

    Returns:
        任务列表
    """
    db.init_sqlite()

    conn = sqlite3.connect(str(db.DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        if status:
            cur = conn.execute(
                "SELECT * FROM agent_tasks WHERE status = ? ORDER BY created_at DESC",
                (status,)
            )
        else:
            cur = conn.execute("SELECT * FROM agent_tasks ORDER BY created_at DESC")
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
