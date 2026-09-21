"""Phase 106: regression guards for delete_asset failure tracking wiring.

Guards G1-G6 prevent Phase 106 from being reverted to the no-tracking state
where DELETE /api/illustrations/{asset_id} does NOT call
notifications.record_failure/record_success or audit_log/publish.

Pattern (Phase 60+ I079 §A enforcement): each guard is a focused test, not a
class. Failing guards pinpoint exactly which invariant was broken.

Guards:
- G1: delete_asset route has >= 2 record_failure(event_type="deletion") calls
- G2: delete_asset route has >= 1 record_success(event_type="deletion") call
- G3: delete_asset route calls audit_log.record_event + notifications.publish (I091)
- G4: _load_deletion_settings helper exists in illustrations.py
- G5: 3 record_failure(slug, ..., event_type="deletion") calls leave generation counter = 0
- G6: I090/I091 rule fields mention DELETE route + I095 EXTENDED mentions deletion event_type
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ILLUSTRATIONS_ROUTE = REPO_ROOT / "apps/studio_api/routes/illustrations.py"
ARCHITECTURE_YML = REPO_ROOT / ".lingwen/architecture.yml"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _strip_docstrings(text: str) -> str:
    """Strip triple-quoted docstrings (N.14 v21 pattern).

    Docstrings may legitimately mention patterns the guards are testing
    (e.g. module docstring says 'record_failure(event_type="deletion")').
    Strip before regex search to avoid false positives.
    """
    return re.sub(r'""".*?""""', "", text, flags=re.DOTALL)


def _extract_delete_asset_body(text: str) -> str:
    """Extract the body of the nested delete_asset function inside register_illustrations.

    delete_asset is nested under register_illustrations (4-space indent). The
    next sibling decorator at the same indent is the terminator.
    """
    match = re.search(
        r'def delete_asset\([^)]*\)[^:]*:(.*?)(?=\n    @app\.|\Z)',
        text,
        re.DOTALL,
    )
    assert match, "delete_asset function not found"
    return match.group(1)


def test_g1_delete_asset_route_has_at_least_two_record_failure_calls():
    """G1: delete_asset route has >= 2 record_failure(event_type='deletion') calls.

    Catches Phase 106 reverts that remove either the LoadError path or the
    StoreError path. Both call sites must remain.
    """
    text = _strip_docstrings(_read(ILLUSTRATIONS_ROUTE))
    body = _extract_delete_asset_body(text)
    failure_calls = body.count('record_failure(')
    event_type_count = body.count('event_type="deletion"')
    assert failure_calls >= 2, (
        f"Expected >= 2 record_failure calls in delete_asset body, found {failure_calls}"
    )
    assert event_type_count >= 2, (
        f"Expected >= 2 'event_type=\"deletion\"' references in delete_asset body, "
        f"found {event_type_count}"
    )


def test_g2_delete_asset_route_has_at_least_one_record_success_call():
    """G2: delete_asset route has >= 1 record_success(event_type='deletion') call.

    Catches Phase 106 reverts that remove the counter reset on success. Without
    record_success, the (slug, "deletion") counter stays elevated forever after
    transient failures (Phase 102 lesson).
    """
    text = _strip_docstrings(_read(ILLUSTRATIONS_ROUTE))
    body = _extract_delete_asset_body(text)
    success_calls = body.count('record_success(')
    assert success_calls >= 1, (
        f"Expected >= 1 record_success call in delete_asset body, found {success_calls}"
    )
    assert 'event_type="deletion"' in body, (
        "record_success must be called with event_type=\"deletion\""
    )


def test_g3_delete_asset_double_writes_audit_log_and_publish():
    """G3: delete_asset route calls audit_log.record_event + notifications.publish (I091).

    Phase 99 invariant: every illustration event must double-write to audit_log
    (persistent) + publish (SSE fan-out) sharing the same event_id ULID.
    """
    text = _strip_docstrings(_read(ILLUSTRATIONS_ROUTE))
    body = _extract_delete_asset_body(text)
    assert 'audit_log.record_event(' in body, (
        "audit_log.record_event not called in delete_asset body"
    )
    assert 'notifications.publish(' in body, (
        "notifications.publish not called in delete_asset body"
    )


def test_g4_load_deletion_settings_helper_exists_in_illustrations_py():
    """G4: _load_deletion_settings helper exists in illustrations.py.

    Mirrors cleanup_route._load_cleanup_settings (Phase 105) and pipeline
    _load_illustration_settings pattern. Catches accidental removal of the
    settings reader that resolves notify_threshold for deletion event_type.
    """
    text = _read(ILLUSTRATIONS_ROUTE)
    assert "def _load_deletion_settings" in text, (
        "_load_deletion_settings helper not found in illustrations.py"
    )
    assert ".lingwen/illustration_settings.yaml" in text, (
        "_load_deletion_settings must read .lingwen/illustration_settings.yaml"
    )


def test_g5_deletion_failures_dont_increment_generation_counter():
    """G5: 3 record_failure(slug, ..., event_type='deletion') calls leave generation counter = 0.

    Phase 104 invariant: counter isolation per (slug, event_type) tuple.
    Phase 106 inherits this — deletion failures MUST NOT bleed into generation
    counter (G5 is the regression guard).
    """
    from lingwen_illustrations import notifications

    slug = "g5-phase106-slug"
    notifications._consecutive_failures.clear()
    notifications._warning_emitted.clear()

    error = RuntimeError("test")
    for _ in range(3):
        notifications.record_failure(
            slug, error,
            project_root=None,
            threshold=1,
            event_type="deletion",
        )

    # Deletion counter incremented to 3
    assert notifications._consecutive_failures[(slug, "deletion")] == 3

    # Generation counter untouched (no key present — "not 0" but "absent")
    assert notifications._consecutive_failures.get((slug, "generation")) is None

    # Cleanup after the test to avoid bleed across tests
    notifications._consecutive_failures.clear()
    notifications._warning_emitted.clear()


def test_g6_i090_i091_i095_extended_to_deletion_event_type():
    """G6: I090/I091 rule fields mention DELETE route + I095 EXTENDED mentions deletion event_type.

    Architecture invariants must be EXTENDED via docstring/note (YAGNI — no new
    invariant ID, just extend existing ones in their rule field). Catches:
    - I090/I091 not extended to mention delete_asset or illustrations.py
    - I095 not extended to mention deletion event_type (4th extension)
    """
    import yaml

    with ARCHITECTURE_YML.open(encoding="utf-8") as f:
        arch = yaml.safe_load(f)

    invariants = {inv["id"]: inv for inv in arch["invariants"]}

    # I090 EXTENDED: must mention delete_asset or illustrations.py
    i090_rule = invariants["I090"]["rule"]
    assert "delete_asset" in i090_rule or "illustrations.py" in i090_rule, (
        f"I090 rule must mention delete_asset or illustrations.py: {i090_rule}"
    )

    # I091 EXTENDED: must mention delete_asset or illustrations.py
    i091_rule = invariants["I091"]["rule"]
    assert "delete_asset" in i091_rule or "illustrations.py" in i091_rule, (
        f"I091 rule must mention delete_asset or illustrations.py: {i091_rule}"
    )

    # I095 EXTENDED: must mention deletion event_type (4th extension)
    i095_rule = invariants["I095"]["rule"]
    assert "deletion" in i095_rule, (
        f"I095 rule must mention deletion event_type: {i095_rule}"
    )
