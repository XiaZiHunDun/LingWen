#!/bin/bash
# novel-factory/.claude/hooks/session-stop.sh
# 会话结束钩子：保存进度、更新状态

NOVEL_FACTORY_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
STATE_FILE="$NOVEL_FACTORY_DIR/workflow_state.json"
SESSION_STATE="$NOVEL_FACTORY_DIR/production/session-state/active.md"

# 创建会话状态目录
mkdir -p "$NOVEL_FACTORY_DIR/production/session-state"

# 记录会话结束状态
echo "# 会话状态 - $(date '+%Y-%m-%d %H:%M:%S')

## 当前进度
" > "$SESSION_STATE"

if [ -f "$STATE_FILE" ]; then
    python3 -c "
import json
try:
    with open('$STATE_FILE', 'r') as f:
        state = json.load(f)
    current_phase = state.get('current_phase', 'UNKNOWN')
    current_step = state.get('current_step', 'UNKNOWN')
    with open('$SESSION_STATE', 'a') as f:
        f.write(f'- 阶段: {current_phase}\n')
        f.write(f'- 步骤: {current_step}\n')
        f.write(f'- 累计问题: {len(state.get(\"issues_found\", {}))}\n')
except Exception as e:
    print(f'状态保存失败: {e}')
" >> "$SESSION_STATE"
fi

echo "
## 会话结束
- 已保存工作进度
" >> "$SESSION_STATE"

echo "会话进度已保存"