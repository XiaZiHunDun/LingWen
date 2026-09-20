"""Phase 103: pipeline.merge_chapter_settings + resolve_model — chapter default_models.

Verifies that:
1. merge_chapter_settings replaces the WHOLE default_models dict (not per-key merge)
2. resolve_model reads chapter-merged default_models[provider] over project default_models[provider]
3. resolve_model fallback path is NOT affected by chapter default_models (project fallback_models wins)
4. resolve_model with no chapter override uses project default_models (regression)
"""
from __future__ import annotations

from lingwen_illustrations.pipeline import merge_chapter_settings, resolve_model
from lingwen_illustrations.providers import KNOWN_PROVIDERS, get_provider


def _make_adapter(provider: str):
    return get_provider(provider)


def _valid_provider_and_model() -> tuple[str, str]:
    """Pick first provider with at least one model."""
    for p in KNOWN_PROVIDERS:
        models = _make_adapter(p).models
        if models:
            return p, next(iter(models))
    raise RuntimeError("No provider has any models")


def test_merge_chapter_default_models_replaces_whole_dict() -> None:
    """Chapter default_models dict REPLACES project default_models dict (shallow merge)."""
    settings = {
        "default_models": {"minimax": "minimax-01", "openai": "dall-e-3"},
        "chapter_overrides": {5: {"default_models": {"openai": "gpt-image-1"}}},
    }
    effective = merge_chapter_settings(settings, 5)
    # Whole dict replaced — minimax default_models lost (chapter owns its view)
    assert effective["default_models"] == {"openai": "gpt-image-1"}


def test_merge_chapter_no_default_models_keeps_project() -> None:
    """Chapter subset without default_models → project default_models preserved."""
    settings = {
        "default_models": {"openai": "dall-e-3"},
        "chapter_overrides": {5: {"max_assets": 8}},
    }
    effective = merge_chapter_settings(settings, 5)
    assert effective["default_models"] == {"openai": "dall-e-3"}
    assert effective["max_assets"] == 8


def test_resolve_model_chapter_default_models_wins_over_project() -> None:
    """Chapter default_models[provider] takes precedence over project default_models[provider]."""
    project_provider, project_model = _valid_provider_and_model()
    # Pick a different valid model for the same provider
    models = list(_make_adapter(project_provider).models)
    if len(models) < 2:
        # Skip — need two distinct models
        return
    chapter_model = models[1] if models[0] == project_model else models[0]
    settings = {
        "default_models": {project_provider: project_model},
        "chapter_overrides": {5: {"default_models": {project_provider: chapter_model}}},
    }
    effective = merge_chapter_settings(settings, 5)
    adapter = _make_adapter(project_provider)
    resolved = resolve_model(
        provider=project_provider,
        explicit=None,
        project_settings=effective,
        adapter=adapter,
    )
    assert resolved == chapter_model


def test_resolve_model_chapter_default_models_no_override() -> None:
    """Chapter without default_models override → uses project default_models."""
    project_provider, project_model = _valid_provider_and_model()
    settings = {
        "default_models": {project_provider: project_model},
        "chapter_overrides": {5: {"max_assets": 8}},  # no default_models key
    }
    effective = merge_chapter_settings(settings, 5)
    adapter = _make_adapter(project_provider)
    resolved = resolve_model(
        provider=project_provider,
        explicit=None,
        project_settings=effective,
        adapter=adapter,
    )
    assert resolved == project_model


def test_resolve_model_chapter_default_models_does_not_affect_fallback_path() -> None:
    """is_fallback=True path uses project fallback_models, NOT chapter default_models."""
    project_provider, _ = _valid_provider_and_model()
    fb_models = list(_make_adapter(project_provider).models)
    if len(fb_models) < 2:
        return
    fb_model = fb_models[1]
    project_default_model = fb_models[0]
    chapter_model = fb_models[-1] if len(fb_models) > 2 else fb_models[1]
    settings = {
        "default_models": {project_provider: project_default_model},
        "fallback_models": {project_provider: fb_model},
        "chapter_overrides": {5: {"default_models": {project_provider: chapter_model}}},
    }
    effective = merge_chapter_settings(settings, 5)
    adapter = _make_adapter(project_provider)
    # Fallback path: chapter default_models must be IGNORED, project fallback_models used
    resolved_fb = resolve_model(
        provider=project_provider,
        explicit=None,
        project_settings=effective,
        adapter=adapter,
        is_fallback=True,
    )
    assert resolved_fb == fb_model, (
        f"is_fallback path must use project fallback_models, "
        f"got {resolved_fb} (expected {fb_model})"
    )
    # Primary path: chapter default_models wins
    resolved_primary = resolve_model(
        provider=project_provider,
        explicit=None,
        project_settings=effective,
        adapter=adapter,
        is_fallback=False,
    )
    assert resolved_primary == chapter_model


def test_resolve_model_explicit_still_wins_over_chapter_default_models() -> None:
    """Explicit API request model wins over chapter default_models (4-tier preserved)."""
    project_provider, _ = _valid_provider_and_model()
    models = list(_make_adapter(project_provider).models)
    if len(models) < 2:
        return
    explicit_model = models[1] if models[0] != models[1] else models[0]
    chapter_model = models[0] if models[0] != explicit_model else models[-1]
    if chapter_model == explicit_model:
        return  # need 2 distinct models
    settings = {
        "default_models": {},
        "chapter_overrides": {5: {"default_models": {project_provider: chapter_model}}},
    }
    effective = merge_chapter_settings(settings, 5)
    adapter = _make_adapter(project_provider)
    resolved = resolve_model(
        provider=project_provider,
        explicit=explicit_model,
        project_settings=effective,
        adapter=adapter,
    )
    assert resolved == explicit_model
