#!/bin/bash
# 日志审计函数库

LOG_DIR="$(cd "$(dirname "$0")/../.." && pwd)/logs"
mkdir -p "$LOG_DIR"

function log_audit() {
    local level=$1
    local action=$2
    local target=$3
    local user=${USER:-unknown}
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $action | $target | user=$user" >> "$LOG_DIR/workflow_$(date +%Y%m%d).log"
}

function log_error_audit() {
    local message=$1
    local context=${2:-}
    log_audit "ERROR" "$message" "$context"
}