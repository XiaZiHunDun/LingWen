"""Phase 105 — Counter isolation + helper relocation + back-compat tests.

3 NEW tests (T7-T9) covering:

T7: 3 cleanup failures do NOT increment generation counter (counter isolation).
T8: notifications.resolve_threshold exists and returns expected values for all event types.
T9: pipeline._resolve_threshold still callable (back-compat re-export from Phase 105 relocation).

These tests verify Phase 105 architectural invariants without modifying behavior.
Each test uses a unique slug to avoid in-memory counter bleed.
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest


def test_t7_cleanup_failures_do_not_increment_generation_counter():
    """Phase 104 invariant: failures in different event types do NOT bleed.

    3 record_failure(slug, ..., event_type='cleanup') calls must leave the
    generation counter at 0.
    """
    from lingwen_illustrations import notifications

    slug = "phase105-t7-isolation"
    error = RuntimeError("test")

    # Trigger 3 cleanup failures
    for _ in range(3):
        notifications.record_failure(
            slug, error,
            project_root=None,
            threshold=math.inf,  # INFINITY so no warning fires
            event_type="cleanup",
        )

    # Cleanup counter is 3
    cleanup_count = notifications._consecutive_failures.get((slug, "cleanup"))
    assert cleanup_count == 3

    # Generation counter is unchanged (still absent)
    generation_count = notifications._consecutive_failures.get(
        (slug, "generation")
    )
    assert generation_count is None


def test_t8_notifications_resolve_threshold_returns_expected_values():
    """Phase 105: notifications.resolve_threshold exists and behaves correctly.

    - int legacy -> returns int directly
    - dict with key -> returns value
    - dict missing key -> returns INFINITY
    - bool -> returns INFINITY (defensive)
    - None -> returns {}
    """
    from lingwen_illustrations import notifications

    # int legacy
    assert notifications.resolve_threshold(
        {"notify_threshold": 5}, "cleanup"
    ) == 5

    # dict with key
    assert notifications.resolve_threshold(
        {"notify_threshold": {"cleanup": 3, "generation": 7}}, "cleanup"
    ) == 3
    assert notifications.resolve_threshold(
        {"notify_threshold": {"cleanup": 3, "generation": 7}}, "generation"
    ) == 7

    # dict missing key -> INFINITY
    assert notifications.resolve_threshold(
        {"notify_threshold": {"generation": 5}}, "cleanup"
    ) == math.inf

    # bool -> INFINITY (defensive — bool is subclass of int)
    assert notifications.resolve_threshold(
        {"notify_threshold": True}, "cleanup"
    ) == math.inf

    # missing notify_threshold key -> INFINITY
    assert notifications.resolve_threshold({}, "cleanup") == math.inf

    # empty settings dict -> INFINITY
    assert notifications.resolve_threshold({}, "deletion") == math.inf


def test_t9_pipeline_resolve_threshold_still_callable():
    """Phase 105: pipeline._resolve_threshold is back-compat re-export.

    pipeline._resolve_threshold is the same callable as
    notifications.resolve_threshold. Existing pipeline callers (generate_illustration
    + regenerate_illustration) and tests are unchanged.
    """
    from lingwen_illustrations import notifications, pipeline

    # Same callable (back-compat re-export via `from ... import ... as _resolve_threshold`)
    assert pipeline._resolve_threshold is notifications.resolve_threshold

    # Callable behavior preserved
    assert pipeline._resolve_threshold(
        {"notify_threshold": 4}, "regeneration"
    ) == 4
    assert pipeline._resolve_threshold(
        {"notify_threshold": {"regeneration": 2}}, "cleanup"
    ) == math.inf  # missing key -> INFINITY
