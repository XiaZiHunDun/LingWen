"""Phase 102: notifications record_failure/record_success + threshold warning emit.

I095 invariant: _consecutive_failures state is maintained only via these helpers.
Threshold crossing emits EXACTLY ONE severity=warning notification; counter stays
elevated until record_success() resets it.

Phase 104: counter keys widened to (project_slug, event_type) tuples (I095 EXTENDED).
All assertions below use tuple keys.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from lingwen_illustrations import notifications
from lingwen_illustrations.notifications import (
    _consecutive_failures,
    record_failure,
    record_success,
)

# Phase 104: counter keys are (slug, event_type) tuples. Test helper for the
# canonical "generation" event_type used by Phase 102 generation pipeline.
EVENT = "generation"


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    """Reset module-level state dicts between tests (I095 isolation)."""
    _consecutive_failures.clear()
    notifications._warning_emitted.clear()


def test_record_failure_increments_counter() -> None:
    record_failure("proj-a", RuntimeError("oops"), project_root=Path("/tmp"), threshold=3, event_type=EVENT)
    assert _consecutive_failures[("proj-a", EVENT)] == 1
    record_failure("proj-a", RuntimeError("oops"), project_root=Path("/tmp"), threshold=3, event_type=EVENT)
    assert _consecutive_failures[("proj-a", EVENT)] == 2


def test_record_success_resets_counter() -> None:
    record_failure("proj-a", RuntimeError("oops"), project_root=Path("/tmp"), threshold=3, event_type=EVENT)
    record_failure("proj-a", RuntimeError("oops"), project_root=Path("/tmp"), threshold=3, event_type=EVENT)
    assert _consecutive_failures[("proj-a", EVENT)] == 2
    record_success("proj-a", EVENT)
    assert _consecutive_failures.get(("proj-a", EVENT), 0) == 0


def test_record_success_when_count_zero_noop() -> None:
    """No negative counter; record_success on zero is safe."""
    record_success("proj-a", EVENT)
    assert _consecutive_failures.get(("proj-a", EVENT), 0) == 0


def test_threshold_emit_warning_on_cross(monkeypatch) -> None:
    """count >= threshold emits 1 warning notification via publish()."""
    captured: list[notifications.NotificationEvent] = []
    monkeypatch.setattr(notifications, "publish", lambda ev: captured.append(ev))
    monkeypatch.setattr(
        notifications, "audit_log",
        MagicMock(record_event=MagicMock()),
    )

    record_failure("proj-a", RuntimeError("e1"), project_root=Path("/tmp"), threshold=3, event_type=EVENT)
    record_failure("proj-a", RuntimeError("e2"), project_root=Path("/tmp"), threshold=3, event_type=EVENT)
    record_failure("proj-a", RuntimeError("e3"), project_root=Path("/tmp"), threshold=3, event_type=EVENT)

    assert len(captured) == 1
    assert captured[0].severity == "warning"
    assert captured[0].extra["consecutive_failures"] == 3
    assert captured[0].extra["last_error"] == "e3"


def test_below_threshold_no_warning(monkeypatch) -> None:
    """count < threshold → no publish() call."""
    captured: list[notifications.NotificationEvent] = []
    monkeypatch.setattr(notifications, "publish", lambda ev: captured.append(ev))
    monkeypatch.setattr(
        notifications, "audit_log",
        MagicMock(record_event=MagicMock()),
    )

    record_failure("proj-a", RuntimeError("e1"), project_root=Path("/tmp"), threshold=3, event_type=EVENT)
    record_failure("proj-a", RuntimeError("e2"), project_root=Path("/tmp"), threshold=3, event_type=EVENT)
    assert len(captured) == 0


def test_threshold_one_emits_on_first_failure(monkeypatch) -> None:
    """threshold=1 → first failure emits."""
    captured: list[notifications.NotificationEvent] = []
    monkeypatch.setattr(notifications, "publish", lambda ev: captured.append(ev))
    monkeypatch.setattr(
        notifications, "audit_log",
        MagicMock(record_event=MagicMock()),
    )

    record_failure("proj-a", RuntimeError("e1"), project_root=Path("/tmp"), threshold=1, event_type=EVENT)
    assert len(captured) == 1


def test_warning_idempotent_until_reset(monkeypatch) -> None:
    """After threshold cross, additional failures do NOT re-emit until reset."""
    captured: list[notifications.NotificationEvent] = []
    monkeypatch.setattr(notifications, "publish", lambda ev: captured.append(ev))
    monkeypatch.setattr(
        notifications, "audit_log",
        MagicMock(record_event=MagicMock()),
    )

    for i in range(5):
        record_failure(
            "proj-a", RuntimeError(f"e{i}"),
            project_root=Path("/tmp"), threshold=3, event_type=EVENT,
        )
    assert len(captured) == 1  # only 1 warning, despite 5 failures
    assert _consecutive_failures[("proj-a", EVENT)] == 5  # counter stays elevated


def test_per_project_isolation() -> None:
    """Different project_slugs have independent counters."""
    record_failure("proj-a", RuntimeError("e"), project_root=Path("/tmp"), threshold=3, event_type=EVENT)
    record_failure("proj-b", RuntimeError("e"), project_root=Path("/tmp"), threshold=3, event_type=EVENT)
    record_failure("proj-b", RuntimeError("e"), project_root=Path("/tmp"), threshold=3, event_type=EVENT)
    assert _consecutive_failures[("proj-a", EVENT)] == 1
    assert _consecutive_failures[("proj-b", EVENT)] == 2


def test_record_failure_unknown_project_slug_does_not_crash() -> None:
    """record_failure for project_slug not in counters → no-op safety."""
    assert ("never-seen", EVENT) not in _consecutive_failures
    record_failure("never-seen", RuntimeError("e"), project_root=Path("/tmp"), threshold=3, event_type=EVENT)
    assert _consecutive_failures[("never-seen", EVENT)] == 1
