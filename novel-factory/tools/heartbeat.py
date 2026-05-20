#!/usr/bin/env python3
"""更新指定任务的heartbeat时间戳"""
import json
import sys
from pathlib import Path

def update_heartbeat(task_name: str):
    project_root = Path(__file__).parent.parent
    workflow_file = project_root / 'workflow_state.json'

    with open(workflow_file, 'r', encoding='utf-8') as f:
        wf = json.load(f)

    if task_name in wf.get('agent_tasks', {}):
        from datetime import datetime
        wf['agent_tasks'][task_name]['heartbeat_at'] = datetime.now().isoformat()

        with open(workflow_file, 'w', encoding='utf-8') as f:
            json.dump(wf, f, ensure_ascii=False, indent=2)

        print(f"Updated heartbeat for task: {task_name}")
    else:
        print(f"Task not found: {task_name}")
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        update_heartbeat(sys.argv[1])
    else:
        print("Usage: heartbeat.py <task_name>")