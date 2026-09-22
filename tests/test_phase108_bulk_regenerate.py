"""Phase 108: bulk regenerate illustration endpoint — regression guards.

Guards prevent regressions across the cluster (Phase 90-107 invariants
preserved + Phase 108 new patterns locked in).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ILLUSTRATIONS_PY = REPO_ROOT / "apps" / "studio_api" / "routes" / "illustrations.py"
ARCHITECTURE_YML = REPO_ROOT / ".lingwen" / "architecture.yml"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _function_body(text: str, function_name: str) -> str:
    """Extract a function's body bounded by the next @app. or async def / def.

    Phase 107 helpers use `text.split("async def <name>(")[1]` which includes
    everything to end of file — too coarse for guards that need to verify
    absence (e.g. no audit_log.record_event). This bounds to the next
    route registration decorator or function definition AND strips the
    docstring (which mentions emit calls in narrative form — false positive
    for absence checks).
    """
    start_marker = f"async def {function_name}("
    if start_marker not in text:
        return ""
    body_start = text.index(start_marker) + len(start_marker)
    # Find next top-level marker after function_start
    rest = text[body_start:]
    end_pos = len(rest)
    for marker in ("\n    @app.", "\n    async def ", "\n    def "):
        idx = rest.find(marker)
        if idx != -1 and idx < end_pos:
            end_pos = idx
    body = rest[:end_pos]
    # Strip docstring (triple-quoted) so narrative mentions of audit_log /
    # notifications / record_event don't trip absence guards.
    body = re.sub(r'"""[\s\S]*?"""', '', body)
    body = re.sub(r"'''[\s\S]*?'''", '', body)
    return body


# ---------- G1: bulk_regenerate_assets route registered with @app.put ----------
def test_g1_bulk_regenerate_route_registered() -> None:
    text = _read(ILLUSTRATIONS_PY)
    assert '@app.put("/api/illustrations"' in text, \
        "G1: bulk route @app.put missing"
    assert "async def bulk_regenerate_assets(" in text, \
        "G1: bulk_regenerate_assets function missing"


# ---------- G2: >10 ids → 422 ----------
def test_g2_over_10_ids_422() -> None:
    text = _read(ILLUSTRATIONS_PY)
    assert re.search(r"len\(asset_ids\)\s*>\s*10[^)]*HTTPException\(\s*422", text), \
        "G2: >10 422 check missing"
    assert re.search(r"max 10 ids per request", text), \
        "G2: 10-limit error message missing"


# ---------- G3: empty ids → 422 ----------
def test_g3_empty_ids_returns_422() -> None:
    text = _read(ILLUSTRATIONS_PY)
    assert re.search(
        r"if\s+not\s+asset_ids[^:]*:\s*\n[^#]*HTTPException\(\s*422",
        text,
        re.MULTILINE,
    ), "G3: empty 422 check missing"


# ---------- G4: per-asset helper fan-out ----------
def test_g4_per_asset_helper_fan_out() -> None:
    """G4: bulk route iterates over asset_ids and calls _regenerate_asset_inner per asset."""
    body = _function_body(_read(ILLUSTRATIONS_PY), "bulk_regenerate_assets")
    assert body, "G4: bulk_regenerate_assets function not found"
    # for-loop calling _regenerate_asset_inner (specific pattern to avoid matching
    # the dict-comp `for a in storage.list_assets` or docstring "for-loop calls")
    assert re.search(
        r"for\s+aid\s+in\s+asset_ids\s*:\s*\n[^#]*_regenerate_asset_inner\(",
        body,
    ), "G4: bulk must iterate asset_ids and call _regenerate_asset_inner per item"
    # mode='bulk' discriminator passed
    assert 'mode="bulk"' in body, \
        "G4: mode='bulk' discriminator missing"


# ---------- G5: counter isolation preserved (event_type='regeneration') ----------
def test_g5_counter_isolation_preserved() -> None:
    """G5: helper uses event_type='regeneration' — does not bleed into deletion/generation."""
    body = _function_body(_read(ILLUSTRATIONS_PY), "_regenerate_asset_inner")
    assert body, "G5: _regenerate_asset_inner function not found"
    assert 'event_type="regeneration"' in body, \
        "G5: event_type='regeneration' missing in helper"


# ---------- G6: Phase 107 bulk_delete + _delete_asset_inner preserved ----------
def test_g6_phase107_preserved() -> None:
    """G6: Phase 107 bulk_delete_assets + _delete_asset_inner still present."""
    text = _read(ILLUSTRATIONS_PY)
    assert "async def bulk_delete_assets(" in text, \
        "G6: Phase 107 bulk_delete_assets missing"
    assert "async def _delete_asset_inner(" in text, \
        "G6: Phase 107 _delete_asset_inner missing"


# ---------- G7: Phase 108 Option A — helper does NOT emit (pipeline owns emit) ----------
def test_g7_helper_emits_no_record_event() -> None:
    """G7: helper does NOT call audit_log.record_event or notifications.publish
    (pipeline owns emit, avoids double-emission breaking I091 invariant).
    Helper only calls record_failure + record_success for counter tracking.
    """
    body = _function_body(_read(ILLUSTRATIONS_PY), "_regenerate_asset_inner")
    assert body, "G7: _regenerate_asset_inner function not found"
    # Option A: NO audit_log.record_event + NO notifications.publish in helper
    assert "audit_log.record_event" not in body, \
        "G7: helper must NOT call audit_log.record_event (pipeline owns emit)"
    assert "notifications.publish" not in body, \
        "G7: helper must NOT call notifications.publish (pipeline owns emit)"
    # But helper DOES call record_failure + record_success
    assert "record_failure(" in body, \
        "G7: helper must call record_failure on IllustrationError"
    assert "record_success(" in body, \
        "G7: helper must call record_success on success/not_found"


# ---------- G8: dict.fromkeys dedupe ----------
def test_g8_dict_fromkeys_dedupe() -> None:
    """G8: dedupe via dict.fromkeys (preserves order)."""
    body = _function_body(_read(ILLUSTRATIONS_PY), "bulk_regenerate_assets")
    assert body, "G8: bulk_regenerate_assets function not found"
    assert "dict.fromkeys" in body, \
        "G8: dict.fromkeys dedupe missing"


# ---------- G9: meta_by_id pre-resolved once before loop ----------
def test_g9_meta_by_id_pre_resolved() -> None:
    """G9: bulk route pre-resolves meta_by_id dict once before loop (Phase 107 I1 invariant)."""
    body = _function_body(_read(ILLUSTRATIONS_PY), "bulk_regenerate_assets")
    assert body, "G9: bulk_regenerate_assets function not found"
    # meta_by_id dict must be defined in the bulk function body
    assert "meta_by_id" in body, \
        "G9: meta_by_id dict missing"
    # Use the specific `for aid in asset_ids` pattern (not `for `, which matches
    # docstring "for-loop calls" or dict-comp `for a in storage.list_assets`)
    meta_pos = body.index("meta_by_id")
    for_loop_match = re.search(r"for\s+aid\s+in\s+asset_ids\s*:", body)
    assert for_loop_match, \
        "G9: `for aid in asset_ids` loop not found"
    for_pos = for_loop_match.start()
    assert meta_pos < for_pos, \
        f"G9: meta_by_id (pos {meta_pos}) must be pre-resolved BEFORE for-loop (pos {for_pos})"


# ---------- G10: regenerate_illustration uses helper (mode='single') ----------
def test_g10_regenerate_uses_helper() -> None:
    """G10: existing regenerate_illustration route now delegates to helper (mode='single')."""
    body = _function_body(_read(ILLUSTRATIONS_PY), "regenerate_illustration")
    assert body, "G10: regenerate_illustration function not found"
    assert "_regenerate_asset_inner(" in body, \
        "G10: regenerate_illustration doesn't delegate to helper"
    assert 'mode="single"' in body, \
        "G10: mode='single' discriminator missing in single route"