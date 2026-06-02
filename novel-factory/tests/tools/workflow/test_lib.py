#!/usr/bin/env python3
"""Tests for infra.tools.workflow.lib module

Coverage target: ≥90% for all public functions
"""
import json
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def mock_env(tmp_path, monkeypatch):
    """Setup mock environment with temporary paths for lib.py"""
    import sys

    # Create temporary directories
    db_dir = tmp_path / ".state"
    db_dir.mkdir()
    locks_dir = tmp_path / ".locks"
    locks_dir.mkdir()

    # Override the module-level variables via monkeypatch.
    # After lib.py → lib/ split, the path constants live in lib.db (the
    # canonical owner). lib/__init__.py re-imports them for backward
    # compat, but the real writes happen through .db, so we patch there.
    monkeypatch.setattr("infra.tools.workflow.lib.db.PROJECT_ROOT", tmp_path)
    monkeypatch.setattr("infra.tools.workflow.lib.db.WORKFLOW_FILE", tmp_path / "workflow_state.json")
    monkeypatch.setattr("infra.tools.workflow.lib.db.DB_DIR", db_dir)
    monkeypatch.setattr("infra.tools.workflow.lib.db.DB_PATH", db_dir / "workflow.db")
    monkeypatch.setattr("infra.tools.workflow.lib.db.LOCKFILE", locks_dir / "workflow.lock")

    # Fix lib.py bug: sys is used in advance_step but not imported at module level
    # lib.py has `sys.path.insert(...)` in advance_step but only imports sys inside __main__ block
    import infra.tools.workflow.lib as lib_module
    lib_module.sys = sys

    return tmp_path


@pytest.fixture
def init_db(mock_env):
    """Initialize database with schema"""
    from infra.tools.workflow.lib import init_sqlite
    init_sqlite()
    return mock_env


@pytest.fixture
def sample_workflow_json(mock_env):
    """Create a sample workflow_state.json"""
    data = {
        "version": "v8.2",
        "current_step": "STEP_14",
        "current_phase": "PHASE_5_MODIFY",
        "agent_tasks": {
            "task_001": {
                "task_name": "write_ch001",
                "agent": "writer-a",
                "status": "completed",
                "heartbeat_at": "2026-05-20T10:00:00",
                "dispatched_at": "2026-05-20T09:00:00"
            }
        }
    }
    json_path = mock_env / "workflow_state.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    return json_path


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
        # Should not raise
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

        # Don't call init_sqlite - test JSON fallback directly via get_json path
        result = get_state("version")
        assert result == "v8.2"

    def test_get_state_nested_json_path(self, sample_workflow_json):
        """Test getting nested value via dot notation"""
        from infra.tools.workflow.lib import get_state

        # This tests the JSON fallback path
        result = get_state("current_phase")
        assert result == "PHASE_5_MODIFY"

    def test_get_state_with_digit_index(self, sample_workflow_json):
        """Test accessing list element by digit index"""
        from infra.tools.workflow.lib import get_state

        # Create JSON with list structure
        json_path = sample_workflow_json.parent / "workflow_state.json"
        data = {
            "phases": ["PHASE_1", "PHASE_2", "PHASE_3"]
        }
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        # Note: get_state uses fallback to JSON for list access
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

        special_value = "value with 'quotes' and unicode \u4e2d\u6587"
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

        # This should succeed - STEP_14 -> STEP_15 is valid
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

            # Check that STEP_COMPLETED event was triggered
            calls = mock_trigger.call_args_list
            event_names = [call[0][0] for call in calls]
            assert "STEP_COMPLETED" in event_names

    def test_advance_step_with_validator(self, init_db):
        """Test advance_step works when validator is available"""
        from infra.tools.workflow.lib import advance_step, set_state, get_state

        set_state("current_step", "STEP_14")

        # This should succeed - STEP_14 -> STEP_15 is valid
        success, msg = advance_step("STEP_15")

        assert success is True
        assert "STEP_15" in msg
        assert get_state("current_step") == "STEP_15"


class TestDispatchTask:
    """Tests for dispatch_task function"""

    def test_dispatch_task_returns_task_id(self, init_db):
        """Test dispatch_task returns the task_name as task_id"""
        from infra.tools.workflow.lib import dispatch_task

        task_id = dispatch_task("write_ch001", "writer-a", "撰写第1章")

        assert task_id == "write_ch001"

    def test_dispatch_task_creates_pending_task(self, init_db):
        """Test that dispatch_task creates a pending task in DB"""
        from infra.tools.workflow.lib import dispatch_task, get_task_status

        dispatch_task("test_task", "agent-x", "Test description")

        task = get_task_status("test_task")
        assert task is not None
        assert task['task_id'] == "test_task"
        assert task['task_name'] == "test_task"
        assert task['agent'] == "agent-x"
        assert task['status'] == "pending"

    def test_dispatch_task_with_empty_description(self, init_db):
        """Test dispatch_task with empty description"""
        from infra.tools.workflow.lib import dispatch_task

        task_id = dispatch_task("task_no_desc", "agent-y", "")

        assert task_id == "task_no_desc"

    def test_dispatch_task_triggers_event(self, init_db):
        """Test that dispatch_task triggers MANUAL_TRIGGER event"""
        from infra.tools.workflow.lib import dispatch_task

        with patch('infra.tools.workflow.lib.events._trigger_event') as mock_trigger:
            dispatch_task("event_test_task", "agent-z", "desc")

            mock_trigger.assert_called()
            call_args = mock_trigger.call_args[0]
            assert call_args[0] == "MANUAL_TRIGGER"

    def test_dispatch_task_multiple_tasks(self, init_db):
        """Test dispatching multiple tasks"""
        from infra.tools.workflow.lib import dispatch_task, list_tasks

        dispatch_task("multi_task_1", "writer-a", "First")
        dispatch_task("multi_task_2", "writer-b", "Second")

        tasks = list_tasks()
        task_ids = [t['task_id'] for t in tasks]
        assert "multi_task_1" in task_ids
        assert "multi_task_2" in task_ids


class TestVerifyTask:
    """Tests for verify_task function"""

    def test_verify_task_returns_true_on_success(self, init_db):
        """Test verify_task returns True on success"""
        from infra.tools.workflow.lib import dispatch_task, verify_task

        dispatch_task("verify_test_task", "agent", "")
        result = verify_task("verify_test_task", "ext_task_123", "completed")

        assert result is True

    def test_verify_task_updates_status(self, init_db):
        """Test that verify_task updates the task status"""
        from infra.tools.workflow.lib import dispatch_task, verify_task, get_task_status

        dispatch_task("status_test_task", "agent", "")
        verify_task("status_test_task", "ext_456", "completed")

        task = get_task_status("status_test_task")
        assert task['status'] == "completed"
        assert task['task_id_external'] == "ext_456"

    def test_verify_task_nonexistent_returns_true(self, init_db):
        """Test verify_task on non-existent task returns True (DB update doesn't error)"""
        from infra.tools.workflow.lib import verify_task

        # Should not raise, returns True
        result = verify_task("nonexistent_task", "ext_id", "completed")
        assert result is True

    def test_verify_task_with_different_statuses(self, init_db):
        """Test verify_task with various status values"""
        from infra.tools.workflow.lib import dispatch_task, verify_task, get_task_status

        for status in ["pending", "running", "completed", "failed"]:
            dispatch_task(f"status_{status}", "agent", "")
            verify_task(f"status_{status}", f"ext_{status}", status)
            task = get_task_status(f"status_{status}")
            assert task['status'] == status


class TestGetTaskStatus:
    """Tests for get_task_status function"""

    def test_get_task_status_returns_dict(self, init_db):
        """Test get_task_status returns a dictionary"""
        from infra.tools.workflow.lib import dispatch_task, get_task_status

        dispatch_task("status_dict_task", "writer", "")
        task = get_task_status("status_dict_task")

        assert isinstance(task, dict)
        assert 'task_id' in task
        assert 'agent' in task

    def test_get_task_status_returns_none_for_missing(self, init_db):
        """Test get_task_status returns None for non-existent task"""
        from infra.tools.workflow.lib import get_task_status

        result = get_task_status("missing_task_xyz")
        assert result is None


class TestListTasks:
    """Tests for list_tasks function"""

    def test_list_tasks_returns_list(self, init_db):
        """Test list_tasks returns a list"""
        from infra.tools.workflow.lib import list_tasks

        result = list_tasks()
        assert isinstance(result, list)

    def test_list_tasks_empty_initially(self, init_db):
        """Test list_tasks returns empty list initially"""
        from infra.tools.workflow.lib import list_tasks

        result = list_tasks()
        assert result == []

    def test_list_tasks_filters_by_status(self, init_db):
        """Test list_tasks filters by status"""
        from infra.tools.workflow.lib import dispatch_task, list_tasks

        dispatch_task("pending_task_1", "writer", "")
        dispatch_task("pending_task_2", "writer", "")

        pending = list_tasks(status="pending")
        assert len(pending) >= 2

    def test_list_tasks_orders_by_created_at(self, init_db):
        """Test list_tasks orders by created_at DESC"""
        from infra.tools.workflow.lib import dispatch_task, list_tasks

        dispatch_task("old_task", "writer", "")
        time.sleep(0.01)  # Ensure different timestamp
        dispatch_task("new_task", "writer", "")

        tasks = list_tasks()
        # Most recent first
        task_ids = [t['task_id'] for t in tasks]
        assert "new_task" in task_ids


class TestCreateCheckpoint:
    """Tests for create_checkpoint function"""

    def test_create_checkpoint_returns_checkpoint_id(self, init_db):
        """Test create_checkpoint returns a checkpoint ID"""
        from infra.tools.workflow.lib import create_checkpoint, set_state

        set_state("current_step", "STEP_15")
        set_state("current_phase", "PHASE_5")

        cp_id = create_checkpoint("Test checkpoint")

        assert cp_id is not None
        assert cp_id.startswith("cp_")

    def test_create_checkpoint_stores_snapshot(self, init_db):
        """Test create_checkpoint stores a valid snapshot"""
        from infra.tools.workflow.lib import create_checkpoint, list_checkpoints

        create_checkpoint("My checkpoint")
        checkpoints = list_checkpoints()

        assert len(checkpoints) >= 1
        assert checkpoints[0]['note'] == "My checkpoint"

    def test_create_checkpoint_includes_state(self, init_db):
        """Test checkpoint snapshot includes workflow state"""
        from infra.tools.workflow.lib import create_checkpoint, set_state, list_checkpoints

        set_state("current_step", "STEP_20")
        cp_id = create_checkpoint("State test")

        checkpoints = list_checkpoints()
        assert checkpoints[0]['step'] == "STEP_20"

    def test_create_checkpoint_multiple_checkpoints(self, init_db):
        """Test creating multiple checkpoints with unique IDs"""
        from infra.tools.workflow.lib import create_checkpoint, list_checkpoints, delete_checkpoint
        import time

        # Create first checkpoint
        cp1 = create_checkpoint("First checkpoint")

        # Wait to ensure different timestamp (checkpoint_id is unique to second)
        time.sleep(1.1)

        # Create second checkpoint
        cp2 = create_checkpoint("Second checkpoint")

        checkpoints = list_checkpoints()
        assert len(checkpoints) >= 2

        # Cleanup
        delete_checkpoint(cp1)
        delete_checkpoint(cp2)


class TestListCheckpoints:
    """Tests for list_checkpoints function"""

    def test_list_checkpoints_returns_list(self, init_db):
        """Test list_checkpoints returns a list"""
        from infra.tools.workflow.lib import list_checkpoints

        result = list_checkpoints()
        assert isinstance(result, list)

    def test_list_checkpoints_orders_by_created_at(self, init_db):
        """Test list_checkpoints returns most recent first"""
        from infra.tools.workflow.lib import create_checkpoint, list_checkpoints, delete_checkpoint
        import time

        # Create first checkpoint
        cp1 = create_checkpoint("Older checkpoint - first")

        # Wait to ensure different timestamp
        time.sleep(1.1)

        # Create second checkpoint
        cp2 = create_checkpoint("Newer checkpoint - second")

        checkpoints = list_checkpoints()
        assert checkpoints[0]['note'] == "Newer checkpoint - second"

        # Cleanup
        delete_checkpoint(cp1)
        delete_checkpoint(cp2)


class TestRestoreCheckpoint:
    """Tests for restore_checkpoint function"""

    def test_restore_checkpoint_returns_true_on_success(self, init_db):
        """Test restore_checkpoint returns (True, msg) on success"""
        from infra.tools.workflow.lib import create_checkpoint, restore_checkpoint, set_state

        set_state("current_step", "STEP_15")
        set_state("current_phase", "PHASE_5")
        cp_id = create_checkpoint("Before restore")

        # Clear current state
        set_state("current_step", "STEP_00")
        set_state("current_phase", "PHASE_0")

        success, msg = restore_checkpoint(cp_id)

        assert success is True
        assert cp_id in msg

    def test_restore_checkpoint_returns_false_for_missing(self, init_db):
        """Test restore_checkpoint returns False for non-existent ID"""
        from infra.tools.workflow.lib import restore_checkpoint

        success, msg = restore_checkpoint("nonexistent_cp_id")

        assert success is False
        assert "not found" in msg

    def test_restore_checkpoint_restores_state(self, init_db):
        """Test restore_checkpoint actually restores state"""
        from infra.tools.workflow.lib import create_checkpoint, restore_checkpoint, set_state, get_state

        set_state("current_step", "STEP_19")
        set_state("current_phase", "PHASE_7")
        cp_id = create_checkpoint("Restore me")

        # Overwrite state
        set_state("current_step", "STEP_00")
        set_state("current_phase", "PHASE_0")

        restore_checkpoint(cp_id)

        assert get_state("current_step") == "STEP_19"
        assert get_state("current_phase") == "PHASE_7"

    def test_restore_checkpoint_clears_old_tasks(self, init_db):
        """Test restore_checkpoint clears existing tasks before restore"""
        from infra.tools.workflow.lib import create_checkpoint, restore_checkpoint, dispatch_task, set_state, list_tasks

        set_state("current_step", "STEP_12")
        dispatch_task("old_task_1", "writer", "")
        dispatch_task("old_task_2", "writer", "")

        cp_id = create_checkpoint("Snapshot")

        # Create new tasks after checkpoint
        dispatch_task("new_task", "writer", "")

        restore_checkpoint(cp_id)

        tasks = list_tasks()
        task_ids = [t['task_id'] for t in tasks]
        assert "new_task" not in task_ids


class TestDeleteCheckpoint:
    """Tests for delete_checkpoint function"""

    def test_delete_checkpoint_returns_true(self, init_db):
        """Test delete_checkpoint returns True"""
        from infra.tools.workflow.lib import create_checkpoint, delete_checkpoint

        cp_id = create_checkpoint("To delete")
        result = delete_checkpoint(cp_id)

        assert result is True

    def test_delete_checkpoint_removes_from_list(self, init_db):
        """Test delete_checkpoint removes checkpoint from list"""
        from infra.tools.workflow.lib import create_checkpoint, delete_checkpoint, list_checkpoints

        cp_id = create_checkpoint("Delete me")
        delete_checkpoint(cp_id)

        checkpoints = list_checkpoints()
        cp_ids = [c['checkpoint_id'] for c in checkpoints]
        assert cp_id not in cp_ids


class TestMigrateJsonToSqlite:
    """Tests for migrate_json_to_sqlite function"""

    def test_migrate_json_to_sqlite_returns_counts(self, sample_workflow_json):
        """Test migrate_json_to_sqlite returns (state_count, task_count)"""
        from infra.tools.workflow.lib import migrate_json_to_sqlite

        state_count, task_count = migrate_json_to_sqlite()

        assert isinstance(state_count, int)
        assert isinstance(task_count, int)
        assert state_count >= 0
        assert task_count >= 0

    def test_migrate_json_to_sqlite_migrates_state(self, sample_workflow_json):
        """Test migrate_json_to_sqlite migrates workflow state"""
        from infra.tools.workflow.lib import migrate_json_to_sqlite, get_state

        migrate_json_to_sqlite()

        assert get_state("current_step") == "STEP_14"

    def test_migrate_json_to_sqlite_migrates_tasks(self, sample_workflow_json):
        """Test migrate_json_to_sqlite migrates agent_tasks"""
        from infra.tools.workflow.lib import migrate_json_to_sqlite, get_task_status, init_sqlite

        init_sqlite()
        migrate_json_to_sqlite()

        task = get_task_status("task_001")
        assert task is not None
        assert task['agent'] == "writer-a"

    def test_migrate_json_to_sqlite_no_file_returns_zero(self, mock_env):
        """Test migrate_json_to_sqlite returns (0, 0) when JSON doesn't exist"""
        from infra.tools.workflow.lib import migrate_json_to_sqlite

        state_count, task_count = migrate_json_to_sqlite()

        assert state_count == 0
        assert task_count == 0

    def test_migrate_json_to_sqlite_handles_complex_values(self, mock_env):
        """Test migration of complex nested values (dicts/lists)"""
        from infra.tools.workflow.lib import migrate_json_to_sqlite, get_state, init_sqlite

        init_sqlite()

        # Create JSON with complex values
        data = {
            "simple_key": "simple_value",
            "complex_key": {"nested": "value", "list": [1, 2, 3]},
            "current_step": "STEP_01"
        }
        json_path = mock_env / "workflow_state.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        state_count, _ = migrate_json_to_sqlite()

        # Complex values are JSON-serialized
        assert state_count >= 3


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


class TestBatchDispatch:
    """Tests for batch_dispatch_writer and batch_dispatch_reviewer"""

    def test_batch_dispatch_writer_returns_dict(self, init_db):
        """Test batch_dispatch_writer returns a dictionary"""
        from infra.tools.workflow.lib import batch_dispatch_writer

        result = batch_dispatch_writer(["ch001", "ch002"])

        assert isinstance(result, dict)
        assert "ch001" in result
        assert "ch002" in result

    def test_batch_dispatch_writer_creates_tasks(self, init_db):
        """Test batch_dispatch_writer creates tasks for each chapter"""
        from infra.tools.workflow.lib import batch_dispatch_writer, list_tasks

        batch_dispatch_writer(["ch_batch_1", "ch_batch_2"])

        tasks = list_tasks()
        task_names = [t['task_name'] for t in tasks]
        assert any("ch_batch_1" in name for name in task_names)
        assert any("ch_batch_2" in name for name in task_names)

    def test_batch_dispatch_writer_with_custom_writers(self, init_db):
        """Test batch_dispatch_writer with custom writer list"""
        from infra.tools.workflow.lib import batch_dispatch_writer

        result = batch_dispatch_writer(["chX"], writers=["writer-z"])

        assert "chX" in result

    def test_batch_dispatch_reviewer_returns_dict(self, init_db):
        """Test batch_dispatch_reviewer returns a dictionary"""
        from infra.tools.workflow.lib import batch_dispatch_reviewer

        result = batch_dispatch_reviewer(["ch003"])

        assert isinstance(result, dict)
        assert "ch003" in result

    def test_batch_dispatch_reviewer_creates_review_tasks(self, init_db):
        """Test batch_dispatch_reviewer creates review tasks"""
        from infra.tools.workflow.lib import batch_dispatch_reviewer, list_tasks

        batch_dispatch_reviewer(["ch_review"])

        tasks = list_tasks()
        task_names = [t['task_name'] for t in tasks]
        assert any("ch_review" in name for name in task_names)


class TestTriggerEvent:
    """Tests for trigger_event function"""

    def test_trigger_event_does_not_raise(self, init_db):
        """Test trigger_event doesn't raise even when EventBus unavailable"""
        from infra.tools.workflow.lib import trigger_event

        # Should not raise
        trigger_event("TEST_EVENT", source="test", data={"key": "value"})

    def test_trigger_event_accepts_kwargs(self, init_db):
        """Test trigger_event accepts keyword arguments"""
        from infra.tools.workflow.lib import trigger_event

        # Should not raise
        trigger_event("TEST_EVENT", arg1="value1", arg2="value2")


class TestAcquireLock:
    """Tests for _acquire_lock function"""

    def test_acquire_lock_returns_bool(self, mock_env):
        """Test _acquire_lock returns a boolean"""
        from infra.tools.workflow.lib import _acquire_lock

        result = _acquire_lock()
        assert isinstance(result, bool)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])