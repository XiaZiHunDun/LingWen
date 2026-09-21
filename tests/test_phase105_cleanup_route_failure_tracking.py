"""Phase 105 — Regression guards G1-G6.

Defensive guards ensuring the cleanup_route failure tracking wiring is not
accidentally reverted. Each guard pins a specific Phase 105 invariant.

Pattern (Phase 60+ I079 §A enforcement): each guard is a focused test, not a
class. Failing guards pinpoint exactly which invariant was broken.

Guards:
- G1: cleanup_route imports notifications AND calls record_failure(event_type="cleanup") >= 2 times
- G2: cleanup_route calls record_success(slug, event_type="cleanup") >= 1 time in success path
- G3: notifications.resolve_threshold exists AND is the same callable as pipeline._resolve_threshold
- G4: pipeline callers (generate/regenerate) use _resolve_threshold (no caller regression)
- G5: 3 record_failure(slug, ..., event_type="cleanup") calls leave generation counter = 0
- G6: cleanup_route reads .lingwen/illustration_settings.yaml with permissive fallback
"""
from __future__ import annotations

import math
import re

import pytest


def _strip_docstrings(source: str) -> str:
    """Strip triple-quoted docstrings (N.14 v21 pattern).

    Docstrings may legitimately mention patterns the guards are testing
    (e.g. module docstring says 'record_failure(event_type="cleanup")').
    Strip before regex search to avoid false positives.
    """
    return re.sub(r'""".*?""""', "", source, flags=re.DOTALL)


def test_g1_cleanup_route_has_two_record_failure_calls_with_cleanup_event_type():
    """cleanup_route calls record_failure(event_type="cleanup") >= 2 times.

    Catches Phase 105 reverts that remove either the 404 LoadError path or
    the StoreError path. Both call sites must remain.
    """
    from apps.studio_api.routes import cleanup_route

    source = _strip_docstrings(cleanup_route.__file__ and open(cleanup_route.__file__).read())
    # Count occurrences of `record_failure(` followed by `event_type="cleanup"`
    # within the same logical call (allow newlines + whitespace between args)
    pattern = re.compile(
        r'record_failure\([^)]*event_type\s*=\s*"cleanup"',
        re.DOTALL,
    )
    matches = pattern.findall(source)
    assert len(matches) >= 2, (
        f"cleanup_route must call record_failure(event_type='cleanup') >= 2 times; "
        f"found {len(matches)}"
    )


def test_g2_cleanup_route_calls_record_success_with_cleanup_event_type():
    """cleanup_route calls record_success(slug, event_type='cleanup') in success path.

    Catches Phase 105 reverts that remove the counter reset on success.
    Without record_success, counter stays elevated forever (Phase 102 lesson).
    """
    from apps.studio_api.routes import cleanup_route

    source = _strip_docstrings(open(cleanup_route.__file__).read())
    pattern = re.compile(
        r'record_success\([^)]*event_type\s*=\s*"cleanup"',
        re.DOTALL,
    )
    matches = pattern.findall(source)
    assert len(matches) >= 1, (
        f"cleanup_route must call record_success(event_type='cleanup') >= 1 time; "
        f"found {len(matches)}"
    )


def test_g3_resolve_threshold_relocated_to_notifications_and_pipeline_reexports():
    """notifications.resolve_threshold exists AND pipeline._resolve_threshold is the same callable.

    Phase 105 relocated _resolve_threshold from pipeline.py to notifications.py.
    Pipeline keeps a back-compat re-export. Catches helper drift / orphan
    re-export (N.14 v22 parsed-value check pattern).
    """
    from lingwen_illustrations import notifications, pipeline

    # notifications.resolve_threshold exists
    assert hasattr(notifications, "resolve_threshold")
    assert callable(notifications.resolve_threshold)

    # Same callable as pipeline._resolve_threshold (back-compat)
    assert pipeline._resolve_threshold is notifications.resolve_threshold


def test_g4_pipeline_caller_still_uses_resolve_threshold():
    """Pipeline generate/regenerate still call _resolve_threshold (no caller regression).

    Catches accidental removal of the back-compat alias or callers being left
    to reference a removed local helper.
    """
    from lingwen_illustrations import pipeline

    source = open(pipeline.__file__).read()
    # Both generate_illustration and regenerate_illustration resolve threshold
    # via _resolve_threshold(effective_settings, "generation"/"regeneration").
    # Count _resolve_threshold call sites within pipeline.py source.
    pattern = re.compile(r'_resolve_threshold\(')
    matches = pattern.findall(source)
    assert len(matches) >= 2, (
        f"pipeline.py must have >= 2 _resolve_threshold call sites "
        f"(generate + regenerate); found {len(matches)}"
    )


def test_g5_counter_isolation_cleanup_failures_do_not_bleed_to_generation():
    """3 record_failure(event_type='cleanup') calls leave generation counter = 0.

    Phase 104 invariant: counter isolation per (slug, event_type) tuple.
    Phase 105 inherits this — cleanup failures MUST NOT bleed into generation
    counter (G5 is the regression guard).
    """
    from lingwen_illustrations import notifications

    slug = "phase105-g5-isolation"
    error = RuntimeError("test")

    # Trigger 3 cleanup failures
    for _ in range(3):
        notifications.record_failure(
            slug, error,
            project_root=None,
            threshold=math.inf,  # INFINITY so no warning fires
            event_type="cleanup",
        )

    # Cleanup counter incremented
    assert notifications._consecutive_failures.get((slug, "cleanup")) == 3

    # Generation counter is untouched
    assert notifications._consecutive_failures.get((slug, "generation")) is None


def test_g6_cleanup_route_load_settings_has_permissive_fallback():
    """cleanup_route settings loader reads illustration_settings.yaml with permissive fallback.

    Catches accidental hard-fail (e.g. removing the missing-file return {} branch)
    that would break cleanup_route when settings don't exist (common case for
    new projects).
    """
    from apps.studio_api.routes import cleanup_route

    source = open(cleanup_route.__file__).read()
    # _load_cleanup_settings helper must exist
    assert "def _load_cleanup_settings" in source, (
        "_load_cleanup_settings helper missing from cleanup_route"
    )
    # Defensive: missing-file path returns {} (not raises)
    assert "return {}" in source, (
        "cleanup_route must have permissive fallback (return {}) for missing settings"
    )
    # Try/except for malformed yaml (matches _load_max_assets pattern)
    assert "(yaml.YAMLError, OSError)" in source, (
        "cleanup_route must catch yaml.YAMLError + OSError for permissive read"
    )
