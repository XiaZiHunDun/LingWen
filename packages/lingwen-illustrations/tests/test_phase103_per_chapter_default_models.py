"""Phase 103 regression guards — per-chapter default_models overrides.

G1: default_models added to _CHAPTER_OVERRIDABLE_FIELDS
G2: _validate_chapter_overrides cross-references per-chapter default_models
G3: merge_chapter_settings shallow merge semantic (dict replacement)
G4: resolve_model 4-tier order preserved (no signature change)
G5: I094 invariant documented in CLAUDE.md / architecture.yml
G6: Frontend Pick whitelist includes default_models
G7: Frontend component renders new column
G8: No new dependencies in pyproject.toml or apps/dashboard/package.json
"""
from __future__ import annotations

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[3]


# G1
def test_g1_default_models_in_chapter_overridable_fields() -> None:
    from apps.studio_api.routes.project_settings import _CHAPTER_OVERRIDABLE_FIELDS
    assert "default_models" in _CHAPTER_OVERRIDABLE_FIELDS


# G2
def test_g2_validate_chapter_overrides_cross_references_default_models() -> None:
    """Validator raises when per-chapter default_models has unknown provider."""
    from pydantic import ValidationError
    from apps.studio_api.routes.project_settings import ProjectSettings
    with __import__("pytest").raises(ValidationError, match="unknown provider"):
        ProjectSettings(chapter_overrides={1: {"default_models": {"unknown_xyz": "m"}}})


# G3
def test_g3_merge_chapter_settings_dict_replacement_semantic() -> None:
    from lingwen_illustrations.pipeline import merge_chapter_settings
    settings = {
        "default_models": {"minimax": "minimax-01", "openai": "dall-e-3"},
        "chapter_overrides": {5: {"default_models": {"openai": "gpt-image-1"}}},
    }
    effective = merge_chapter_settings(settings, 5)
    # Whole dict replaced (shallow merge); minimax default_models lost
    assert "minimax" not in effective["default_models"]
    assert effective["default_models"] == {"openai": "gpt-image-1"}


# G4
def test_g4_resolve_model_4_tier_order_preserved() -> None:
    """Explicit > fallback (when is_fallback) > default_models > provider default."""
    from lingwen_illustrations.pipeline import resolve_model
    from lingwen_illustrations.providers import KNOWN_PROVIDERS, get_provider
    # Pick any valid provider
    provider = next(iter(KNOWN_PROVIDERS))
    adapter = get_provider(provider)
    models = list(adapter.models)
    if len(models) < 2:
        __import__("pytest").skip("Need >= 2 models")
    # explicit wins
    resolved = resolve_model(
        provider=provider, explicit=models[1], project_settings={}, adapter=adapter,
    )
    assert resolved == models[1]
    # default tier
    resolved = resolve_model(
        provider=provider, explicit=None,
        project_settings={"default_models": {provider: models[1]}},
        adapter=adapter,
    )
    assert resolved == models[1]
    # provider default tier (no settings)
    resolved = resolve_model(
        provider=provider, explicit=None, project_settings=None, adapter=adapter,
    )
    assert resolved == adapter.default_model


# G5
def test_g5_i094_invariant_documented() -> None:
    """I094 invariant exists in architecture.yml OR CLAUDE.md."""
    arch_yml = REPO_ROOT / ".lingwen" / "architecture.yml"
    claude_md = REPO_ROOT / "CLAUDE.md"
    arch_text = arch_yml.read_text(encoding="utf-8") if arch_yml.exists() else ""
    claude_text = claude_md.read_text(encoding="utf-8") if claude_md.exists() else ""
    # Either source mentions I094 by number AND merge_chapter_settings
    assert ("I094" in arch_text and "merge_chapter_settings" in arch_text) or (
        "I094" in claude_text and "merge_chapter_settings" in claude_text
    ), "I094 invariant must be documented in architecture.yml or CLAUDE.md"


# G6
def test_g6_frontend_pick_whitelist_includes_default_models() -> None:
    """TypeScript Pick<ProjectSettings, ...> includes 'default_models' for chapter_overrides."""
    api_ts = REPO_ROOT / "apps" / "dashboard" / "src" / "api" / "illustrations.ts"
    text = api_ts.read_text(encoding="utf-8")
    # Match the Pick whitelist union containing chapter_overrides
    pattern = re.compile(
        r"chapter_overrides\?:.*?Pick<[^>]*?'default_models'",
        re.DOTALL,
    )
    assert pattern.search(text), (
        f"chapter_overrides Pick whitelist must include 'default_models' in {api_ts}"
    )


# G7
def test_g7_component_renders_default_models_column() -> None:
    """ProjectSettingsIllustration.vue has default_models column header."""
    component = REPO_ROOT / "apps" / "dashboard" / "src" / "components" / "illustrations" / "ProjectSettingsIllustration.vue"
    text = component.read_text(encoding="utf-8")
    # Column header text and at least one testid reference
    assert "Default Models" in text, "Column header missing"
    assert "chapter-override-default-models" in text, "testid missing"


# G8
def test_g8_no_new_dependencies() -> None:
    """Phase 103 introduces 0 new third-party or workspace dependencies.

    Anchored at f25ace5a (LAST Phase 102 commit) so this guard continues to
    cover the full Phase 103 window even after Tasks 10+11 push HEAD forward.
    """
    import subprocess
    result = subprocess.run(
        ["git", "diff", "f25ace5a..HEAD", "--name-only", "--", "pyproject.toml", "packages/*/pyproject.toml", "apps/*/package.json"],
        cwd=str(REPO_ROOT),
        capture_output=True, text=True,
    )
    assert result.returncode == 0, "git diff failed"
    assert result.stdout.strip() == "", (
        f"Phase 103 should not add new deps; touched: {result.stdout}"
    )