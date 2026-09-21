"""Phase 106 — Deletion event_type counter isolation + helper resilience tests.

6 NEW tests (T7-T9) covering:

T7: 3 deletion failures do NOT increment generation counter (counter isolation).
T8a: notifications.resolve_threshold returns int for configured "deletion" key.
T8b: notifications.resolve_threshold returns INFINITY for unconfigured "deletion" key.
T9a: _load_deletion_settings returns {} when .lingwen/illustration_settings.yaml is missing.
T9b: _load_deletion_settings returns {} when yaml is malformed.
T9c: _load_deletion_settings returns dict when yaml is valid.

These tests verify Phase 106 architectural invariants without modifying behavior.
T7/T8a/T8b use unique slugs per test (iso-slug) to avoid in-memory counter bleed
and rely on Phase 104 + Phase 105 machinery that already works.

T9a/T9b/T9c are RED until C5 creates `_load_deletion_settings` in
`apps/studio_api/routes/illustrations.py` (mirrors Phase 105 `_load_cleanup_settings`
in cleanup_route.py).
"""
from __future__ import annotations

import pytest
from lingwen_illustrations import notifications


@pytest.fixture(autouse=True)
def _reset_state():
    """Reset counter + warning flags per test (Phase 105 lesson).

    Phase 105 lesson: must clear BOTH _consecutive_failures AND _warning_emitted
    to prevent cross-test contamination. Without this, _warning_emitted=True from
    a prior test could mask threshold-crossing behavior in subsequent tests.
    """
    notifications._consecutive_failures.clear()
    notifications._warning_emitted.clear()
    yield
    notifications._consecutive_failures.clear()
    notifications._warning_emitted.clear()


def test_t7_deletion_counter_isolated_from_generation():
    """Phase 104 + 105 invariant: failures in different event types do NOT bleed.

    3 record_failure(slug, ..., event_type='deletion') calls must leave the
    generation counter at 0 (counter keyed per (slug, event_type) tuple).
    """
    slug = "phase106-t7-iso-slug"
    error = RuntimeError("test")

    # Trigger 3 deletion failures with threshold=1 (would emit warning, but
    # counter must remain isolated from generation).
    for _ in range(3):
        notifications.record_failure(
            slug, error,
            project_root=None,
            threshold=1,
            event_type="deletion",
        )

    # Deletion counter is 3
    deletion_count = notifications._consecutive_failures.get((slug, "deletion"))
    assert deletion_count == 3

    # Generation counter is unchanged (still absent / 0)
    generation_count = notifications._consecutive_failures.get(
        (slug, "generation")
    )
    assert generation_count is None or generation_count == 0


def test_t8a_resolve_threshold_returns_int_for_configured_deletion_key():
    """Phase 104 invariant: resolve_threshold returns int for configured key.

    settings = {"notify_threshold": {"generation": 3, "regeneration": 3,
                                       "cleanup": 3, "deletion": 5}}
    → resolve_threshold(settings, "deletion") == 5
    """
    settings = {
        "notify_threshold": {
            "generation": 3,
            "regeneration": 3,
            "cleanup": 3,
            "deletion": 5,
        }
    }
    assert notifications.resolve_threshold(settings, "deletion") == 5


def test_t8b_resolve_threshold_returns_infinity_for_missing_deletion_key():
    """Phase 104 invariant: missing notify_threshold key → INFINITY (never warn).

    settings = {"notify_threshold": {"generation": 3}}
    → resolve_threshold(settings, "deletion") == INFINITY_THRESHOLD
    """
    settings = {"notify_threshold": {"generation": 3}}
    result = notifications.resolve_threshold(settings, "deletion")
    assert result == notifications.INFINITY_THRESHOLD


def test_t9a_load_deletion_settings_permissive_fallback_missing_file(tmp_path):
    """Phase 106 NEW helper resilience: missing yaml → returns {}.

    `_load_deletion_settings(project_root)` is added in Phase 106 C5 to
    `apps/studio_api/routes/illustrations.py` (mirrors Phase 105
    `_load_cleanup_settings` in cleanup_route.py). Missing file is the
    common path (most projects don't ship illustration_settings.yaml)
    and must degrade gracefully.
    """
    from apps.studio_api.routes.illustrations import _load_deletion_settings

    # tmp_path exists but no .lingwen/illustration_settings.yaml inside
    assert _load_deletion_settings(tmp_path) == {}


def test_t9b_load_deletion_settings_permissive_fallback_malformed_yaml(tmp_path):
    """Phase 106 NEW helper resilience: malformed yaml → returns {}.

    yaml.YAMLError on parse must be swallowed (defensive read) so the
    delete_asset route continues to function. Returns {} so
    resolve_threshold sees no notify_threshold → INFINITY (never warn).
    """
    from apps.studio_api.routes.illustrations import _load_deletion_settings

    settings_path = tmp_path / ".lingwen" / "illustration_settings.yaml"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text("not: valid: yaml: [[[", encoding="utf-8")
    assert _load_deletion_settings(tmp_path) == {}


def test_t9c_load_deletion_settings_returns_dict_when_present(tmp_path):
    """Phase 106 NEW helper resilience: valid yaml → returns parsed dict.

    Validates the helper passes through yaml.safe_load output so
    resolve_threshold can read notify_threshold["deletion"] from the
    same file used by pipeline._load_illustration_settings +
    cleanup_route._load_cleanup_settings (Phase 104 shared source of truth).
    """
    from apps.studio_api.routes.illustrations import _load_deletion_settings

    settings_path = tmp_path / ".lingwen" / "illustration_settings.yaml"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        "notify_threshold:\n  deletion: 7\n",
        encoding="utf-8",
    )
    result = _load_deletion_settings(tmp_path)
    assert result == {"notify_threshold": {"deletion": 7}}
