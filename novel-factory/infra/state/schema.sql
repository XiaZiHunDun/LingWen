-- SQLite Schema for Workflow State Management
-- Replaces workflow_state.json with atomic SQLite operations

-- Workflow state tracking (key-value store)
CREATE TABLE IF NOT EXISTS workflow_state (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent task registry
CREATE TABLE IF NOT EXISTS task (
    id TEXT PRIMARY KEY,
    task_name TEXT NOT NULL,
    agent TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'running', 'completed', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit log for all state changes
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    action TEXT NOT NULL,
    result TEXT,
    old_value TEXT,
    new_value TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by TEXT
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_task_status ON task(status);
CREATE INDEX IF NOT EXISTS idx_task_agent ON task(agent);
CREATE INDEX IF NOT EXISTS idx_audit_task ON audit_log(task_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);

-- Initial state rows
INSERT OR IGNORE INTO workflow_state (key, value, updated_at)
VALUES ('current_step', 'STEP_00', CURRENT_TIMESTAMP);

INSERT OR IGNORE INTO workflow_state (key, value, updated_at)
VALUES ('current_phase', 'PHASE_0_INIT', CURRENT_TIMESTAMP);

INSERT OR IGNORE INTO workflow_state (key, value, updated_at)
VALUES ('version', 'v8.2', CURRENT_TIMESTAMP);