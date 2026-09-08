"""Project-scoped chapter range helpers for CLI."""

from __future__ import annotations

from lingwen_paths import ProjectPaths

from lingwen_project_config import ProjectConfig

_DEFAULT_MAX_CHAPTER = 360


def project_max_chapter(paths: ProjectPaths | None = None) -> int:
    try:
        config = ProjectConfig.load(paths or ProjectPaths.get())
        return max(1, int(config.max_chapter))
    except Exception:
        return _DEFAULT_MAX_CHAPTER
