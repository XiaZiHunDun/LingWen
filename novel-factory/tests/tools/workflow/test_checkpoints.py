"""Tests for infra.tools.workflow.lib.checkpoints (create/list/restore/delete).

Checkpoint layer: snapshot + restore state for crash recovery / rollback.
"""
import time


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
        from infra.tools.workflow.lib import create_checkpoint, list_checkpoints, set_state

        set_state("current_step", "STEP_20")
        create_checkpoint("State test")

        checkpoints = list_checkpoints()
        assert checkpoints[0]['step'] == "STEP_20"

    def test_create_checkpoint_multiple_checkpoints(self, init_db):
        """Test creating multiple checkpoints with unique IDs"""
        from infra.tools.workflow.lib import create_checkpoint, delete_checkpoint, list_checkpoints

        cp1 = create_checkpoint("First checkpoint")
        time.sleep(1.1)
        cp2 = create_checkpoint("Second checkpoint")

        checkpoints = list_checkpoints()
        assert len(checkpoints) >= 2

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
        from infra.tools.workflow.lib import create_checkpoint, delete_checkpoint, list_checkpoints

        cp1 = create_checkpoint("Older checkpoint - first")
        time.sleep(1.1)
        cp2 = create_checkpoint("Newer checkpoint - second")

        checkpoints = list_checkpoints()
        assert checkpoints[0]['note'] == "Newer checkpoint - second"

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
        from infra.tools.workflow.lib import create_checkpoint, get_state, restore_checkpoint, set_state

        set_state("current_step", "STEP_19")
        set_state("current_phase", "PHASE_7")
        cp_id = create_checkpoint("Restore me")

        set_state("current_step", "STEP_00")
        set_state("current_phase", "PHASE_0")

        restore_checkpoint(cp_id)

        assert get_state("current_step") == "STEP_19"
        assert get_state("current_phase") == "PHASE_7"

    def test_restore_checkpoint_clears_old_tasks(self, init_db):
        """Test restore_checkpoint clears existing tasks before restore"""
        from infra.tools.workflow.lib import (
            create_checkpoint,
            dispatch_task,
            list_tasks,
            restore_checkpoint,
            set_state,
        )

        set_state("current_step", "STEP_12")
        dispatch_task("old_task_1", "writer", "")
        dispatch_task("old_task_2", "writer", "")

        cp_id = create_checkpoint("Snapshot")

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
