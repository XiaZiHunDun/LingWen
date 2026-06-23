"""Apply creation_mode defaults to lingwen check."""
from __future__ import annotations

from dataclasses import replace
from typing import Any

from infra.creator_mode import (
    CREATION_MODE_STUDIO,
    CreatorSettings,
    settings_from_project_config,
)
from infra.paths import ProjectPaths
from infra.project_config import ProjectConfig


def load_creator_check_context(
    paths: ProjectPaths | None = None,
) -> tuple[ProjectConfig, CreatorSettings]:
    resolved = paths or ProjectPaths.get()
    config = ProjectConfig.load(resolved)
    settings = settings_from_project_config(config)
    return config, settings


def apply_creator_check_defaults(
    options: Any,
    *,
    paths: ProjectPaths | None = None,
    fail_severity_explicit: bool = False,
) -> tuple[Any, ProjectConfig, CreatorSettings]:
    """Merge project.yaml creator profile into CheckOptions when not overridden."""
    config, settings = load_creator_check_context(paths)

    updated = options
    if not fail_severity_explicit and settings.fail_severity:
        updated = replace(options, fail_severity=settings.fail_severity)

    if not settings.run_llm_judge and getattr(updated, "llm", False):
        updated = replace(updated, llm=False)

    return updated, config, settings


def format_check_mode_banner(config: ProjectConfig, settings: CreatorSettings) -> str:
    if settings.creation_mode == CREATION_MODE_STUDIO:
        return (
            f"工作室模式 ({settings.quality_profile}) · "
            f"fail≥{settings.fail_severity or 'any'}"
        )
    label = {
        "companion": "陪伴模式",
        "advance": "推进模式",
    }.get(settings.creation_mode, settings.creation_mode)
    return (
        f"{label} ({settings.quality_profile}) · "
        f"仅拦 {settings.fail_severity} · 默认无 LLM judge"
    )
