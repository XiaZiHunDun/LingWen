from datetime import datetime, timezone
from ulid import ULID
from lingwen_storage.events.jsonl_store import WorkflowEvent
from lingwen_storage.events.reducer import reduce_events, WorkflowProjection


def _e(step: str, payload: dict, cid: str = "c1") -> WorkflowEvent:
    return WorkflowEvent(
        event_id=str(ULID()),
        occurred_at=datetime.now(timezone.utc),
        step=step,
        actor="test",
        correlation_id=cid,
        payload=payload,
    )


def test_empty_events_returns_initial():
    state = reduce_events([])
    assert state.chapter_count == 0
    assert state.current_step == "STEP_00"


def test_chapter_drafted_increments_count():
    e1 = _e("STEP_12", {"chapter_id": "ch001", "draft_path": "/tmp/c.md"})
    state = reduce_events([e1])
    assert "ch001" in state.chapters_drafted
    assert state.chapter_count == 1


def test_audit_appends_issues():
    e1 = _e("STEP_12", {"chapter_id": "ch001", "draft_path": "/tmp/c.md"})
    e2 = _e("STEP_15", {
        "chapter_id": "ch001",
        "issues": [{"severity": "P1", "category": "ai-trace"}],
    })
    state = reduce_events([e1, e2])
    assert state.audit_history["ch001"][0].severity == "P1"


def test_publish_adds_to_published():
    e1 = _e("STEP_21", {"chapter_id": "ch002"})
    state = reduce_events([e1])
    assert "ch002" in state.chapters_published


def test_publish_empty_cid_is_skipped():
    e1 = _e("STEP_21", {})
    state = reduce_events([e1])
    assert "" not in state.chapters_published
    assert len(state.chapters_published) == 0


def test_decision_appends_to_pending():
    e1 = _e("STEP_08", {"decision": {"choice": "A"}})
    state = reduce_events([e1])
    assert state.pending_decisions == [{"choice": "A"}]


def test_audit_missing_chapter_id_is_skipped():
    e1 = _e("STEP_15", {
        "issues": [{"severity": "P1", "category": "ai-trace"}],
    })
    state = reduce_events([e1])
    assert "" not in state.chapters_audited
    assert "" not in state.audit_history
    assert len(state.chapters_audited) == 0