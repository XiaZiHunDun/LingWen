# novel-factory/infra/tools/workflow/lib.py
"""工作流工具库 - Python封装函数

提供状态管理、任务分发、断点续跑等核心功能。
供 run_workflow.sh 调用的Python封装层。

Usage:
    from infra.tools.workflow.lib import get_state, set_state, advance_step
    dispatch_task('write_chapter_001', 'writer-a', '撰写第1章')
"""
import json
import sqlite3
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
WORKFLOW_FILE = PROJECT_ROOT / "workflow_state.json"
DB_DIR = PROJECT_ROOT / ".state"
DB_PATH = DB_DIR / "workflow.db"
LOCKFILE = PROJECT_ROOT / ".locks" / "workflow.lock"

# 确保目录存在
DB_DIR.mkdir(parents=True, exist_ok=True)
(LOCKFILE.parent).mkdir(parents=True, exist_ok=True)


# ============================================================
# 数据库初始化
# ============================================================

def init_sqlite() -> None:
    """初始化SQLite数据库（如不存在）"""
    conn = sqlite3.connect(str(DB_PATH))
    try:
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                checkpoint_id TEXT UNIQUE NOT NULL,
                phase TEXT,
                step TEXT,
                snapshot TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                note TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()


def _acquire_lock() -> bool:
    """获取flock锁"""
    import fcntl
    try:
        fd = os.open(str(LOCKFILE), os.O_CREAT | os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except (IOError, OSError):
        return False


# ============================================================
# 状态管理 (SQLite + JSON fallback)
# ============================================================

def get_state(key: str, fallback: str = "") -> str:
    """从SQLite获取状态，fallback到JSON

    Args:
        key: 状态键（如 'current_step'）
        fallback: 备用值（SQLite无数据时返回）

    Returns:
        状态值字符串
    """
    init_sqlite()

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            "SELECT value FROM workflow_state WHERE key = ?",
            (key,)
        )
        row = cur.fetchone()
        if row and row['value']:
            return row['value']
    except Exception:
        pass
    finally:
        conn.close()

    # SQLite无数据时fallback到JSON
    if WORKFLOW_FILE.exists():
        try:
            with open(WORKFLOW_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            val = data
            for k in key.split('.'):
                if k == '':
                    continue
                if k.isdigit() and isinstance(val, list):
                    val = val[int(k)]
                elif isinstance(val, dict):
                    val = val.get(k)
                else:
                    return fallback

            return str(val) if val is not None else fallback
        except Exception:
            pass

    return fallback


def set_state(key: str, value: str) -> bool:
    """写入SQLite状态

    Args:
        key: 状态键
        value: 状态值

    Returns:
        True成功，False失败
    """
    init_sqlite()

    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("""
            INSERT OR REPLACE INTO workflow_state (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, value))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}", file=__import__('sys').stderr)
        return False
    finally:
        conn.close()


def get_json(key: str, fallback: Any = None) -> Any:
    """直接从JSON获取值（不经SQLite）

    Args:
        key: JSON路径（如 'current_phase'）
        fallback: 备用值

    Returns:
        JSON值
    """
    if not WORKFLOW_FILE.exists():
        return fallback

    try:
        with open(WORKFLOW_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        val = data
        for k in key.split('.'):
            if k == '':
                continue
            if k.isdigit() and isinstance(val, list):
                val = val[int(k)]
            elif isinstance(val, dict):
                val = val.get(k)
            else:
                return fallback

        return val if val is not None else fallback
    except Exception:
        return fallback


# ============================================================
# 步骤推进
# ============================================================

def advance_step(target_step: str) -> Tuple[bool, str]:
    """步骤推进（带校验）

    Args:
        target_step: 目标步骤（如 'STEP_05'）

    Returns:
        (成功标志, 消息)
    """
    init_sqlite()

    current_step = get_state("current_step", "")

    # 校验转换合法性
    sys.path.insert(0, str(PROJECT_ROOT / "infra" / "state"))
    try:
        from workflow_validator import validate_transition

        is_valid, msg = validate_transition(current_step, target_step)
        if not is_valid:
            return False, f"INVALID: {msg}"
    except ImportError:
        pass  # validator不可用时跳过校验

    # 写入SQLite
    set_state("current_step", target_step)

    # 触发事件
    _trigger_event("STEP_COMPLETED", {
        "step": target_step,
        "previous_step": current_step
    })
    _trigger_event("state_updated", {
        "key": "current_step",
        "value": target_step
    })

    return True, f"Advanced to {target_step}"


# ============================================================
# 任务分发与验证
# ============================================================

def dispatch_task(task_name: str, agent: str, desc: str = "") -> str:
    """分发任务

    Args:
        task_name: 任务名称
        agent: Agent标识
        desc: 任务描述

    Returns:
        任务ID
    """
    init_sqlite()

    timestamp = datetime.now().isoformat()

    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("""
            INSERT OR REPLACE INTO agent_tasks
            (task_id, task_name, agent, status, dispatched_at, heartbeat_at, task_id_external, created_at)
            VALUES (?, ?, ?, 'pending', ?, ?, NULL, ?)
        """, (task_name, task_name, agent, timestamp, timestamp, timestamp))
        conn.commit()
        task_id = task_name
    except Exception as e:
        conn.rollback()
        task_id = f"ERROR: {e}"
    finally:
        conn.close()

    # 触发事件
    _trigger_event("MANUAL_TRIGGER", {
        "agent": agent,
        "task": task_name,
        "desc": desc
    })

    return task_id


def verify_task(task_name: str, task_id: str, status: str = "completed") -> bool:
    """验证任务完成

    Args:
        task_name: 任务名称
        task_id: Agent返回的task_id
        status: 新状态（默认completed）

    Returns:
        True成功，False失败
    """
    init_sqlite()

    timestamp = datetime.now().isoformat()

    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("""
            UPDATE agent_tasks
            SET status = ?, heartbeat_at = ?, task_id_external = ?
            WHERE task_id = ?
        """, (status, timestamp, task_id, task_name))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}", file=__import__('sys').stderr)
        return False
    finally:
        conn.close()


def get_task_status(task_name: str) -> Optional[Dict]:
    """获取任务状态

    Args:
        task_name: 任务名称

    Returns:
        任务信息字典，无则返回None
    """
    init_sqlite()

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            "SELECT * FROM agent_tasks WHERE task_id = ?",
            (task_name,)
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_tasks(status: Optional[str] = None) -> List[Dict]:
    """列出任务

    Args:
        status: 按状态过滤（如 'pending', 'running', 'completed'）

    Returns:
        任务列表
    """
    init_sqlite()

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        if status:
            cur = conn.execute(
                "SELECT * FROM agent_tasks WHERE status = ? ORDER BY created_at DESC",
                (status,)
            )
        else:
            cur = conn.execute("SELECT * FROM agent_tasks ORDER BY created_at DESC")
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# ============================================================
# 断点续跑
# ============================================================

def create_checkpoint(note: str = "") -> str:
    """创建断点快照

    Args:
        note: 断点说明

    Returns:
        checkpoint_id
    """
    init_sqlite()

    checkpoint_id = datetime.now().strftime("cp_%Y%m%d_%H%M%S")

    phase = get_state("current_phase", "N/A")
    step = get_state("current_step", "N/A")

    # 获取完整状态快照
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute("SELECT * FROM workflow_state")
        state_data = [dict(row) for row in cur.fetchall()]

        cur = conn.execute("SELECT * FROM agent_tasks ORDER BY created_at DESC")
        task_data = [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

    snapshot = {
        "phase": phase,
        "step": step,
        "state": state_data,
        "tasks": task_data,
        "workflow_file": str(WORKFLOW_FILE)
    }

    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute("""
            INSERT INTO checkpoints (checkpoint_id, phase, step, snapshot, note)
            VALUES (?, ?, ?, ?, ?)
        """, (checkpoint_id, phase, step, json.dumps(snapshot, ensure_ascii=False), note))
        conn.commit()
    finally:
        conn.close()

    return checkpoint_id


def list_checkpoints() -> List[Dict]:
    """列出所有断点

    Returns:
        断点列表
    """
    init_sqlite()

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            "SELECT checkpoint_id, phase, step, note, created_at FROM checkpoints ORDER BY created_at DESC"
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def restore_checkpoint(checkpoint_id: str) -> Tuple[bool, str]:
    """从断点恢复

    Args:
        checkpoint_id: 断点ID

    Returns:
        (成功标志, 消息)
    """
    init_sqlite()

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            "SELECT snapshot FROM checkpoints WHERE checkpoint_id = ?",
            (checkpoint_id,)
        )
        row = cur.fetchone()
        if not row:
            return False, f"Checkpoint not found: {checkpoint_id}"
    finally:
        conn.close()

    try:
        snapshot = json.loads(row['snapshot'])

        # 恢复状态
        conn.execute("BEGIN IMMEDIATE")
        try:
            # 清空现有状态
            conn.execute("DELETE FROM workflow_state")
            conn.execute("DELETE FROM agent_tasks")

            # 恢复状态数据
            for item in snapshot.get("state", []):
                conn.execute("""
                    INSERT INTO workflow_state (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (item['key'], item['value']))

            # 恢复任务数据
            for task in snapshot.get("tasks", []):
                conn.execute("""
                    INSERT INTO agent_tasks
                    (task_id, task_name, agent, status, heartbeat_at, task_id_external, dispatched_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task['task_id'],
                    task['task_name'],
                    task.get('agent', ''),
                    task.get('status', 'pending'),
                    task.get('heartbeat_at'),
                    task.get('task_id_external'),
                    task.get('dispatched_at'),
                    task.get('created_at', datetime.now().isoformat())
                ))

            conn.commit()
        except Exception as e:
            conn.rollback()
            return False, f"Restore failed: {e}"
        finally:
            conn.close()

        return True, f"Restored checkpoint {checkpoint_id}"
    except Exception as e:
        return False, f"Failed to parse checkpoint: {e}"


def delete_checkpoint(checkpoint_id: str) -> bool:
    """删除断点

    Args:
        checkpoint_id: 断点ID

    Returns:
        True成功
    """
    init_sqlite()

    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute("DELETE FROM checkpoints WHERE checkpoint_id = ?", (checkpoint_id,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


# ============================================================
# 事件触发
# ============================================================

def _trigger_event(event_name: str, data: Dict) -> None:
    """触发事件（异步）"""
    try:
        import asyncio
        sys.path.insert(0, str(PROJECT_ROOT))
        from infra.hooks.event_bus import Event, get_event_bus

        eb = get_event_bus()
        event = Event(name=event_name, source="lib.py", data=data)
        asyncio.run(eb.publish_async(event))
    except Exception:
        pass  # EventBus不可用时静默失败


def trigger_event(event_name: str, source: str = "lib.py", **data) -> None:
    """触发事件（公开接口）"""
    _trigger_event(event_name, data)


# ============================================================
# 批量操作
# ============================================================

def batch_dispatch_writer(chapters: List[str], writers: List[str] = None) -> Dict[str, str]:
    """批量分配作家任务

    Args:
        chapters: 章节列表（如 ['ch001', 'ch002']）
        writers: 作家列表，默认10个作家循环

    Returns:
        {chapter: task_id} 映射
    """
    if writers is None:
        writers = [chr(ord('a') + i) for i in range(10)]  # a-j

    results = {}
    for i, ch in enumerate(chapters):
        writer_id = writers[i % len(writers)]
        task_id = dispatch_task(f"write_{ch}", f"writer-{writer_id}", f"撰写{ch}")
        results[ch] = task_id

    return results


def batch_dispatch_reviewer(chapters: List[str], reviewers: List[str] = None) -> Dict[str, str]:
    """批量分配审核员任务

    Args:
        chapters: 章节列表
        reviewers: 审核员列表，默认5个审核员每2人一组

    Returns:
        {chapter: task_id} 映射
    """
    if reviewers is None:
        reviewers = [chr(ord('a') + i) for i in range(5)]  # a-e

    results = {}
    for i, ch in enumerate(chapters):
        reviewer_id = reviewers[i % len(reviewers)]
        task_id = dispatch_task(f"review_{ch}", f"reviewer-{reviewer_id}", f"审核{ch}")
        results[ch] = task_id

    return results


# ============================================================
# 迁移工具
# ============================================================

def migrate_json_to_sqlite() -> Tuple[int, int]:
    """将JSON状态迁移到SQLite

    Returns:
        (状态条数, 任务条数)
    """
    if not WORKFLOW_FILE.exists():
        return 0, 0

    with open(WORKFLOW_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("BEGIN IMMEDIATE")
    state_count = 0
    task_count = 0

    try:
        for key, value in data.items():
            if key == 'agent_tasks':
                continue
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)

            conn.execute("""
                INSERT OR REPLACE INTO workflow_state (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, str(value) if value else ''))
            state_count += 1

        for task_id, task in data.get('agent_tasks', {}).items():
            conn.execute("""
                INSERT OR REPLACE INTO agent_tasks
                (task_id, task_name, agent, status, heartbeat_at, task_id_external, dispatched_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                task.get('task_name', task_id),
                task.get('agent', ''),
                task.get('status', 'pending'),
                task.get('heartbeat_at'),
                task.get('task_id'),
                task.get('dispatched_at'),
                task.get('created_at', datetime.now().isoformat())
            ))
            task_count += 1

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        state_count = 0
        task_count = 0
    finally:
        conn.close()

    return state_count, task_count


# ============================================================
# 主入口（测试用）
# ============================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python lib.py <command> [args...]")
        print("Commands: get_state, set_state, advance_step, dispatch_task, verify_task, checkpoint, restore, list_checkpoints")
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