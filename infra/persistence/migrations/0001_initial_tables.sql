-- Initial database schema (baseline migration)
-- This migration creates the core tables used by the system

-- Ripple system tables
CREATE TABLE IF NOT EXISTS reference_nodes (
    id TEXT PRIMARY KEY,
    dimension TEXT NOT NULL,
    volume INTEGER NOT NULL,
    chapter INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_nodes_volume ON reference_nodes(volume);
CREATE INDEX IF NOT EXISTS idx_nodes_dim ON reference_nodes(dimension);

CREATE TABLE IF NOT EXISTS reference_edges (
    id TEXT PRIMARY KEY,
    from_node_id TEXT NOT NULL REFERENCES reference_nodes(id),
    to_node_id TEXT NOT NULL REFERENCES reference_nodes(id),
    relationship_type TEXT NOT NULL,
    weight REAL NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_edges_from ON reference_edges(from_node_id);
CREATE INDEX IF NOT EXISTS idx_edges_to ON reference_edges(to_node_id);

CREATE TABLE IF NOT EXISTS reference_ripples (
    id TEXT PRIMARY KEY,
    trigger_volume INTEGER NOT NULL,
    trigger_chapter INTEGER NOT NULL,
    affected_nodes TEXT NOT NULL,
    affected_edges TEXT NOT NULL,
    proposed_actions TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    confirmed_at TEXT,
    applied_at TEXT,
    payload TEXT NOT NULL,
    parent_ripple_id TEXT
);

CREATE TABLE IF NOT EXISTS ripple_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ripple_id TEXT NOT NULL REFERENCES reference_ripples(id),
    action TEXT NOT NULL CHECK(action IN ('created', 'applied', 'rejected', 'failed', 'rolled_back')),
    prev_status TEXT,
    new_status TEXT NOT NULL,
    actor TEXT NOT NULL,
    origin TEXT NOT NULL CHECK(origin IN ('ui', 'cli', 'system')),
    reason TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_ripple ON ripple_audit(ripple_id, created_at DESC);

CREATE TABLE IF NOT EXISTS ripple_cascade (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_ripple_id TEXT NOT NULL,
    cascade_nodes_json TEXT NOT NULL,
    cascade_edges_json TEXT NOT NULL,
    cascade_actions_json TEXT NOT NULL,
    depth_reached INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (trigger_ripple_id) REFERENCES reference_ripples(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cascade_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ripple_id TEXT NOT NULL,
    max_depth INTEGER NOT NULL,
    depth_reached INTEGER NOT NULL,
    algorithm TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('running', 'completed', 'cancelled', 'failed')),
    nodes_json TEXT NOT NULL,
    edges_json TEXT NOT NULL,
    actions_json TEXT NOT NULL,
    FOREIGN KEY (ripple_id) REFERENCES reference_ripples(id) ON DELETE CASCADE
);

-- Cost tracking tables
CREATE TABLE IF NOT EXISTS cost_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario TEXT NOT NULL,
    tier TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_usd REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_cost_records_scenario ON cost_records(scenario);
CREATE INDEX IF NOT EXISTS idx_cost_records_timestamp ON cost_records(timestamp);

-- Budget tables
CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL,
    usd REAL NOT NULL,
    run_id TEXT,
    set_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_budgets_scope_setat ON budgets(scope, set_at DESC);

CREATE TABLE IF NOT EXISTS budgets_by_tier (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tier TEXT NOT NULL,
    usd REAL NOT NULL,
    set_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workflow tables
CREATE TABLE IF NOT EXISTS workflow_state (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

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
);

CREATE TABLE IF NOT EXISTS state_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT,
    record_id TEXT,
    old_value TEXT,
    new_value TEXT,
    changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    changed_by TEXT
);

-- Reading power tables
CREATE TABLE IF NOT EXISTS hooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter TEXT NOT NULL,
    hook_type TEXT NOT NULL,
    strength REAL NOT NULL,
    position TEXT NOT NULL,
    content TEXT NOT NULL,
    llm_analyzed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chapter, hook_type, position)
);

CREATE TABLE IF NOT EXISTS coolpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter TEXT NOT NULL,
    pattern TEXT NOT NULL,
    density REAL NOT NULL,
    combo_with TEXT,
    content TEXT NOT NULL,
    llm_analyzed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chapter, pattern)
);

CREATE TABLE IF NOT EXISTS chapter_summary (
    chapter TEXT PRIMARY KEY,
    hook_count INTEGER DEFAULT 0,
    hook_strength_avg REAL DEFAULT 0.0,
    coolpoint_count INTEGER DEFAULT 0,
    coolpoint_density REAL DEFAULT 0.0,
    reading_power_score REAL DEFAULT 0.0,
    last_analyzed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analysis_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter TEXT NOT NULL,
    analyzer_type TEXT NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    duration_ms INTEGER,
    status TEXT NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);