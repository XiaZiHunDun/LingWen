#!/bin/bash
# backup_json.sh - 定期备份workflow_state.json（过渡期兼容）
# 用途：在SQLite迁移期间保持JSON备份，确保可回滚

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORKFLOW_FILE="$PROJECT_ROOT/workflow_state.json"
BACKUP_DIR="$PROJECT_ROOT/.state/backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "[INFO] 备份workflow_state.json..."
echo "  源文件: $WORKFLOW_FILE"
echo "  备份目录: $BACKUP_DIR"

if [ -f "$WORKFLOW_FILE" ]; then
    # 创建带时间戳的备份
    cp "$WORKFLOW_FILE" "$BACKUP_DIR/workflow_state.json.$TIMESTAMP"
    echo "  已备份: workflow_state.json.$TIMESTAMP"

    # 保持最近的5个备份
    cd "$BACKUP_DIR"
    ls -t workflow_state.json.* 2>/dev/null | tail -n +6 | xargs -r rm -f
    echo "  清理旧备份（保留最近5个）"

    # 同时备份SQLite（如果有）
    DB_PATH="$PROJECT_ROOT/.state/workflow.db"
    if [ -f "$DB_PATH" ]; then
        cp "$DB_PATH" "$BACKUP_DIR/workflow.db.$TIMESTAMP"
        echo "  SQLite已备份: workflow.db.$TIMESTAMP"
    fi

    # 列出当前备份
    echo ""
    echo "当前备份文件:"
    ls -lh "$BACKUP_DIR"/workflow* 2>/dev/null || echo "（无备份）"
else
    echo "[WARN] workflow_state.json不存在，无需备份"
fi

echo ""
echo "[INFO] 下次备份可通过cron自动执行"
echo "  添加到crontab: 0 */6 * * * $PROJECT_ROOT/tools/workflow/backup_json.sh"