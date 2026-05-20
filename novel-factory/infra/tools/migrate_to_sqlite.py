#!/usr/bin/env python3
"""
Migrate existing workflow_state.json to SQLite
Backup original JSON file before migration
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime


def migrate(workflow_json: str, db_path: str):
    # Backup
    backup_path = workflow_json + f".backup-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    with open(workflow_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Save backup
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Backed up JSON to: {backup_path}")

    # Initialize SQLite
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))

    # Create schema
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

    # Migrate top-level state
    for key, value in data.items():
        if key not in ('agent_tasks',):
            conn.execute("""
                INSERT OR REPLACE INTO workflow_state (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, json.dumps(value, ensure_ascii=False)))

    # Migrate agent_tasks
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

    conn.commit()
    conn.close()
    print(f"Migration complete. SQLite DB: {db_path}")


if __name__ == '__main__':
    project_root = Path(__file__).parent.parent.parent
    workflow_json = project_root / 'workflow_state.json'
    db_path = project_root / '.state' / 'workflow.db'

    migrate(str(workflow_json), str(db_path))