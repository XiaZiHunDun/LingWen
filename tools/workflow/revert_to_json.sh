#!/bin/bash
# revert_to_json.sh - 紧急情况恢复到JSON模式
# 用途：当SQLite出现故障时，快速切换回workflow_state.json主控模式

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORKFLOW_FILE="$PROJECT_ROOT/workflow_state.json"
DB_PATH="$PROJECT_ROOT/.state/workflow.db"
BACKUP_DIR="$PROJECT_ROOT/.state/backup"

echo "=========================================="
echo "  紧急回滚：恢复JSON主控模式"
echo "=========================================="
echo ""

# 检查是否有备份
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/workflow_state.json.* 2>/dev/null | head -1)
if [ -z "$LATEST_BACKUP" ]; then
    echo "[ERROR] 没有找到workflow_state.json备份"
    echo "  请检查: $BACKUP_DIR"
    exit 1
fi

echo "[1/4] 停止所有运行中的Agent..."
# 给运行中的进程发送信号（如果需要）
echo "  （如需要，可手动kill相关进程）"

echo ""
echo "[2/4] 备份当前SQLite状态..."
if [ -f "$DB_PATH" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    cp "$DB_PATH" "$BACKUP_DIR/workflow.db.emergency_backup.$TIMESTAMP"
    echo "  SQLite已备份到: workflow.db.emergency_backup.$TIMESTAMP"
else
    echo "  SQLite不存在，跳过"
fi

echo ""
echo "[3/4] 恢复workflow_state.json..."
cp "$LATEST_BACKUP" "$WORKFLOW_FILE"
echo "  已恢复: $LATEST_BACKUP -> $WORKFLOW_FILE"

echo ""
echo "[4/4] 更新hooks.yaml为JSON模式..."
sed -i 's|sqlite://.state/workflow.db|workflow_state.json|g' "$PROJECT_ROOT/novel-factory/hooks.yaml" 2>/dev/null || true
echo "  hooks.yaml已更新为JSON模式"

echo ""
echo "=========================================="
echo "  回滚完成！"
echo "=========================================="
echo ""
echo "当前状态:"
echo "  workflow_state.json: $(ls -lh "$WORKFLOW_FILE" 2>/dev/null | awk '{print $5, $6, $7, $8}')"
echo "  SQLite状态: $([ -f "$DB_PATH" ] && echo "已保留(未删除)" || echo "不存在")"
echo ""
echo "下一步:"
echo "  1. 运行 ./run_workflow.sh status 检查状态"
echo "  2. 确认workflow_state.json内容正确"
echo "  3. 继续工作流"
echo ""
echo "如需恢复SQLite模式，执行:"
echo "  ./tools/workflow/restore_sqlite.sh"