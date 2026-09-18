"""Phase 98 regression guards (G1-G13).

Enforces Phase 98 invariants:
- I090 NEW: lru_cleanup + audit_log.record_event are the only entry points
  for illustration LRU deletion and event logging.
- ProjectSettings schema extended with 3 new fields (back-compat).
- Frontend ProjectSettingsIllustration persists every field.
- write_workspace auto_generate reads from persisted settings.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_g1_storage_lru_cleanup_exists():
    """G1: storage.lru_cleanup exists in lingwen-illustrations."""
    src = _read(PROJECT_ROOT / "packages/lingwen-illustrations/src/lingwen_illustrations/storage.py")
    assert "def lru_cleanup" in src
    # Must be exported
    assert '"lru_cleanup"' in src or "'lru_cleanup'" in src


def test_g2_project_settings_has_4_fields():
    """G2: ProjectSettings has 4 fields."""
    src = _read(PROJECT_ROOT / "apps/studio_api/routes/project_settings.py")
    assert "default_provider" in src
    assert "auto_generate" in src
    assert "max_assets" in src
    assert "confirm_before_generate" in src


def test_g3_audit_log_record_event_exists():
    """G3: audit_log.record_event exists."""
    src = _read(PROJECT_ROOT / "packages/lingwen-illustrations/src/lingwen_illustrations/audit_log.py")
    assert "def record_event" in src
    assert "__all__" in src
    assert "record_event" in src.split("__all__")[1]


def test_g4_pipeline_calls_lru_after_save_asset():
    """G4: pipeline calls lru_cleanup after save_asset (regex anchored)."""
    src = _read(PROJECT_ROOT / "packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py")
    # Use line-based matching since save_asset is a simple call (no parens in args).
    save_asset_idx = src.find("storage.save_asset(project_root, image_bytes, meta)")
    assert save_asset_idx > -1, "save_asset call must be present in generate_illustration"
    # Search for lru_cleanup in the remaining 1200 chars after save_asset
    chunk = src[save_asset_idx:save_asset_idx + 1200]
    assert "lru_cleanup(" in chunk, "lru_cleanup must be called after save_asset"


def test_g5_cleanup_endpoint_registered():
    """G5: POST /api/projects/{slug}/illustrations/cleanup endpoint registered."""
    src = _read(PROJECT_ROOT / "apps/studio_api/routes/cleanup_route.py")
    assert "/api/projects/{slug}/illustrations/cleanup" in src
    assert "register_cleanup" in src
    # And registered in routes facade
    routes_init = _read(PROJECT_ROOT / "apps/studio_api/routes/__init__.py")
    assert "register_cleanup" in routes_init


def test_g6_settings_route_accepts_4_fields():
    """G6: PUT /settings accepts 4-field body via ProjectSettings Pydantic schema."""
    src = _read(PROJECT_ROOT / "apps/studio_api/routes/project_settings.py")
    # ProjectSettings class must declare all 4 fields
    # (defensive: ensures all 4 are wired to the schema, not just present in module)
    assert re.search(r"default_provider:\s*Literal", src)
    assert re.search(r"auto_generate:\s*bool", src)
    assert re.search(r"max_assets:\s*int", src)
    assert re.search(r"confirm_before_generate:\s*bool", src)


def test_g7_write_workspace_reads_auto_generate():
    """G7: write_workspace background reads auto_generate from settings (not hardcoded)."""
    src = _read(PROJECT_ROOT / "apps/studio_api/background.py")
    # Must read settings.auto_generate, not hardcoded False
    assert "settings.auto_generate" in src
    # And write_workspace.py uses the settings
    write_ws = _read(PROJECT_ROOT / "apps/studio_api/routes/write_workspace.py")
    assert "auto_generate" in write_ws


def test_g8_settings_illustration_spec_has_3_fields():
    """G8: ProjectSettingsIllustration.spec.ts contains all 3 field testids."""
    spec_path = PROJECT_ROOT / "apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.spec.ts"
    src = _read(spec_path)
    assert "auto_generate" in src
    assert "max_assets" in src
    assert "confirm_before_generate" in src


def test_g9_generate_dialog_has_confirm_logic():
    """G9: GenerateIllustrationDialog has confirm_before_generate logic."""
    vue_path = PROJECT_ROOT / "apps/dashboard/src/components/illustrations/GenerateIllustrationDialog.vue"
    src = _read(vue_path)
    assert "confirm_before_generate" in src
    assert "window.confirm" in src


def test_g10_yaml_backcompat_defaults():
    """G10: yaml schema back-compat — all 4 fields have defaults so old yaml loads."""
    src = _read(PROJECT_ROOT / "apps/studio_api/routes/project_settings.py")
    # Default values must be present
    assert "auto_generate: bool = False" in src
    assert "max_assets: int = 20" in src
    assert "confirm_before_generate: bool = False" in src


def test_g11_audit_log_failures_silent():
    """G11: audit_log.record_event never raises (OSError swallowed)."""
    src = _read(PROJECT_ROOT / "packages/lingwen-illustrations/src/lingwen_illustrations/audit_log.py")
    assert "except OSError" in src
    # best-effort comment
    assert "best-effort" in src.lower() or "never raise" in src.lower()


def test_g12_i090_invariant_in_architecture():
    """G12: I090 invariant exists in .lingwen/architecture.yml."""
    import yaml

    arch_path = PROJECT_ROOT / ".lingwen/architecture.yml"
    if not arch_path.exists():
        pytest.skip("architecture.yml not found")
    data = yaml.safe_load(arch_path.read_text())
    invariants = data.get("invariants", [])
    has_i090 = any(inv.get("id") == "I090" for inv in invariants)
    assert has_i090, "I090 invariant must be declared in architecture.yml"


def test_g13_per_type_chapter_scope():
    """G13: per-type+per-chapter scope — lru_cleanup filters by type and chapter_num."""
    src = _read(PROJECT_ROOT / "packages/lingwen-illustrations/src/lingwen_illustrations/storage.py")
    # Both filters present
    assert "m.type ==" in src or "m.type ==" in src
    assert "m.chapter_num ==" in src
    # chapter_num required for chapter type
    assert "chapter_num required for chapter assets" in src or "chapter_num required" in src
