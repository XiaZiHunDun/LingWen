"""Read and activate the Studio active-project state."""
from __future__ import annotations

import json
import os
from pathlib import Path

from lingwen_paths import ProjectPaths

from lingwen_studio_registry.discovery import factory_root, get_project_by_slug, list_projects
from lingwen_studio_registry.models import _ACTIVE_STATE, StudioProject


def active_state_path() -> Path:
    return factory_root() / "infra" / ".state" / _ACTIVE_STATE


def read_active_slug() -> str | None:
    state = active_state_path()
    if state.is_file():
        data = json.loads(state.read_text(encoding="utf-8"))
        slug = data.get("slug")
        if slug and get_project_by_slug(str(slug)):
            return str(slug)
    env = os.environ.get("LINGWEN_PROJECT_ROOT", "").strip()
    if env:
        env_path = Path(env).resolve()
        for project in list_projects():
            if project.root.resolve() == env_path:
                return project.slug
    projects = list_projects()
    return projects[0].slug if projects else None


def activate_project(slug: str) -> StudioProject:
    project = get_project_by_slug(slug)
    if project is None:
        raise ValueError(f"unknown project slug: {slug!r}")
    state = active_state_path()
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps({"slug": slug, "root": str(project.root)}, ensure_ascii=False, indent=2), encoding="utf-8")
    os.environ["LINGWEN_PROJECT_ROOT"] = str(project.root)
    ProjectPaths.reset()
    ProjectPaths.get(project.root)
    return project


def active_project() -> StudioProject | None:
    slug = read_active_slug()
    if slug is None:
        return None
    return get_project_by_slug(slug)
