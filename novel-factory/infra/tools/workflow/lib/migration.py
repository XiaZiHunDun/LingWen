"""JSON → SQLite 数据迁移（一次性工具，v7.0 之后已不需要）"""
import json
import sqlite3
from datetime import datetime
from typing import Tuple

from . import db


def migrate_json_to_sqlite() -> Tuple[int, int]:
    """将JSON状态迁移到SQLite

    Returns:
        (状态条数, 任务条数)
    """
    if not db.WORKFLOW_FILE.exists():
        return 0, 0

    with open(db.WORKFLOW_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    conn = sqlite3.connect(str(db.DB_PATH))
    conn.execute("BEGIN IMMEDIATE")
    state_count = 0
    task_count = 0

    try:
        for key, value in data.items():
            if key == 'agent_tasks':
                continue
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)

            conn.execute("""
                INSERT OR REPLACE INTO workflow_state (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, str(value) if value else ''))
            state_count += 1

        for task_id, task in data.get('agent_tasks', {}).items():
            conn.execute("""
                INSERT OR REPLACE INTO agent_tasks
                (task_id, task_name, agent, status, heartbeat_at, task_id_external, dispatched_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                task.get('task_name', task_id),
                task.get('agent', ''),
                task.get('status', 'pending'),
                task.get('heartbeat_at'),
                task.get('task_id'),
                task.get('dispatched_at'),
                task.get('created_at', datetime.now().isoformat())
            ))
            task_count += 1

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        state_count = 0
        task_count = 0
    finally:
        conn.close()

    return state_count, task_count
