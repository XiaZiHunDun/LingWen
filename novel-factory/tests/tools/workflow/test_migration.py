"""Tests for infra.tools.workflow.lib.migration (migrate_json_to_sqlite).

Migration layer: one-shot JSON → SQLite conversion for legacy workflow_state.json.
"""
import json


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

        data = {
            "simple_key": "simple_value",
            "complex_key": {"nested": "value", "list": [1, 2, 3]},
            "current_step": "STEP_01"
        }
        json_path = mock_env / "workflow_state.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        state_count, _ = migrate_json_to_sqlite()

        assert state_count >= 3
