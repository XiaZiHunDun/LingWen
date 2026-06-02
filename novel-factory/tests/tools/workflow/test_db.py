"""Tests for infra.tools.workflow.lib.db (init_sqlite, _acquire_lock).

Lowest-layer tests: DB schema + flock lock. These exercise the foundation
that state/tasks/checkpoints all depend on.
"""
import sqlite3


class TestInitSqlite:
    """Tests for init_sqlite function"""

    def test_init_creates_tables(self, mock_env):
        """Test that init_sqlite creates all required tables"""
        from infra.tools.workflow.lib import init_sqlite, DB_PATH

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
        from infra.tools.workflow.lib import init_sqlite, DB_PATH

        init_sqlite()

        conn = sqlite3.connect(str(DB_PATH))
        columns = [col[1] for col in conn.execute("PRAGMA table_info(workflow_state)").fetchall()]
        conn.close()

        assert 'key' in columns
        assert 'value' in columns
        assert 'updated_at' in columns

    def test_init_creates_agent_tasks_table(self, mock_env):
        """Test agent_tasks table structure"""
        from infra.tools.workflow.lib import init_sqlite, DB_PATH

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
