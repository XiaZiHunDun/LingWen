#!/bin/bash
# restore_sqlite.sh - 从JSON恢复到SQLite模式
# 用途：重新启用SQLite作为主控状态存储

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORKFLOW_FILE="$PROJECT_ROOT/workflow_state.json"
DB_PATH="$PROJECT_ROOT/.state/workflow.db"
HOOKS_FILE="$PROJECT_ROOT/novel-factory/hooks.yaml"

echo "=========================================="
echo "  恢复SQLite主控模式"
echo "=========================================="
echo ""

echo "[1/3] 更新hooks.yaml为SQLite模式..."
sed -i 's|workflow_state.json|sqlite://.state/workflow.db|g' "$HOOKS_FILE" 2>/dev/null || true
echo "  hooks.yaml已更新为SQLite模式"

echo ""
echo "[2/3] 运行迁移脚本..."
if [ -f "$PROJECT_ROOT/novel-factory/infra/tools/migrate_to_sqlite.py" ]; then
    python3 "$PROJECT_ROOT/novel-factory/infra/tools/migrate_to_sqlite.py"
    echo "  迁移完成"
else
    echo "  迁移脚本不存在，跳过"
fi

echo ""
echo "[3/3] 初始化SQLite（如果尚未存在）..."
mkdir -p "$(dirname "$DB_PATH")"
python3 << PYEOF
import sqlite3
db_path = '$DB_PATH'
conn = sqlite3.connect(db_path)
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
conn.execute("""
    CREATE TABLE IF NOT EXISTS state_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_name TEXT,
        record_id TEXT,
        old_value TEXT,
        new_value TEXT,
        changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
        changed_by TEXT
    )
""")
conn.commit()
conn.close()
print("SQLite初始化完成")
PYEOF

echo ""
echo "=========================================="
echo "  SQLite模式已恢复！"
echo "=========================================="
echo ""
echo "下一步:"
echo "  1. 运行 ./run_workflow.sh init (如果需要重新初始化)"
echo "  2. 运行 ./run_workflow.sh status 检查状态"
echo ""