"""Phase 102 regression guards G1-G12 + I094 + I095 invariants.

Validates that the 3 new ProjectSettings fields (fallback_models /
chapter_overrides / notify_threshold) + 2 new invariants (I094 merge_chapter_settings
+ I095 record_failure/record_success state machine) are correctly wired across
backend + frontend + architecture.
"""
from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_SETTINGS_PY = (
    REPO_ROOT / "apps/studio_api" / "routes" / "project_settings.py"
)
PIPELINE_PY = (
    REPO_ROOT
    / "packages"
    / "lingwen-illustrations"
    / "src"
    / "lingwen_illustrations"
    / "pipeline.py"
)
NOTIFICATIONS_PY = (
    REPO_ROOT
    / "packages"
    / "lingwen-illustrations"
    / "src"
    / "lingwen_illustrations"
    / "notifications.py"
)
PROJECT_SETTINGS_VUE = (
    REPO_ROOT
    / "apps"
    / "dashboard"
    / "src"
    / "components"
    / "illustrations"
    / "ProjectSettingsIllustration.vue"
)
USE_PROJECT_SETTINGS_JS = (
    REPO_ROOT
    / "apps"
    / "dashboard"
    / "src"
    / "stores"
    / "useProjectSettings.js"
)
ARCHITECTURE_YML = REPO_ROOT / ".lingwen" / "architecture.yml"


# ---- G1: ProjectSettings schema has the 3 new fields ----

def test_g1_project_settings_schema_has_3_new_fields() -> None:
    """ProjectSettings declares fallback_models + chapter_overrides + notify_threshold."""
    src = PROJECT_SETTINGS_PY.read_text()
    assert "fallback_models" in src
    assert "chapter_overrides" in src
    assert "notify_threshold" in src


# ---- G2: pipeline.merge_chapter_settings exists ----

def test_g2_pipeline_merge_chapter_settings_exists() -> None:
    src = PIPELINE_PY.read_text()
    assert "def merge_chapter_settings" in src


# ---- G3: pipeline.resolve_model accepts is_fallback flag ----

def test_g3_pipeline_resolve_model_accepts_is_fallback() -> None:
    src = PIPELINE_PY.read_text()
    assert "is_fallback" in src


# ---- G4: notifications.record_failure + record_success helpers exist ----

def test_g4_notifications_record_failure_and_success_exist() -> None:
    src = NOTIFICATIONS_PY.read_text()
    assert "def record_failure" in src
    assert "def record_success" in src


# ---- G5: notifications._consecutive_failures state + warning emission ----

def test_g5_notifications_consecutive_failures_state_with_warning_emit() -> None:
    src = NOTIFICATIONS_PY.read_text()
    assert "_consecutive_failures" in src
    assert "severity" in src
    assert "_emit_failure_warning" in src or "emit_failure_warning" in src


# ---- G6: chapter_overrides Pydantic subset validator ----

def test_g6_chapter_overrides_pydantic_subset_validator() -> None:
    src = PROJECT_SETTINGS_PY.read_text()
    assert "_validate_chapter_overrides" in src
    # Validator should reject unknown fields with a clear message
    assert "unknown fields" in src
    assert "allowed:" in src


# ---- G7: fallback_models Pydantic provider/model cross-reference validator ----

def test_g7_fallback_models_pydantic_provider_model_validator() -> None:
    src = PROJECT_SETTINGS_PY.read_text()
    assert "_validate_fallback_models" in src
    assert "unknown provider" in src
    assert "unknown model" in src
    assert "valid models" in src


# ---- G8: notify_threshold >= 1 validator ----

def test_g8_notify_threshold_ge_1_validator() -> None:
    src = PROJECT_SETTINGS_PY.read_text()
    assert "_validate_notify_threshold" in src
    assert "notify_threshold must be >= 1" in src


# ---- G9: I094 + I095 invariants declared in architecture.yml ----

def test_g9_i094_and_i095_invariants_in_architecture_yml() -> None:
    yml = ARCHITECTURE_YML.read_text()
    assert "I094" in yml
    assert "I095" in yml
    # I094 should reference merge_chapter_settings
    assert "merge_chapter_settings" in yml
    # I095 should reference record_failure / record_success
    assert "record_failure" in yml or "record_success" in yml


# ---- G10: frontend Vue component has 3 new sections ----

def test_g10_frontend_component_has_3_new_sections() -> None:
    src = PROJECT_SETTINGS_VUE.read_text()
    # Fallback Models section: either English label or Chinese label "Fallback 模型"
    # or the data-testid="fallback-models-section" attribute.
    assert (
        "Fallback Models" in src
        or "Fallback 模型" in src
        or "fallback-models-section" in src
    )
    # Chapter Overrides section: English / Chinese "章节覆写" / data-testid.
    assert (
        "Chapter Overrides" in src
        or "章节覆写" in src
        or "chapter-overrides-section" in src
        or "chapter_overrides" in src
    )
    # Notify Threshold section: English / Chinese "通知阈值" / data-testid.
    assert (
        "Notify Threshold" in src
        or "通知阈值" in src
        or "notify-threshold-section" in src
        or "notify_threshold" in src
    )


# ---- G11: frontend store has 3 new fields ----

def test_g11_frontend_store_has_3_new_fields() -> None:
    src = USE_PROJECT_SETTINGS_JS.read_text()
    assert "fallback_models" in src
    assert "chapter_overrides" in src
    assert "notify_threshold" in src


# ---- G12: backward compat — Phase 101 yaml loads via Pydantic v2 default fill ----

def test_g12_backward_compat_old_yaml_loads_with_defaults() -> None:
    """Phase 101 yaml (no 3 new fields) loads successfully via Pydantic v2 default fill."""
    import yaml

    from apps.studio_api.routes.project_settings import ProjectSettings

    old_yaml = """\
default_provider: minimax
auto_generate: false
max_assets: 20
confirm_before_generate: false
fallback_chain: []
"""
    data = yaml.safe_load(old_yaml)
    s = ProjectSettings(**data)
    assert s.fallback_models == {}
    assert s.chapter_overrides == {}
    assert s.notify_threshold == 3
