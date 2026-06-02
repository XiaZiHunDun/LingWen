"""状态管理 + 步骤推进

SQLite 主存储 + JSON 兜底 + 步骤转换校验
"""
import json
import logging
import sqlite3
import sys
from typing import Any, Tuple

from . import db
from . import events

logger = logging.getLogger(__name__)


def get_state(key: str, fallback: str = "") -> str:
    """从SQLite获取状态，fallback到JSON

    Args:
        key: 状态键（如 'current_step'）
        fallback: 备用值（SQLite无数据时返回）

    Returns:
        状态值字符串
    """
    db.init_sqlite()

    # 使用WAL模式和只读事务提高并发读性能
    conn = sqlite3.connect(str(db.DB_PATH), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            "SELECT value FROM workflow_state WHERE key = ?",
            (key,)
        )
        row = cur.fetchone()
        if row and row['value']:
            return row['value']
    except Exception as e:
        logger.warning(f"get_state读取失败: {e}")
    finally:
        conn.close()

    # SQLite无数据时fallback到JSON
    if db.WORKFLOW_FILE.exists():
        try:
            with open(db.WORKFLOW_FILE, 'r', encoding='utf-8') as f:
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
    db.init_sqlite()

    conn = sqlite3.connect(str(db.DB_PATH), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
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
    if not db.WORKFLOW_FILE.exists():
        return fallback

    try:
        with open(db.WORKFLOW_FILE, 'r', encoding='utf-8') as f:
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


def advance_step(target_step: str) -> Tuple[bool, str]:
    """步骤推进（带校验）

    Args:
        target_step: 目标步骤（如 'STEP_05'）

    Returns:
        (成功标志, 消息)
    """
    db.init_sqlite()

    current_step = get_state("current_step", "")

    # 校验转换合法性
    sys.path.insert(0, str(db.PROJECT_ROOT / "infra" / "state"))
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
    events._trigger_event("STEP_COMPLETED", {
        "step": target_step,
        "previous_step": current_step
    })
    events._trigger_event("state_updated", {
        "key": "current_step",
        "value": target_step
    })

    # STEP_17完成时触发强制验证闭环事件
    if target_step == 'STEP_17':
        events._trigger_event("STEP_17_COMPLETED", {
            "step": "STEP_17",
            "previous_step": current_step,
            "verify_result": None  # 初始为null，等待验证
        })

    return True, f"Advanced to {target_step}"
