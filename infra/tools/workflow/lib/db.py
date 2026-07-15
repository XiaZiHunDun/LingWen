"""数据库初始化与文件锁

SQLite 数据库连接管理 + flock 互斥锁
"""
import logging
import os
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
WORKFLOW_FILE = PROJECT_ROOT / "workflow_state.json"
DB_DIR = PROJECT_ROOT / ".state"
DB_PATH = DB_DIR / "workflow.db"
LOCKFILE = PROJECT_ROOT / ".locks" / "workflow.lock"

# 确保目录存在
DB_DIR.mkdir(parents=True, exist_ok=True)
(LOCKFILE.parent).mkdir(parents=True, exist_ok=True)


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


_lock_fd = None


def _acquire_lock() -> bool:
    """获取flock锁"""
    global _lock_fd
    import fcntl
    try:
        _lock_fd = os.open(str(LOCKFILE), os.O_CREAT | os.O_RDWR)
        fcntl.flock(_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except (IOError, OSError):
        return False


def _release_lock() -> None:
    """释放flock锁"""
    global _lock_fd
    import fcntl
    if _lock_fd is not None:
        try:
            fcntl.flock(_lock_fd, fcntl.LOCK_UN)
            os.close(_lock_fd)
        except (IOError, OSError):
            pass
        _lock_fd = None
