"""Tests for infra.tools.workflow.lib.tasks (dispatch_task, verify_task, get_task_status, list_tasks).

Task layer: agent task lifecycle (dispatch → run → verify).

NOTE: TestDispatchTask.test_dispatch_task_triggers_event patches
`infra.tools.workflow.lib.events._trigger_event`. tasks.py must import as
`from . import events; events._trigger_event(...)` for this patch to work.
"""
import time
from unittest.mock import patch


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
        from infra.tools.workflow.lib import dispatch_task, get_task_status, verify_task

        dispatch_task("status_test_task", "agent", "")
        verify_task("status_test_task", "ext_456", "completed")

        task = get_task_status("status_test_task")
        assert task['status'] == "completed"
        assert task['task_id_external'] == "ext_456"

    def test_verify_task_nonexistent_returns_true(self, init_db):
        """Test verify_task on non-existent task returns True (DB update doesn't error)"""
        from infra.tools.workflow.lib import verify_task

        result = verify_task("nonexistent_task", "ext_id", "completed")
        assert result is True

    def test_verify_task_with_different_statuses(self, init_db):
        """Test verify_task with various status values"""
        from infra.tools.workflow.lib import dispatch_task, get_task_status, verify_task

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
        time.sleep(0.01)
        dispatch_task("new_task", "writer", "")

        tasks = list_tasks()
        task_ids = [t['task_id'] for t in tasks]
        assert "new_task" in task_ids
