"""灵文 项目初始化器

LingWen canonical project_init module (Phase 42 P3-ARCHDEBT project_init).
Migrated from infra/project_init.py — see invariant #56.

Provides `init_minimal_short_project` + scaffolding helpers for creator / studio
projects (slug validation, default parent dir, minimal chapter beats, project
yaml, pillars md, readme md, outline md, character profiles).
"""
from __future__ import annotations

from lingwen_project_init.beats import (
    _chapter_beats,
    _chapter_outline_md,
    _character_profiles,
    _global_outline_md,
    _pillars_md,
    _project_yaml,
    _readme_md,
    init_minimal_short_project,
)
from lingwen_project_init.models import (
    _MINIMAL_BEATS,
    _SLUG_RE,
    InitProjectResult,
)
from lingwen_project_init.slug import (
    _validate_chapter_count,
    default_project_parent,
    validate_slug,
)

__all__ = [
    # models (1 class; underscore-prefixed consts _SLUG_RE + _MINIMAL_BEATS NOT in __all__)
    "InitProjectResult",
    # slug (2 public; underscore-private _validate_chapter_count NOT in __all__)
    "validate_slug",
    "default_project_parent",
    # beats (1 public; underscore-private helpers NOT in __all__)
    "init_minimal_short_project",
]
