"""Project settings persistence (Phase 96 + Phase 98).

PUT/GET /api/projects/{slug}/settings — stores per-project illustration
preferences (default_provider + auto_generate + max_assets +
confirm_before_generate) at <project_root>/.lingwen/illustration_settings.yaml.

Extends Phase 95 deferred work ("持久化在 v2 走 /api/projects/{slug}/settings").

Phase 98: 3 new fields (auto_generate / max_assets / confirm_before_generate).
Back-compat via Pydantic v2 default fill — old yaml files still load.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from fastapi import FastAPI, HTTPException
from lingwen_illustrations.exceptions import LoadError
from pydantic import BaseModel, ValidationError

from apps.studio_api.routes._project_helpers import project_root_for
from apps.studio_api.routes.ctx import RoutesContext


class ProjectSettings(BaseModel):
    """Phase 101: extended with fallback_chain.

    Schema migration is back-compat: Pydantic v2 fills missing fields with defaults.
    Old yaml files from Phase 100 (without fallback_chain) still load successfully.
    """
    default_provider: Literal["minimax", "openai", "stability"] = "minimax"
    default_models: dict[str, str] = {}                  # Phase 100
    auto_generate: bool = False                          # Phase 98
    max_assets: int = 20                                # Phase 98
    confirm_before_generate: bool = False               # Phase 98
    fallback_chain: list[str] = []                      # NEW (Phase 101)


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
