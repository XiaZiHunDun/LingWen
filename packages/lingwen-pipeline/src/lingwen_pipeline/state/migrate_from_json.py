#!/usr/bin/env python3
"""
Migrate workflow_state.json to SQLite
Creates backup of original JSON and imports all data

v16.5 #N.3: Migrated to SqliteStorageAdapter from lingwen_storage.
Public API unchanged: migrate_from_json(json_path, db_path) returns dict.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

from lingwen_storage.sqlite_storage_adapter import SqliteStorageAdapter


def migrate_from_json(json_path: str, db_path: str) -> dict:
    """
    Read workflow_state.json and migrate to SQLite database

    Returns migration report with counts and any errors

    v16.5 #N.3: storage layer now SqliteStorageAdapter from lingwen_storage
    (previously direct sqlite3). Public API preserved.
    """
    json_path = Path(json_path)
    db_path = Path(db_path)

    # Backup original JSON
    backup_path = json_path.with_suffix(".json.backup")
    shutil.copy2(json_path, backup_path)

    # Load JSON
    with open(json_path) as f:
        data = json.load(f)

    # Import here to avoid circular imports
    from lingwen_pipeline.state.state_manager import StateManager

    # Initialize StateManager (creates schema)
    StateManager(db_path)

    # Migrate current step/phase
    current_step = data.get("current_step", "STEP_00")
    current_phase = data.get("current_phase", "PHASE_0_INIT")
    version = data.get("version", "v8.2")

    storage = SqliteStorageAdapter(str(db_path))

    def _do(conn) -> dict:
        conn.execute(
            """
            INSERT OR REPLACE INTO workflow_state (key, value, updated_at)
            VALUES ('current_step', ?, CURRENT_TIMESTAMP)
        """,
            (current_step,),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO workflow_state (key, value, updated_at)
            VALUES ('current_phase', ?, CURRENT_TIMESTAMP)
        """,
            (current_phase,),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO workflow_state (key, value, updated_at)
            VALUES ('version', ?, CURRENT_TIMESTAMP)
        """,
            (version,),
        )

        # Migrate tasks
        tasks_migrated = 0
        if "writer_batches" in data:
            for batch_id, batch in data["writer_batches"].items():
                status = batch.get("status", "pending")
                # Normalize status to allowed values
                if status == "in_progress":
                    status = "running"
                elif status not in ("pending", "running", "completed", "failed"):
                    status = "pending"

                conn.execute(
                    """
                    INSERT OR REPLACE INTO task (id, task_name, agent, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (
                        batch_id,
                        batch.get("chapter_range", batch_id),
                        "content_writer",
                        status,
                        batch.get("created_at", datetime.now().isoformat()),
                    ),
                )
                tasks_migrated += 1

        if "batches" in data:
            for batch_id, batch in data["batches"].items():
                status = batch.get("status", "pending")
                if status == "in_progress":
                    status = "running"
                elif status not in ("pending", "running", "completed", "failed"):
                    status = "pending"

                conn.execute(
                    """
                    INSERT OR REPLACE INTO task (id, task_name, agent, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (
                        batch_id,
                        batch.get("chapter_range", batch_id),
                        batch.get("chief", "auditor"),
                        status,
                        batch.get("created_at", datetime.now().isoformat()),
                    ),
                )
                tasks_migrated += 1

        # Migrate review_queue entries to audit_log
        audit_entries = 0
        if "review_queue" in data:
            review_queue = data["review_queue"]
            for completed in review_queue.get("completed", []):
                batch_id = completed.get("batch_id", "unknown")
                reviewer = completed.get("reviewer", "unknown")
                chapters = completed.get("chapters", [])

                conn.execute(
                    """
                    INSERT INTO audit_log (task_id, action, result, new_value, changed_by)
                    VALUES (?, 'review_completed', ?, ?, 'Migration')
                """,
                    (
                        batch_id,
                        "completed",
                        json.dumps(
                            {
                                "batch_id": batch_id,
                                "reviewer": reviewer,
                                "chapters": chapters,
                                "completed_at": completed.get("completed_at", ""),
                            }
                        ),
                    ),
                )
                audit_entries += 1

        return {"tasks_migrated": tasks_migrated, "audit_entries": audit_entries}

    counts = storage.with_transaction(_do)

    return {
        "backup_created": str(backup_path),
        "version": version,
        "current_step": current_step,
        "current_phase": current_phase,
        "tasks_migrated": counts["tasks_migrated"],
        "audit_entries": counts["audit_entries"],
        "phases": list(data.get("phases", {}).keys()),
    }


if __name__ == "__main__":
    import sys

    project_root = Path(__file__).parent.parent.parent
    json_path = project_root / "workflow_state.json"
    db_path = project_root / ".state" / "workflow.db"

    print(f"Migrating {json_path} -> {db_path}")

    report = migrate_from_json(json_path, db_path)

    print("\n=== Migration Complete ===")
    print(f"Backup: {report['backup_created']}")
    print(f"Version: {report['version']}")
    print(f"Current Step: {report['current_step']}")
    print(f"Current Phase: {report['current_phase']}")
    print(f"Tasks Migrated: {report['tasks_migrated']}")
    print(f"Audit Entries: {report['audit_entries']}")
    print(f"Phases: {report['phases']}")
