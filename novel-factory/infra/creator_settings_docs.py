"""Editable creator settings documents (pillars, global outline)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from infra.creator_volume_plan import global_outline_path
from infra.paths import ProjectPaths
from infra.project_config import ProjectConfig
from infra.studio_registry import StudioProject


def creator_settings_docs_payload(project: StudioProject) -> dict[str, Any]:
    paths = ProjectPaths.get(project.root)
    config = ProjectConfig.load(paths)
    pillars_path = config.pillars_path
    outline_path = global_outline_path(project.root)

    pillars_text = ""
    if pillars_path.is_file():
        pillars_text = pillars_path.read_text(encoding="utf-8")

    global_outline_text = ""
    if outline_path.is_file():
        global_outline_text = outline_path.read_text(encoding="utf-8")

    return {
        "slug": config.slug,
        "pillars_path": str(pillars_path),
        "global_outline_path": str(outline_path),
        "pillars_text": pillars_text,
        "global_outline_text": global_outline_text,
    }


def save_creator_settings_docs(
    project: StudioProject,
    *,
    pillars_text: str | None = None,
    global_outline_text: str | None = None,
) -> dict[str, Any]:
    paths = ProjectPaths.get(project.root)
    config = ProjectConfig.load(paths)

    if pillars_text is not None:
        path = config.pillars_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(pillars_text.rstrip() + "\n", encoding="utf-8")

    if global_outline_text is not None:
        path = global_outline_path(project.root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(global_outline_text.rstrip() + "\n", encoding="utf-8")

    return creator_settings_docs_payload(project)
