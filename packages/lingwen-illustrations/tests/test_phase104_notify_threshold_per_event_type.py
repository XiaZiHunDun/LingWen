"""Phase 104 — notify_threshold per event_type — validator + counter guards.

8 guards (G1-G8) cover schema validation + counter state semantics.
Per spec 2026-09-21-phase-104-notify-threshold-per-event-type-design.md §1 + §2.
"""
from __future__ import annotations

import math

import pytest
from lingwen_illustrations import notifications

from apps.studio_api.routes.project_settings import ProjectSettings

KNOWN_EVENT_TYPES = ("generation", "regeneration", "cleanup", "deletion")
INFINITY = math.inf


# --- G1: validator accepts int legacy, expands to 4-key dict ---

def test_g1_validator_int_legacy_expands_to_4_key_dict():
    ps = ProjectSettings(notify_threshold=3)
    assert ps.notify_threshold == {
        "generation": 3, "regeneration": 3, "cleanup": 3, "deletion": 3,
    }


def test_g1b_validator_int_legacy_value_at_minimum():
    ps = ProjectSettings(notify_threshold=1)
    assert ps.notify_threshold == {et: 1 for et in KNOWN_EVENT_TYPES}


# --- G2: validator accepts partial dict, preserves only configured keys ---

def test_g2_validator_partial_dict_keeps_only_configured_keys():
    ps = ProjectSettings(notify_threshold={"generation": 5})
    assert ps.notify_threshold == {"generation": 5}


def test_g2b_validator_empty_dict_is_valid_opt_out():
    ps = ProjectSettings(notify_threshold={})
    assert ps.notify_threshold == {}


def test_g2c_validator_multi_event_type_dict():
    ps = ProjectSettings(notify_threshold={"generation": 5, "regeneration": 10})
    assert ps.notify_threshold == {"generation": 5, "regeneration": 10}


# --- G3: validator rejects unknown event_type key ---

def test_g3_validator_rejects_unknown_event_type():
    with pytest.raises(ValueError, match="not in"):
        ProjectSettings(notify_threshold={"unknown_type": 3})


# --- G4: validator rejects value < 1 ---

def test_g4_validator_rejects_int_below_1():
    with pytest.raises(ValueError, match="must be >= 1"):
        ProjectSettings(notify_threshold=0)


def test_g4b_validator_rejects_dict_value_below_1():
    with pytest.raises(ValueError, match="must be int >= 1"):
        ProjectSettings(notify_threshold={"generation": 0})


# --- G5: _resolve_threshold returns configured int or INFINITY for missing ---

def test_g5_resolve_threshold_returns_int_for_configured_key(monkeypatch):
    from lingwen_illustrations import pipeline
    settings = {"notify_threshold": {"generation": 5}}
    assert pipeline._resolve_threshold(settings, "generation") == 5


def test_g5b_resolve_threshold_returns_infinity_for_missing_key(monkeypatch):
    from lingwen_illustrations import pipeline
    settings = {"notify_threshold": {"generation": 5}}
    assert pipeline._resolve_threshold(settings, "cleanup") == INFINITY


# --- G6: counter keys are (project_slug, event_type) tuples (NOT bare slug) ---

def test_g6_consecutive_failures_keys_are_tuples(monkeypatch, tmp_path):
    """Phase 104 I095 EXTENDED: state keyed per (slug, event_type) tuple."""
    notifications._consecutive_failures.clear()
    notifications.record_failure(
        "test-slug", RuntimeError("boom"),
        project_root=tmp_path, threshold=3, event_type="generation",
    )
    assert ("test-slug", "generation") in notifications._consecutive_failures
    assert "test-slug" not in notifications._consecutive_failures


# --- G7: record_failure increments only target event_type counter ---

def test_g7_record_failure_isolates_event_type_counters(monkeypatch, tmp_path):
    """3 generation failures + 0 regeneration failures → 0 regen warnings."""
    notifications._consecutive_failures.clear()
    notifications._warning_emitted.clear()
    for _ in range(3):
        notifications.record_failure(
            "test-slug", RuntimeError("boom"),
            project_root=tmp_path, threshold=3, event_type="generation",
        )
    assert notifications._consecutive_failures[("test-slug", "generation")] == 3
    assert ("test-slug", "regeneration") not in notifications._consecutive_failures


# --- G8: record_success resets only target event_type counter ---

def test_g8_record_success_isolates_event_type_counters(monkeypatch, tmp_path):
    """Reset (slug, 'generation') only — (slug, 'regeneration') untouched."""
    notifications._consecutive_failures.clear()
    notifications._warning_emitted.clear()
    # Pre-populate both counters
    notifications.record_failure(
        "test-slug", RuntimeError("boom"),
        project_root=tmp_path, threshold=3, event_type="generation",
    )
    notifications.record_failure(
        "test-slug", RuntimeError("boom"),
        project_root=tmp_path, threshold=3, event_type="regeneration",
    )
    # Reset generation only
    notifications.record_success("test-slug", "generation")
    assert notifications._consecutive_failures[("test-slug", "generation")] == 0
    assert notifications._consecutive_failures[("test-slug", "regeneration")] == 1
