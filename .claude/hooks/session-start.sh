#!/bin/bash
# novel-factory/.claude/hooks/session-start.sh
# 会话开始钩子：加载项目状态、显示进度

NOVEL_FACTORY_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
STATE_FILE="$NOVEL_FACTORY_DIR/workflow_state.json"

echo "=== 灵文 · 工业化小说生产系统 ==="
echo ""

if [ -f "$STATE_FILE" ]; then
    # 解析当前阶段（使用 python 避免 jq 依赖）
    python3 -c "
import json
import sys
try:
    with open('$STATE_FILE', 'r') as f:
        state = json.load(f)
    current_phase = state.get('current_phase', 'UNKNOWN')
    current_step = state.get('current_step', 'UNKNOWN')
    print(f'当前阶段: {current_phase}')
    print(f'当前步骤: {current_step}')
    print('')
    # 显示未完成的步骤
    issues = state.get('issues_found', {})
    if issues:
        print(f'未解决问题数: {len(issues)}')
        print('')
except Exception as e:
    print(f'状态文件读取失败: {e}')
"
else
    echo "workflow_state.json 不存在，请先初始化项目"
fi

echo "输入 /help 查看可用命令"