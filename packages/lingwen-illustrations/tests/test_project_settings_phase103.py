"""Phase 103: ProjectSettings schema — chapter_overrides[].default_models cross-reference.

Per-chapter default_models must:
- Cross-reference provider in KNOWN_PROVIDERS
- Cross-reference model in provider.KNOWN_MODELS
- Empty dict accepted (chapter uses project default_models)
- Back-compat with old yaml without per-chapter default_models
"""
from __future__ import annotations

import pytest
import yaml
from pydantic import ValidationError

from apps.studio_api.routes.project_settings import ProjectSettings


def test_chapter_default_models_field_in_whitelist() -> None:
    """default_models added to _CHAPTER_OVERRIDABLE_FIELDS."""
    from apps.studio_api.routes.project_settings import _CHAPTER_OVERRIDABLE_FIELDS
    assert "default_models" in _CHAPTER_OVERRIDABLE_FIELDS


def test_chapter_default_models_accepts_valid_pair() -> None:
    """Valid chapter default_models subset passes validation."""
    from lingwen_illustrations.providers import KNOWN_PROVIDERS, get_provider

    valid_provider = next(iter(KNOWN_PROVIDERS))
    valid_model = next(iter(get_provider(valid_provider).models))
    s = ProjectSettings(chapter_overrides={1: {"default_models": {valid_provider: valid_model}}})
    assert s.chapter_overrides[1]["default_models"] == {valid_provider: valid_model}


def test_chapter_default_models_accepts_empty_dict() -> None:
    """Empty default_models dict in subset is accepted (no override)."""
    s = ProjectSettings(chapter_overrides={1: {"default_models": {}}})
    assert s.chapter_overrides[1]["default_models"] == {}


def test_chapter_default_models_accepts_multiple_providers() -> None:
    """Multiple provider-model pairs in same chapter."""
    from lingwen_illustrations.providers import KNOWN_PROVIDERS, get_provider

    if len(KNOWN_PROVIDERS) < 2:
        pytest.skip("Need >= 2 providers for this test")
    providers = list(KNOWN_PROVIDERS)[:2]
    pairs = {p: next(iter(get_provider(p).models)) for p in providers}
    s = ProjectSettings(chapter_overrides={5: {"default_models": pairs}})
    assert s.chapter_overrides[5]["default_models"] == pairs


def test_chapter_default_models_rejects_unknown_provider() -> None:
    """Unknown provider in chapter default_models raises ValidationError."""
    with pytest.raises(ValidationError, match="unknown provider"):
        ProjectSettings(chapter_overrides={1: {"default_models": {"unknown_provider_xyz": "model-x"}}})


def test_chapter_default_models_rejects_unknown_model() -> None:
    """Unknown model for valid provider raises ValidationError."""
    with pytest.raises(ValidationError, match="unknown model"):
        ProjectSettings(chapter_overrides={1: {"default_models": {"openai": "unknown-model-xyz"}}})


def test_chapter_default_models_does_not_break_other_columns() -> None:
    """Other chapter_overrides subset fields still work alongside default_models."""
    from lingwen_illustrations.providers import KNOWN_PROVIDERS, get_provider

    valid_provider = next(iter(KNOWN_PROVIDERS))
    valid_model = next(iter(get_provider(valid_provider).models))
    s = ProjectSettings(chapter_overrides={
        3: {
            "max_assets": 8,
            "confirm_before_generate": True,
            "auto_generate": False,
            "fallback_chain": ["stability"],
            "default_models": {valid_provider: valid_model},
        }
    })
    assert s.chapter_overrides[3]["max_assets"] == 8
    assert s.chapter_overrides[3]["default_models"] == {valid_provider: valid_model}


def test_chapter_default_models_yaml_round_trip(tmp_path) -> None:
    """YAML dump + reload preserves per-chapter default_models."""
    from lingwen_illustrations.providers import KNOWN_PROVIDERS, get_provider

    valid_provider = next(iter(KNOWN_PROVIDERS))
    valid_model = next(iter(get_provider(valid_provider).models))
    target = tmp_path / "settings.yaml"
    original = ProjectSettings(chapter_overrides={
        1: {"default_models": {valid_provider: valid_model}},
        5: {"default_models": {}},
    })
    target.write_text(yaml.safe_dump(original.model_dump(), allow_unicode=True), encoding="utf-8")
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    loaded = ProjectSettings(**data)
    assert loaded.chapter_overrides[1]["default_models"] == {valid_provider: valid_model}
    assert loaded.chapter_overrides[5]["default_models"] == {}


def test_chapter_default_models_back_compat_old_yaml() -> None:
    """Phase 102 yaml without per-chapter default_models still loads."""
    old_yaml = """\
default_provider: minimax
auto_generate: false
max_assets: 20
confirm_before_generate: false
fallback_chain: []
chapter_overrides:
  5:
    max_assets: 8
"""
    data = yaml.safe_load(old_yaml)
    s = ProjectSettings(**data)
    # Old yaml had no per-chapter default_models → key absent in subset
    assert "default_models" not in s.chapter_overrides[5]
    assert s.chapter_overrides[5]["max_assets"] == 8


def test_chapter_default_models_error_includes_chapter_num() -> None:
    """Error message identifies which chapter has bad default_models."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectSettings(chapter_overrides={42: {"default_models": {"unknown_provider": "x"}}})
    # Pydantic v2 ValidationError exposes error details
    error_str = str(exc_info.value)
    assert "42" in error_str or "chapter_overrides" in error_str
