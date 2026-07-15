"""工作流工具库 - Python 封装函数

提供状态管理、任务分发、断点续跑等核心功能。
供 run_workflow.sh 调用的Python封装层。

Usage:
    from infra.tools.workflow.lib import get_state, set_state, advance_step
    dispatch_task('write_chapter_001', 'writer-a', '撰写第1章')

本包是从原 infra/tools/workflow/lib.py (814 行) 拆分而来:
    - db.py          数据库初始化 + flock 锁
    - state.py       get/set_state + advance_step
    - tasks.py       dispatch/verify/get_task_status/list_tasks
    - checkpoints.py create/list/restore/delete_checkpoint
    - events.py      _get_hook_engine / _trigger_event / trigger_event
    - batch.py       batch_dispatch_writer / batch_dispatch_reviewer
    - migration.py   migrate_json_to_sqlite (一次性工具)

公共 API 表面保持向后兼容: 所有原 lib.py 顶层符号仍然可从
`from infra.tools.workflow.lib import ...` 访问。
"""
# 路径常量（测试通过 monkeypatch 修改）
# 批量
from .batch import batch_dispatch_reviewer, batch_dispatch_writer

# 断点
from .checkpoints import (
    create_checkpoint,
    delete_checkpoint,
    list_checkpoints,
    restore_checkpoint,
)

# 锁（内部使用，但暴露以保持向后兼容）
from .db import (
    DB_DIR,
    DB_PATH,
    LOCKFILE,
    PROJECT_ROOT,
    WORKFLOW_FILE,
    _acquire_lock,
    _release_lock,
    init_sqlite,
)

# 事件
from .events import _get_hook_engine, _trigger_event, trigger_event

# 迁移
from .migration import migrate_json_to_sqlite

# 状态管理
from .state import advance_step, get_json, get_state, set_state

# 任务管理
from .tasks import dispatch_task, get_task_status, list_tasks, verify_task

__all__ = [
    # 常量
    "DB_DIR", "DB_PATH", "LOCKFILE", "PROJECT_ROOT", "WORKFLOW_FILE",
    # 数据库
    "init_sqlite",
    # 锁
    "_acquire_lock", "_release_lock",
    # 状态
    "advance_step", "get_json", "get_state", "set_state",
    # 任务
    "dispatch_task", "get_task_status", "list_tasks", "verify_task",
    # 断点
    "create_checkpoint", "delete_checkpoint", "list_checkpoints", "restore_checkpoint",
    # 事件
    "_get_hook_engine", "_trigger_event", "trigger_event",
    # 批量
    "batch_dispatch_reviewer", "batch_dispatch_writer",
    # 迁移
    "migrate_json_to_sqlite",
]


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m infra.tools.workflow.lib <command> [args...]")
        print("Commands: get_state, set_state, advance_step, dispatch_task, verify_task, checkpoint, restore, list_checkpoints, init")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "get_state":
        key = sys.argv[2] if len(sys.argv) > 2 else ""
        fallback = sys.argv[3] if len(sys.argv) > 3 else ""
        print(get_state(key, fallback))

    elif cmd == "set_state":
        key = sys.argv[2] if len(sys.argv) > 2 else ""
        value = sys.argv[3] if len(sys.argv) > 3 else ""
        print("OK" if set_state(key, value) else "FAILED")

    elif cmd == "advance_step":
        step = sys.argv[2] if len(sys.argv) > 2 else ""
        success, msg = advance_step(step)
        print(msg)

    elif cmd == "dispatch_task":
        task = sys.argv[2] if len(sys.argv) > 2 else ""
        agent = sys.argv[3] if len(sys.argv) > 3 else ""
        desc = sys.argv[4] if len(sys.argv) > 4 else ""
        print(dispatch_task(task, agent, desc))

    elif cmd == "verify_task":
        task = sys.argv[2] if len(sys.argv) > 2 else ""
        task_id = sys.argv[3] if len(sys.argv) > 3 else ""
        print("OK" if verify_task(task, task_id) else "FAILED")

    elif cmd == "checkpoint":
        note = sys.argv[2] if len(sys.argv) > 2 else ""
        print(create_checkpoint(note))

    elif cmd == "restore":
        cp_id = sys.argv[2] if len(sys.argv) > 2 else ""
        success, msg = restore_checkpoint(cp_id)
        print(msg)

    elif cmd == "list_checkpoints":
        for cp in list_checkpoints():
            print(f"{cp['checkpoint_id']}: {cp['phase']}/{cp['step']} - {cp['note']} ({cp['created_at']})")

    elif cmd == "init":
        init_sqlite()
        print("SQLite initialized")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
