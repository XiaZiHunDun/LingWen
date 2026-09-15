"""Tests for lingwen_workflow.events (trigger_event).

Events layer: decoupled pub/sub for workflow signals (STEP_COMPLETED, MANUAL_TRIGGER, etc).

trigger_event must never raise, even when EventBus is unavailable — this is
its primary contract, hence the two "does not raise" tests.
"""


class TestTriggerEvent:
    """Tests for trigger_event function"""

    def test_trigger_event_does_not_raise(self, init_db):
        """Test trigger_event doesn't raise even when EventBus unavailable"""
        from lingwen_workflow import trigger_event

        trigger_event("TEST_EVENT", source="test", data={"key": "value"})

    def test_trigger_event_accepts_kwargs(self, init_db):
        """Test trigger_event accepts keyword arguments"""
        from lingwen_workflow import trigger_event

        trigger_event("TEST_EVENT", arg1="value1", arg2="value2")
