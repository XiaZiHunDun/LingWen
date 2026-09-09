"""Studio project discovery from the factory root and projects directory."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from lingwen_studio_registry.models import StudioProject


def factory_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_yaml_project(root: Path) -> dict[str, Any]:
    config_path = root / "config" / "project.yaml"
    if not config_path.is_file():
        return {}
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return data.get("project") or {}


def list_projects() -> list[StudioProject]:
    root = factory_root()
    items: list[StudioProject] = []
    root_raw = _load_yaml_project(root)
    if root_raw:
        items.append(StudioProject(slug=str(root_raw.get("slug", "default")), name=str(root_raw.get("name", "default")), role=str(root_raw.get("role", "production")), root=root, location="root"))
    projects_dir = root / "projects"
    if projects_dir.is_dir():
        for child in sorted(projects_dir.iterdir()):
            if not child.is_dir():
                continue
            raw = _load_yaml_project(child)
            if not raw:
                continue
            items.append(StudioProject(slug=str(raw.get("slug", child.name)), name=str(raw.get("name", child.name)), role=str(raw.get("role", "production")), root=child, location="projects"))
    return items


def get_project_by_slug(slug: str) -> StudioProject | None:
    for project in list_projects():
        if project.slug == slug:
            return project
    return None
