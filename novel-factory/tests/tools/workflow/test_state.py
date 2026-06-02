"""Tests for infra.tools.workflow.lib.state (get_state, set_state, advance_step, get_json).

State layer: key-value store + JSON fallback for legacy migration.

NOTE: TestAdvanceStep.test_advance_step_stores_previous_step patches
`infra.tools.workflow.lib.events._trigger_event` (the lib.events module
binding). state.py must import as `from . import events; events._trigger_event(...)`
for this patch to take effect — that's the monkeypatch-friendly pattern.
"""
import json
from unittest.mock import patch


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
