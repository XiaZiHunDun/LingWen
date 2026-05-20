#!/bin/bash
# 小说工作室 · 工作流编排脚本 v3.0
# 简化为"传送带"：只做命令分发、参数解析、日志记录
# 核心逻辑委托给 infra/tools/workflow/lib.py
#
# 用法: ./run_workflow.sh [command] [params]
#
# 环境变量:
#   PROJECT_ROOT - 项目根目录（自动检测）
#   WORKFLOW_FILE - JSON状态文件路径
#   DB_PATH - SQLite数据库路径

set -euo pipefail

# ============================================================
# 路径初始化
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKFLOW_FILE="${WORKFLOW_FILE:-$PROJECT_ROOT/workflow_state.json}"
DB_PATH="${DB_PATH:-$PROJECT_ROOT/.state/workflow.db}"

# flock锁保护
LOCKFILE="$PROJECT_ROOT/.locks/workflow.lock"
mkdir -p "$(dirname "$LOCKFILE")"
exec 200>"$LOCKFILE"
flock -n 200 || { echo "[ERROR] Another instance is running"; exit 1; }

# ============================================================
# 颜色输出
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

function log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}
function log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}
function log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}
function log_section() {
    echo -e "${CYAN}=== $1 ===${NC}"
}

# ============================================================
# Python封装调用
# ============================================================

PYTHON_LIB="from infra.tools.workflow.lib import get_state, set_state, advance_step, dispatch_task, verify_task, create_checkpoint, list_checkpoints, restore_checkpoint, list_tasks, get_task_status, init_sqlite, migrate_json_to_sqlite; "

function py_call() {
    python3 -c "${PYTHON_LIB} $1" 2>&1
}

function py_call_bg() {
    python3 -c "${PYTHON_LIB} $1" &>/dev/null &
}

# ============================================================
# 命令实现
# ============================================================

# 初始化
function cmd_init() {
    log_section "初始化工作流"

    # 初始化SQLite
    py_call "init_sqlite()"
    log_info "SQLite初始化完成"

    # 如果JSON存在则迁移
    if [ -f "$WORKFLOW_FILE" ]; then
        log_warn "检测到workflow_state.json，迁移到SQLite..."
        result=$(py_call "migrate_json_to_sqlite()")
        state_count=$(echo "$result" | head -1 | cut -d',' -f1)
        task_count=$(echo "$result" | head -1 | cut -d',' -f2)
        log_info "迁移完成: $state_count 条状态, $task_count 条任务"
    else
        # 初始化空状态
        py_call "set_state(\"version\", \"v2.0\")"
        py_call "set_state(\"workflow_version\", \"v5.0（22步工作流）\")"
        py_call "set_state(\"current_phase\", \"PHASE_0_SETUP\")"
        py_call "set_state(\"current_step\", \"SETUP_00\")"
        py_call "set_state(\"initialized_at\", \"$(date +%Y-%m-%d)\")"
        log_info "工作流初始化完成"
    fi

    # 触发事件
    py_call_bg '_trigger_event("OUTLINE_APPROVED", {"phase": "PHASE_0_SETUP", "step": "SETUP_00"})'
}

# 状态查看
function cmd_status() {
    log_section "当前状态"
    echo "阶段: $(py_call "print(get_state('current_phase', 'N/A'))")"
    echo "步骤: $(py_call "print(get_state('current_step', 'N/A'))")"
    echo ""

    # 任务统计
    local task_count=$(py_call "len([t for t in list_tasks() if t.get('status') != 'completed'])" 2>/dev/null || echo "0")
    echo "进行中任务: $task_count"
    echo ""
}

# 步骤推进
function cmd_advance() {
    local target_step=${1:-}
    if [ -z "$target_step" ]; then
        log_error "用法: ./run_workflow.sh advance <STEP_XX>"
        exit 1
    fi

    result=$(py_call "advance_step('$target_step')")
    if [[ "$result" == *"INVALID"* ]]; then
        log_error "步骤校验失败: $result"
        exit 1
    fi
    log_info "$result"
}

# 启动任务
function cmd_launch() {
    local task_name=${1:-}
    local agent=${2:-}
    local desc=${3:-""}

    if [ -z "$task_name" ] || [ -z "$agent" ]; then
        log_error "用法: ./run_workflow.sh launch <task_name> <agent> [desc]"
        exit 1
    fi

    log_info "启动Agent: [$agent] -> $task_name"
    task_id=$(py_call "dispatch_task('$task_name', '$agent', '$desc')")
    echo "任务ID: $task_id"
    echo ""
    echo "请在主会话中使用 Agent 工具启动任务，并记录返回的 task_id"
    echo "然后运行: ./run_workflow.sh verify $task_name <task_id>"
}

# 验证任务
function cmd_verify() {
    local task_name=${1:-}
    local task_id=${2:-}

    if [ -z "$task_name" ] || [ -z "$task_id" ]; then
        log_error "用法: ./run_workflow.sh verify <task_name> <task_id>"
        exit 1
    fi

    log_info "验证任务: $task_name (task_id: $task_id)"
    success=$(py_call "verify_task('$task_name', '$task_id')")
    if [ "$success" = "True" ]; then
        log_info "任务验证完成"
    else
        log_error "验证失败"
        exit 1
    fi
}

# 批量分配作家
function cmd_assign_batch() {
    local type=${1:-}
    local range=${2:-}

    if [ -z "$type" ] || [ -z "$range" ]; then
        log_error "用法: ./run_workflow.sh assign_batch <writer|reviewer> <range>"
        exit 1
    fi

    log_info "批量分配: $type -> $range"

    if [ "$type" = "writer" ]; then
        echo "10作家并行写作（每人一章）："
        echo "  作家A → ch001, 作家B → ch002, ..."
        echo ""
        echo "使用: ./run_workflow.sh launch write_ch001 writer-a '撰写第1章'"
    elif [ "$type" = "reviewer" ]; then
        echo "5审核员并行审核（每2人一组）："
        echo "  审核员A+B → 审ch001-010"
        echo ""
        echo "使用: ./run_workflow.sh launch review_ch001 reviewer-a '审核第1章'"
    fi
}

# 任务列表
function cmd_tasks() {
    log_section "Agent任务追踪"
    py_call "print('\n'.join([f'{t[\"task_id\"]}: {t[\"agent\"]} ({t[\"status\"]})' for t in list_tasks()[:20]]))" 2>/dev/null || echo "（无任务记录）"
}

# 断点创建
function cmd_checkpoint() {
    local note=${1:-""}
    checkpoint_id=$(py_call "create_checkpoint('$note')")
    log_info "断点已创建: $checkpoint_id"
}

# 断点续跑
function cmd_resume() {
    local checkpoint_id=${1:-}

    if [ -z "$checkpoint_id" ]; then
        # 自动选择最新断点
        checkpoint_id=$(py_call "list_checkpoints()[0]['checkpoint_id'] if list_checkpoints() else ''")
        if [ -z "$checkpoint_id" ]; then
            log_error "没有可用的断点"
            exit 1
        fi
        log_info "自动选择最新断点: $checkpoint_id"
    fi

    log_info "从断点恢复: $checkpoint_id"
    result=$(py_call "restore_checkpoint('$checkpoint_id')")
    if [[ "$result" == *"Restored"* ]]; then
        log_info "$result"
    else
        log_error "$result"
        exit 1
    fi
}

# 列出断点
function cmd_list_checkpoints() {
    log_section "可用断点"
    py_call "print('\n'.join([f'{c[\"checkpoint_id\"]}: {c[\"phase\"]}/{c[\"step\"]} - {c[\"note\"]} ({c[\"created_at\"]})' for c in list_checkpoints()]))" 2>/dev/null || echo "（无断点）"
}

# 快速上手
function cmd_quickstart() {
    log_section "灵文 · 快速上手"
    echo ""
    echo "  1. 初始化:        ./run_workflow.sh init"
    echo "  2. 查看状态:      ./run_workflow.sh status"
    echo "  3. 启动任务:       ./run_workflow.sh launch <task> <agent> <desc>"
    echo "  4. 验证任务:       ./run_workflow.sh verify <task> <task_id>"
    echo "  5. 任务列表:       ./run_workflow.sh tasks"
    echo "  6. 创建断点:       ./run_workflow.sh checkpoint [note]"
    echo "  7. 断点续跑:       ./run_workflow.sh resume [checkpoint_id]"
    echo "  8. 列出断点:       ./run_workflow.sh list_checkpoints"
    echo ""
}

# 帮助
function cmd_help() {
    echo "用法: $0 {command} [params]"
    echo ""
    echo "Commands:"
    echo "  init              - 初始化工作流"
    echo "  quickstart       - 快速上手指南"
    echo "  status           - 查看当前状态"
    echo "  advance <step>    - 推进到指定步骤"
    echo "  launch <t> <a> [d] - 启动Agent任务"
    echo "  verify <t> <id>   - 验证任务完成"
    echo "  assign_batch <t> <r> - 批量分配（writer/reviewer）"
    echo "  tasks            - 查看任务列表"
    echo "  checkpoint [note] - 创建断点"
    echo "  resume [cp_id]    - 从断点恢复（默认最新）"
    echo "  list_checkpoints  - 列出可用断点"
    echo "  help             - 显示帮助"
    echo ""
}

# ============================================================
# 主入口
# ============================================================

COMMAND=${1:-help}

case "$COMMAND" in
    init)              cmd_init ;;
    quickstart)        cmd_quickstart ;;
    status)            cmd_status ;;
    advance)           cmd_advance "$2" ;;
    launch)           cmd_launch "$2" "$3" "$4" ;;
    verify)           cmd_verify "$2" "$3" ;;
    assign_batch)     cmd_assign_batch "$2" "$3" ;;
    tasks)            cmd_tasks ;;
    checkpoint)       cmd_checkpoint "$2" ;;
    resume)           cmd_resume "$2" ;;
    list_checkpoints)  cmd_list_checkpoints ;;
    help|--help|-h)   cmd_help ;;
    *)
        log_error "未知命令: $COMMAND"
        cmd_help
        exit 1
        ;;
esac