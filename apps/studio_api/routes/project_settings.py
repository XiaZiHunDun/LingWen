"""Project settings persistence (Phase 96 + Phase 98 + Phase 101 + Phase 102).

PUT/GET /api/projects/{slug}/settings — stores per-project illustration
preferences (default_provider + auto_generate + max_assets +
confirm_before_generate + fallback_chain + fallback_models +
chapter_overrides + notify_threshold) at
<project_root>/.lingwen/illustration_settings.yaml.

Extends Phase 95 deferred work ("持久化在 v2 走 /api/projects/{slug}/settings").

Phase 98: 3 new fields (auto_generate / max_assets / confirm_before_generate).
Phase 101: fallback_chain field.
Phase 102: 3 new fields (fallback_models / chapter_overrides / notify_threshold)
+ Pydantic validators for subset whitelist + provider/model cross-reference.

Back-compat via Pydantic v2 default fill — old yaml files still load.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

import yaml
from fastapi import FastAPI, HTTPException
from lingwen_illustrations.exceptions import LoadError
from pydantic import BaseModel, ValidationError, field_validator

from apps.studio_api.routes._project_helpers import project_root_for
from apps.studio_api.routes.ctx import RoutesContext

# Whitelisted subset of ProjectSettings fields that can be overridden per chapter
# (Phase 102). Phase 103 adds default_models — chapter can override which model
# to use per provider. Other fields (e.g. default_provider, fallback_models,
# fallback_chain itself) make less sense per-chapter and would add complexity
# to the merge logic.
_CHAPTER_OVERRIDABLE_FIELDS: frozenset[str] = frozenset(
    {"max_assets", "confirm_before_generate", "auto_generate", "fallback_chain", "default_models"}
)


class ProjectSettings(BaseModel):
    """Phase 102: extended with fallback_models + chapter_overrides + notify_threshold.

    Schema migration is back-compat: Pydantic v2 fills missing fields with defaults.
    Old yaml files from Phase 101 (without 3 new fields) still load successfully.
    """
    default_provider: Literal["minimax", "openai", "stability"] = "minimax"
    default_models: dict[str, str] = {}                  # Phase 100
    auto_generate: bool = False                          # Phase 98
    max_assets: int = 20                                # Phase 98
    confirm_before_generate: bool = False               # Phase 98
    fallback_chain: list[str] = []                      # Phase 101
    # NEW Phase 102 ↓
    fallback_models: dict[str, str] = {}                 # per-provider model for chain retry path
    chapter_overrides: dict[int, dict[str, Any]] = {}   # chapter_num -> subset of fields
    notify_threshold: int = 3                           # consecutive failures before warning

    @field_validator("fallback_models")
    @classmethod
    def _validate_fallback_models(cls, v: dict[str, str]) -> dict[str, str]:
        """Key must be in KNOWN_PROVIDERS; value must be in provider.KNOWN_MODELS."""
        # Lazy import to avoid cycle at module load (providers package imports models)
        from lingwen_illustrations.providers import KNOWN_PROVIDERS, get_provider

        for provider, model in v.items():
            if provider not in KNOWN_PROVIDERS:
                raise ValueError(f"unknown provider: {provider!r}")
            adapter = get_provider(provider)
            if model not in adapter.models:
                raise ValueError(
                    f"unknown model {model!r} for provider {provider!r}; "
                    f"valid models: {adapter.models}"
                )
        return v

    @field_validator("chapter_overrides")
    @classmethod
    def _validate_chapter_overrides(cls, v: dict[int, dict[str, Any]]) -> dict[int, dict[str, Any]]:
        """Key >= 0 int; value keys must be subset of _CHAPTER_OVERRIDABLE_FIELDS.

        Phase 103: cross-reference per-chapter default_models values against
        KNOWN_PROVIDERS + provider.KNOWN_MODELS (same pattern as top-level
        fallback_models validator).
        """
        from lingwen_illustrations.providers import KNOWN_PROVIDERS, get_provider

        for chapter_num, subset in v.items():
            if not isinstance(chapter_num, int) or chapter_num < 0:
                raise ValueError(
                    f"chapter_num must be >= 0 int, got {chapter_num!r}"
                )
            unknown = set(subset.keys()) - _CHAPTER_OVERRIDABLE_FIELDS
            if unknown:
                raise ValueError(
                    f"unknown fields in chapter_overrides[{chapter_num}]: {unknown}; "
                    f"allowed: {sorted(_CHAPTER_OVERRIDABLE_FIELDS)}"
                )
            # Phase 103: cross-reference per-chapter default_models if present
            if "default_models" in subset:
                cls._validate_chapter_default_models(
                    chapter_num, subset["default_models"], KNOWN_PROVIDERS, get_provider
                )
        return v

    @classmethod
    def _validate_chapter_default_models(
        cls,
        chapter_num: int,
        default_models: dict[str, str],
        known_providers: frozenset[str],
        get_provider_fn: Callable,
    ) -> None:
        """Cross-reference per-chapter default_models against KNOWN_MODELS.

        Mirrors the top-level fallback_models validator pattern (Phase 100).
        """
        for provider, model in default_models.items():
            if provider not in known_providers:
                raise ValueError(
                    f"chapter_overrides[{chapter_num}].default_models: "
                    f"unknown provider: {provider!r}"
                )
            adapter = get_provider_fn(provider)
            if model not in adapter.models:
                raise ValueError(
                    f"chapter_overrides[{chapter_num}].default_models: "
                    f"unknown model {model!r} for provider {provider!r}; "
                    f"valid models: {adapter.models}"
                )

    @field_validator("notify_threshold")
    @classmethod
    def _validate_notify_threshold(cls, v: int) -> int:
        if not isinstance(v, int) or v < 1:
            raise ValueError(f"notify_threshold must be >= 1, got {v}")
        return v


def _settings_path(project_root: Path) -> Path:
    return project_root / ".lingwen" / "illustration_settings.yaml"


def _save_settings(project_root: Path, settings: ProjectSettings) -> None:
    target = _settings_path(project_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        yaml.safe_dump(settings.model_dump(), allow_unicode=True),
        encoding="utf-8",
    )


def _load_settings(project_root: Path) -> ProjectSettings:
    """Load settings, silently falling back to defaults on missing/corrupt yaml.

    Returns ProjectSettings() (all defaults) when:
    - yaml file does not exist
    - yaml is malformed (YAMLError)
    - yaml content fails Pydantic validation (ValidationError)
    """
    target = _settings_path(project_root)
    if not target.exists():
        return ProjectSettings()
    try:
        data = yaml.safe_load(target.read_text(encoding="utf-8"))
        return ProjectSettings(**(data or {}))
    except (yaml.YAMLError, ValidationError):
        return ProjectSettings()


def register_project_settings(app: FastAPI, ctx: RoutesContext) -> None:
    """Mount /api/projects/{slug}/settings routes."""
    _ = ctx  # reserved for future ctx fields (e.g. settings storage abstraction)

    @app.put("/api/projects/{slug}/settings", response_model=ProjectSettings)
    async def put_settings(slug: str, settings: ProjectSettings) -> ProjectSettings:
        try:
            root = project_root_for(slug)
        except LoadError as e:
            raise HTTPException(404, detail={"stage": "load", "error": e.message}) from e
        _save_settings(root, settings)
        return settings

    @app.get("/api/projects/{slug}/settings", response_model=ProjectSettings)
    def get_settings(slug: str) -> ProjectSettings:
        try:
            root = project_root_for(slug)
        except LoadError as e:
            raise HTTPException(404, detail={"stage": "load", "error": e.message}) from e
        return _load_settings(root)


__all__ = ["register_project_settings", "ProjectSettings"]
