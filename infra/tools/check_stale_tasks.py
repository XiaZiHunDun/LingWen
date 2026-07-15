#!/usr/bin/env python3
"""
检测workflow_state.json中的stale任务
超时阈值：30分钟（可配置）
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

STALE_THRESHOLD_MINUTES = 30

def check_stale_tasks(workflow_file: str) -> list[dict]:
    """检测stale任务并返回列表"""
    with open(workflow_file, 'r', encoding='utf-8') as f:
        wf = json.load(f)

    stale_tasks = []
    now = datetime.now()

    for task_id, task in wf.get('agent_tasks', {}).items():
        if task.get('status') == 'running':
            heartbeat_str = task.get('heartbeat_at')
            if heartbeat_str:
                try:
                    heartbeat = datetime.fromisoformat(heartbeat_str)
                    elapsed = now - heartbeat
                    if elapsed > timedelta(minutes=STALE_THRESHOLD_MINUTES):
                        task['stale_reason'] = f"heartbeat {elapsed.total_seconds():.0f}s ago"
                        task['task_id'] = task_id
                        stale_tasks.append(task)
                except ValueError:
                    pass

    return stale_tasks

def main():
    project_root = Path(__file__).parent.parent
    workflow_file = project_root / 'workflow_state.json'

    if len(sys.argv) > 1 and sys.argv[1] == '--fix':
        # 修复模式：标记stale任务
        stale = check_stale_tasks(str(workflow_file))
        if stale:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                wf = json.load(f)

            for task in stale:
                task_id = task['task_id']
                if task_id in wf['agent_tasks']:
                    wf['agent_tasks'][task_id]['status'] = 'stale'
                    print(f"Marked task {task_id} as stale")

            with open(workflow_file, 'w', encoding='utf-8') as f:
                json.dump(wf, f, ensure_ascii=False, indent=2)

            print(f"Fixed {len(stale)} stale tasks")
        else:
            print("No stale tasks found")
    else:
        # 只检测模式
        stale = check_stale_tasks(str(workflow_file))
        if stale:
            print(f"Found {len(stale)} stale tasks:")
            for task in stale:
                print(f"  - {task['task_id']}: {task.get('stale_reason', 'unknown')}")
            sys.exit(1)
        else:
            print("No stale tasks")

if __name__ == '__main__':
    main()
