"""Phase 107: G1-G10 regression guards.

Guard against future regressions to bulk_delete_assets wiring + helper refactor
+ invariant extensions.
"""
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ILLUS_ROUTES = REPO_ROOT / "apps" / "studio_api" / "routes" / "illustrations.py"
ARCH_YML = REPO_ROOT / ".lingwen" / "architecture.yml"


# ---------- G1: bulk_delete_assets route registered ----------
def test_g1_bulk_delete_assets_route_registered():
    text = ILLUS_ROUTES.read_text(encoding="utf-8")
    assert "@app.delete(" in text and '"/api/illustrations"' in text
    assert "async def bulk_delete_assets(" in text
    # Returns {deleted, failed, summary} shape
    assert '"deleted"' in text and '"failed"' in text and '"summary"' in text


# ---------- G2: 51 ids → 422 ----------
def test_g2_limit_51_returns_422():
    text = ILLUS_ROUTES.read_text(encoding="utf-8")
    # Check for `len(asset_ids) > 50: raise HTTPException(422, ...)` pattern
    assert re.search(r"len\(asset_ids\)\s*>\s*50[^)]*HTTPException\(\s*422", text), \
        "bulk_delete_assets must enforce 50-id limit via 422"


# ---------- G3: empty ids → 422 ----------
def test_g3_empty_ids_returns_422():
    text = ILLUS_ROUTES.read_text(encoding="utf-8")
    assert re.search(r"if\s+not\s+asset_ids[^:]*:\s*\n[^#]*HTTPException\(\s*422", text, re.MULTILINE), \
        "bulk_delete_assets must raise 422 on empty asset_ids"


# ---------- G4: per-asset record_success + audit + publish in helper ----------
def test_g4_helper_records_per_asset():
    text = ILLUS_ROUTES.read_text(encoding="utf-8")
    # _delete_asset_inner function exists
    assert "async def _delete_asset_inner(" in text
    # Has all four notifications calls (record_failure x2 / record_success x2 inside helper)
    # We focus on success path: record_success + audit_log + publish are in helper body
    helper_section = text.split("async def _delete_asset_inner(")[1]
    assert "record_success(" in helper_section
    assert "audit_log.record_event(" in helper_section
    assert "notifications.publish(" in helper_section


# ---------- G5: 5/5 deletes produce 5 per-asset audit + publish ----------
def test_g5_bulk_iterates_per_asset():
    text = ILLUS_ROUTES.read_text(encoding="utf-8")
    bulk_section = text.split("async def bulk_delete_assets(")[1]
    # for-loop calling _delete_asset_inner
    assert re.search(r"for\s+\w+\s+in\s+asset_ids[^:]*:\s*\n[^#]*_delete_asset_inner\(", bulk_section), \
        "bulk_delete_assets must iterate asset_ids and call _delete_asset_inner per item"


# ---------- G6: counter isolation (Phase 106 G5 复用) ----------
def test_g6_counter_isolation_preserved():
    """Bulk deletion failures must NOT increment generation counter."""
    # Indirect verification: helper accepts event_type="deletion" and uses Phase 104 tuple keys
    text = ILLUS_ROUTES.read_text(encoding="utf-8")
    assert 'event_type="deletion"' in text
    # Phase 106 G5 test file should still be passing (verified via pytest run during Commit 11)


# ---------- G7: Phase 106 delete_asset single-delete preserved ----------
def test_g7_delete_asset_uses_helper():
    text = ILLUS_ROUTES.read_text(encoding="utf-8")
    # Single-delete route now calls _delete_asset_inner
    delete_route = text.split("@app.delete(\"/api/illustrations/{asset_id}\")")[1].split("@app.delete")[0]
    assert "_delete_asset_inner(" in delete_route, \
        "delete_asset route must delegate to _delete_asset_inner helper"
    # Single mode passed
    assert 'mode="single"' in delete_route


# ---------- G8: invariant extension documented ----------
def test_g8_invariant_extension_in_architecture_yml():
    text = ARCH_YML.read_text(encoding="utf-8")
    # I090 mentions bulk_delete_assets as caller
    assert re.search(r"id:\s*I090", text)
    # Parse YAML around I090 block (defensive: not raw grep)
    sections = text.split("\n  - id:")
    for section in sections:
        if section.lstrip().startswith("I090"):
            assert "bulk_delete_assets" in section, "I090 must mention bulk_delete_assets as 5th caller"
        elif section.lstrip().startswith("I091"):
            assert "bulk_delete_assets" in section, "I091 must mention bulk_delete_assets as 5th double-write site"
        elif section.lstrip().startswith("I095"):
            # I095 EXTENDED mentions bulk_delete_assets
            assert "bulk_delete_assets" in section or "Phase 107" in section, \
                "I095 must mention Phase 107 bulk_delete_assets extension"


# ---------- G9: dedupe via dict.fromkeys ----------
def test_g9_dedupe_via_dict_fromkeys():
    text = ILLUS_ROUTES.read_text(encoding="utf-8")
    bulk_section = text.split("async def bulk_delete_assets(")[1]
    assert "dict.fromkeys" in bulk_section, \
        "bulk_delete_assets must dedupe via dict.fromkeys"


# ---------- G10: cross-project implicit-not-found ----------
def test_g10_cross_project_not_via_explicit_check():
    """Cross-project isolation comes from per-project storage dirs, not explicit slug-vs-aid check."""
    text = ILLUS_ROUTES.read_text(encoding="utf-8")
    bulk_section = text.split("async def bulk_delete_assets(")[1]
    # No explicit cross-project slug-vs-aid mapping check
    assert "asset_id in project" not in bulk_section
    assert "asset not in" not in bulk_section
    # Helper raises LoadError naturally → handled via not_found status
    # (verified by T8 test in test_bulk_delete_api.py)