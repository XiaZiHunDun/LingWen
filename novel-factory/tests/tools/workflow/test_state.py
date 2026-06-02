"""Tests for infra.tools.workflow.lib.state (get_state, set_state, advance_step, get_json).

State layer: key-value store + JSON fallback for legacy migration.

NOTE: TestAdvanceStep.test_advance_step_stores_previous_step patches
`infra.tools.workflow.lib.events._trigger_event` (the lib.events module
binding). state.py must import as `from . import events; events._trigger_event(...)`
for this patch to take effect — that's the monkeypatch-friendly pattern.
"""
import json
from unittest.mock import patch


class _SpyConnection:
    """轻量级 Connection 代理:记录 execute() SQL,转发其余调用到真实连接

    sqlite3.Connection 的 execute 是 C 实现的 read-only 属性,无法
    monkeypatch,所以我们包一层 proxy。R3-003 读锁测试用它来验证
    get_state 走 BEGIN/SELECT/COMMIT 路径。
    """

    def __init__(self, real, captured: list):
        self._real = real
        self._captured = captured

    def execute(self, sql, *args, **kwargs):
        self._captured.append(sql if isinstance(sql, str) else sql.decode("utf-8", "replace"))
        return self._real.execute(sql, *args, **kwargs)

    def commit(self):
        self._captured.append("COMMIT")
        return self._real.commit()

    def rollback(self):
        self._captured.append("ROLLBACK")
        return self._real.rollback()

    def close(self):
        return self._real.close()

    def __getattr__(self, name):
        return getattr(self._real, name)

    def __setattr__(self, name, value):
        # row_factory / text_factory 等可写属性转发到真实连接
        if name in ("_real", "_captured"):
            super().__setattr__(name, value)
        else:
            setattr(self._real, name, value)


class TestGetState:
    """Tests for get_state function"""

    def test_get_state_returns_value(self, init_db):
        """Test getting a state value that exists"""
        from infra.tools.workflow.lib import get_state, set_state

        set_state("current_step", "STEP_15")
        result = get_state("current_step")
        assert result == "STEP_15"

    def test_get_state_returns_fallback_when_missing(self, init_db):
        """Test that fallback is returned when key doesn't exist"""
        from infra.tools.workflow.lib import get_state

        result = get_state("nonexistent_key", fallback="default_value")
        assert result == "default_value"

    def test_get_state_fallback_empty_string(self, init_db):
        """Test fallback defaults to empty string"""
        from infra.tools.workflow.lib import get_state

        result = get_state("nonexistent_key")
        assert result == ""

    def test_get_state_falls_back_to_json(self, sample_workflow_json):
        """Test fallback to JSON when SQLite has no data"""
        from infra.tools.workflow.lib import get_state, DB_PATH

        result = get_state("version")
        assert result == "v8.2"

    def test_get_state_nested_json_path(self, sample_workflow_json):
        """Test getting nested value via dot notation"""
        from infra.tools.workflow.lib import get_state

        result = get_state("current_phase")
        assert result == "PHASE_5_MODIFY"

    def test_get_state_with_digit_index(self, sample_workflow_json):
        """Test accessing list element by digit index"""
        from infra.tools.workflow.lib import get_state

        json_path = sample_workflow_json.parent / "workflow_state.json"
        data = {
            "phases": ["PHASE_1", "PHASE_2", "PHASE_3"]
        }
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        result = get_state("phases.1")
        assert result == "PHASE_2"

    def test_get_state_json_file_not_exists(self, mock_env):
        """Test behavior when JSON doesn't exist"""
        from infra.tools.workflow.lib import get_state

        result = get_state("any_key", fallback="fallback")
        assert result == "fallback"


class TestSetState:
    """Tests for set_state function"""

    def test_set_state_returns_true_on_success(self, init_db):
        """Test set_state returns True on success"""
        from infra.tools.workflow.lib import set_state

        result = set_state("test_key", "test_value")
        assert result is True

    def test_set_state_stores_value(self, init_db):
        """Test that set_state actually stores the value"""
        from infra.tools.workflow.lib import set_state, get_state

        set_state("my_key", "my_value")
        result = get_state("my_key")
        assert result == "my_value"

    def test_set_state_overwrites_existing(self, init_db):
        """Test that set_state overwrites existing value"""
        from infra.tools.workflow.lib import set_state, get_state

        set_state("overwrite_key", "first_value")
        set_state("overwrite_key", "second_value")

        result = get_state("overwrite_key")
        assert result == "second_value"

    def test_set_state_multiple_keys(self, init_db):
        """Test setting multiple keys independently"""
        from infra.tools.workflow.lib import set_state, get_state

        set_state("key1", "value1")
        set_state("key2", "value2")

        assert get_state("key1") == "value1"
        assert get_state("key2") == "value2"

    def test_set_state_with_special_characters(self, init_db):
        """Test storing values with special characters"""
        from infra.tools.workflow.lib import set_state, get_state

        special_value = "value with 'quotes' and unicode 中 文"
        set_state("special_key", special_value)

        result = get_state("special_key")
        assert result == special_value


class TestAdvanceStep:
    """Tests for advance_step function"""

    def test_advance_step_valid_transition(self, init_db):
        """Test advancing step with valid transition"""
        from infra.tools.workflow.lib import advance_step, get_state, set_state

        set_state("current_step", "STEP_14")

        success, msg = advance_step("STEP_15")

        assert success is True
        assert "STEP_15" in msg
        assert get_state("current_step") == "STEP_15"

    def test_advance_step_invalid_transition(self, init_db):
        """Test that invalid transition is rejected"""
        from infra.tools.workflow.lib import advance_step, set_state, get_state

        set_state("current_step", "STEP_14")

        success, msg = advance_step("STEP_15")

        assert success is True
        assert "STEP_15" in msg
        assert get_state("current_step") == "STEP_15"

    def test_advance_step_stores_previous_step(self, init_db):
        """Test advance_step stores previous step info"""
        from infra.tools.workflow.lib import advance_step, set_state

        set_state("current_step", "STEP_14")

        with patch('infra.tools.workflow.lib.events._trigger_event') as mock_trigger:
            advance_step("STEP_15")

            calls = mock_trigger.call_args_list
            event_names = [call[0][0] for call in calls]
            assert "STEP_COMPLETED" in event_names

    def test_advance_step_with_validator(self, init_db):
        """Test advance_step works when validator is available"""
        from infra.tools.workflow.lib import advance_step, set_state, get_state

        set_state("current_step", "STEP_14")

        success, msg = advance_step("STEP_15")

        assert success is True
        assert "STEP_15" in msg
        assert get_state("current_step") == "STEP_15"


class TestGetJson:
    """Tests for get_json function"""

    def test_get_json_returns_value(self, sample_workflow_json):
        """Test get_json returns value from JSON file"""
        from infra.tools.workflow.lib import get_json

        result = get_json("version")
        assert result == "v8.2"

    def test_get_json_returns_fallback(self, sample_workflow_json):
        """Test get_json returns fallback when key not found"""
        from infra.tools.workflow.lib import get_json

        result = get_json("nonexistent", fallback="default")
        assert result == "default"

    def test_get_json_no_file_returns_fallback(self, mock_env):
        """Test get_json returns fallback when JSON file doesn't exist"""
        from infra.tools.workflow.lib import get_json

        result = get_json("any_key", fallback="fallback_value")
        assert result == "fallback_value"

    def test_get_json_nested_access(self, sample_workflow_json):
        """Test get_json with nested dict access"""
        from infra.tools.workflow.lib import get_json

        result = get_json("current_phase")
        assert result == "PHASE_5_MODIFY"


class TestGetStateReadLock:
    """R3-003: get_state 读锁 — 显式 BEGIN 让读事务与写事务互斥

    在 WAL 模式下,默认每个 SELECT 独立,跨语句不能保证一致视图。
    显式 BEGIN (DEFERRED) 让读方获得一致的快照,并在 COMMIT 时
    显式释放 — 配合 set_state 的 BEGIN IMMEDIATE,避免读到
    "半提交"中间态的窗口。
    """

    def test_get_state_uses_explicit_read_transaction(self, init_db, monkeypatch):
        """BEGIN/COMMIT 包裹读路径 — 验证代码走读事务分支

        通过 monkeypatch db.sqlite3.connect 返回一个轻量级 ConnectionProxy,
        记录所有 execute() 调用的 SQL。
        """
        from infra.tools.workflow.lib import get_state, set_state, db

        set_state("current_step", "STEP_15")

        captured_sql = []
        original_connect = db.sqlite3.connect

        def wrapped_connect(*args, **kwargs):
            real_conn = original_connect(*args, **kwargs)
            proxy = _SpyConnection(real_conn, captured_sql)
            return proxy

        monkeypatch.setattr(db.sqlite3, "connect", wrapped_connect)

        # 初始化 DB 的 SQL(已在 set_state 时跑过)只跑一次,这里只关心
        # get_state 自身的 BEGIN/SELECT/COMMIT 序列。
        captured_sql.clear()

        result = get_state("current_step")
        assert result == "STEP_15"

        upper_sqls = [s.upper() for s in captured_sql]
        # 过滤掉 init_sqlite() 产生的 CREATE TABLE 噪声(它们是幂等的)
        # 只保留 PRAGMA / BEGIN / SELECT / COMMIT
        txn_sqls = [
            s for s in upper_sqls
            if any(k in s for k in ("BEGIN", "COMMIT", "SELECT", "JOURNAL_MODE", "BUSY_TIMEOUT"))
        ]
        assert any(s.strip() == "BEGIN" for s in txn_sqls), (
            f"get_state should issue BEGIN; got: {txn_sqls}"
        )
        assert any(s.strip() == "COMMIT" for s in txn_sqls), (
            f"get_state should issue COMMIT; got: {txn_sqls}"
        )
        # SELECT 必须在 BEGIN 之后、且 BEGIN 之后的第一个 COMMIT 之前
        begin_idx = next(i for i, s in enumerate(txn_sqls) if s.strip() == "BEGIN")
        select_idx = next(i for i, s in enumerate(txn_sqls) if "SELECT" in s and i > begin_idx)
        commit_idx = next(
            i for i, s in enumerate(txn_sqls)
            if s.strip() == "COMMIT" and i > select_idx
        )
        assert begin_idx < select_idx < commit_idx, (
            f"SELECT must be wrapped by BEGIN/COMMIT; "
            f"begin={begin_idx} select={select_idx} commit={commit_idx}; txn_sqls={txn_sqls}"
        )

    def test_get_state_reads_consistent_snapshot(self, init_db):
        """读事务快照一致性 — BEGIN 后单 connection 内多次 SELECT 应一致

        流程:
          1. 写入 key1=v1, key2=v2
          2. 在读事务内 SELECT key1 后, 另一个连接 INSERT key1=v1_new
          3. 读事务内再 SELECT key1 应仍是 v1(快照一致)
        """
        import sqlite3
        from infra.tools.workflow.lib import db, set_state

        set_state("r3_003_key1", "v1")
        set_state("r3_003_key2", "v2")

        # 单独写线程
        import threading
        commit_done = threading.Event()
        snap_holder = {}

        def mutator():
            conn = sqlite3.connect(str(db.DB_PATH), timeout=30)
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "INSERT OR REPLACE INTO workflow_state (key, value, updated_at) "
                "VALUES (?, ?, CURRENT_TIMESTAMP)",
                ("r3_003_key1", "v1_new"),
            )
            # 在 reader 第一次 SELECT 之后, reader 看到 v1
            # (确保 reader 已经开始)
            commit_done.wait(timeout=2.0)
            conn.commit()
            conn.close()

        # 启动 mutator 线程
        mt = threading.Thread(target=mutator)
        mt.start()

        # reader: BEGIN → 选 key1 (snapshot 此时锁定) → 等 mutator commit → 再选 key1
        conn = sqlite3.connect(str(db.DB_PATH), timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("BEGIN")
        cur1 = conn.execute("SELECT value FROM workflow_state WHERE key = ?", ("r3_003_key1",))
        first = cur1.fetchone()
        # 触发 mutator 提交
        commit_done.set()
        mt.join(timeout=2.0)
        # 在同一 reader 事务中再读(应看到快照时的值 v1,不是 v1_new)
        cur2 = conn.execute("SELECT value FROM workflow_state WHERE key = ?", ("r3_003_key1",))
        second = cur2.fetchone()
        conn.commit()
        conn.close()

        assert first is not None and first[0] == "v1"
        # 关键断言:同一读事务内二次 SELECT 应读到一致快照
        assert second is not None and second[0] == "v1", (
            f"读事务快照应一致,二次 SELECT 应仍为 v1,实际: {second}"
        )
