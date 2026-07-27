QUERIES = {
    "upsert_workflow_state": """
        INSERT INTO workflow_state (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = CURRENT_TIMESTAMP
    """,
    "select_workflow_state": """
        SELECT * FROM workflow_state 
        WHERE key = ?
    """,
    "select_all_workflow_states": """
        SELECT * FROM workflow_state 
        ORDER BY updated_at DESC
    """,
    "insert_agent_task": """
        INSERT INTO agent_tasks (task_id, task_name, agent, status)
        VALUES (?, ?, ?, ?)
    """,
    "update_agent_task": """
        UPDATE agent_tasks 
        SET status = ?, heartbeat_at = ?, task_id_external = ?, dispatched_at = ?, error_msg = ?
        WHERE task_id = ?
    """,
    "select_agent_task": """
        SELECT * FROM agent_tasks 
        WHERE task_id = ?
    """,
    "select_agent_tasks_by_status": """
        SELECT * FROM agent_tasks 
        WHERE status = ? 
        ORDER BY created_at DESC
    """,
    "insert_state_history": """
        INSERT INTO state_history (table_name, record_id, old_value, new_value, changed_by)
        VALUES (?, ?, ?, ?, ?)
    """,
}