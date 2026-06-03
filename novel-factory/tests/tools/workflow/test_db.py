"""Tests for infra.tools.workflow.lib.db (init_sqlite, _acquire_lock).

Lowest-layer tests: DB schema + flock lock. These exercise the foundation
that state/tasks/checkpoints all depend on.
"""
import sqlite3


class TestInitSqlite:
    """Tests for init_sqlite function"""

    def test_init_creates_tables(self, mock_env):
        """Test that init_sqlite creates all required tables"""
        from infra.tools.workflow.lib import init_sqlite

        # 必须从 .db 子模块 import DB_PATH — lib/__init__.py 用
        # `from .db import DB_PATH` 在 import 时把值冻结,后续 monkeypatch
        # 改的 infra.tools.workflow.lib.db.DB_PATH 不会反映到 lib.DB_PATH。
        # init_sqlite 函数自身在 db.py 内,会读 monkeypatch 后的 db.DB_PATH;
        # 但本测试需要从同一处读,才能连到 init 过的 tmp DB。
        from infra.tools.workflow.lib.db import DB_PATH

        init_sqlite()

        conn = sqlite3.connect(str(DB_PATH))
        tables = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' ORDER BY name
        """).fetchall()
        conn.close()

        table_names = [t[0] for t in tables]
        assert 'workflow_state' in table_names
        assert 'agent_tasks' in table_names
        assert 'state_history' in table_names
        assert 'checkpoints' in table_names

    def test_init_is_idempotent(self, init_db):
        """Test that calling init_sqlite multiple times doesn't error"""
        from infra.tools.workflow.lib import init_sqlite
        init_sqlite()
        init_sqlite()

    def test_init_creates_workflow_state_table(self, mock_env):
        """Test workflow_state table structure"""
        from infra.tools.workflow.lib import init_sqlite

        # 见 test_init_creates_tables — 从 .db 子模块 import 拿到 monkeypatch 后的值
        from infra.tools.workflow.lib.db import DB_PATH

        init_sqlite()

        conn = sqlite3.connect(str(DB_PATH))
        columns = [col[1] for col in conn.execute("PRAGMA table_info(workflow_state)").fetchall()]
        conn.close()

        assert 'key' in columns
        assert 'value' in columns
        assert 'updated_at' in columns

    def test_init_creates_agent_tasks_table(self, mock_env):
        """Test agent_tasks table structure"""
        from infra.tools.workflow.lib import init_sqlite
        from infra.tools.workflow.lib.db import DB_PATH

        init_sqlite()

        conn = sqlite3.connect(str(DB_PATH))
        columns = [col[1] for col in conn.execute("PRAGMA table_info(agent_tasks)").fetchall()]
        conn.close()

        assert 'task_id' in columns
        assert 'task_name' in columns
        assert 'agent' in columns
        assert 'status' in columns
        assert 'heartbeat_at' in columns
        assert 'dispatched_at' in columns


class TestAcquireLock:
    """Tests for _acquire_lock function"""

    def test_acquire_lock_returns_bool(self, mock_env):
        """Test _acquire_lock returns a boolean"""
        from infra.tools.workflow.lib import _acquire_lock

        result = _acquire_lock()
        assert isinstance(result, bool)
