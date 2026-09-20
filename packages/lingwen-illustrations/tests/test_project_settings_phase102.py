"""Phase 102: ProjectSettings schema — fallback_models + chapter_overrides + notify_threshold.

Back-compat: Pydantic v2 default-fill means old yaml files (without 3 new fields)
still load successfully with default values.
"""
from __future__ import annotations

import pytest
import yaml
from pydantic import ValidationError

from apps.studio_api.routes.project_settings import ProjectSettings


def test_fallback_models_field_present() -> None:
    s = ProjectSettings()
    assert hasattr(s, "fallback_models")
    assert s.fallback_models == {}


def test_chapter_overrides_field_present() -> None:
    s = ProjectSettings()
    assert hasattr(s, "chapter_overrides")
    assert s.chapter_overrides == {}


def test_notify_threshold_field_present_default_3() -> None:
    s = ProjectSettings()
    assert hasattr(s, "notify_threshold")
    assert s.notify_threshold == 3


def test_back_compat_old_yaml_without_new_fields_loads() -> None:
    """Phase 101 yaml (no fallback_models/chapter_overrides/notify_threshold) loads with defaults."""
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


def test_chapter_overrides_valid_subset() -> None:
    s = ProjectSettings(chapter_overrides={5: {"max_assets": 8}})
    assert s.chapter_overrides == {5: {"max_assets": 8}}


def test_chapter_overrides_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError, match="unknown fields"):
        ProjectSettings(chapter_overrides={5: {"unknown_field": True}})


def test_chapter_overrides_rejects_negative_chapter_num() -> None:
    with pytest.raises(ValidationError, match="chapter_num"):
        ProjectSettings(chapter_overrides={-1: {"max_assets": 5}})


def test_notify_threshold_rejects_zero() -> None:
    with pytest.raises(ValidationError, match="notify_threshold"):
        ProjectSettings(notify_threshold=0)


def test_notify_threshold_rejects_negative() -> None:
    with pytest.raises(ValidationError, match="notify_threshold"):
        ProjectSettings(notify_threshold=-1)


def test_fallback_models_rejects_unknown_provider() -> None:
    with pytest.raises(ValidationError, match="provider"):
        ProjectSettings(fallback_models={"unknown_provider": "model-x"})


def test_fallback_models_rejects_unknown_model() -> None:
    with pytest.raises(ValidationError, match="model"):
        ProjectSettings(fallback_models={"openai": "unknown-model-xyz"})


def test_fallback_models_accepts_valid() -> None:
    """At least one valid provider/model pair passes (cross-references real KNOWN_MODELS)."""
    from lingwen_illustrations.providers import KNOWN_PROVIDERS
    from lingwen_illustrations.providers import get_provider

    valid_found = False
    for provider_name in KNOWN_PROVIDERS:
        adapter = get_provider(provider_name)
        if adapter.models:
            model = next(iter(adapter.models))
            s = ProjectSettings(fallback_models={provider_name: model})
            assert s.fallback_models == {provider_name: model}
            valid_found = True
            break
    assert valid_found, "No provider has any models in KNOWN_MODELS — test setup broken"


def test_round_trip_yaml_save_load_preserves_new_fields(tmp_path) -> None:
    """Yaml dump + reload preserves all 3 new fields."""
    target = tmp_path / "settings.yaml"
    original = ProjectSettings(
        fallback_models={"openai": "dall-e-3"},
        chapter_overrides={5: {"max_assets": 8}},
        notify_threshold=5,
    )
    target.write_text(yaml.safe_dump(original.model_dump(), allow_unicode=True), encoding="utf-8")
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    loaded = ProjectSettings(**data)
    assert loaded.fallback_models == original.fallback_models
    assert loaded.chapter_overrides == original.chapter_overrides
    assert loaded.notify_threshold == original.notify_threshold
