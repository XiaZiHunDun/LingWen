"""Slug validation + project parent resolution.

Migrated from infra/project_init.py — see invariant #56.
"""
from __future__ import annotations

import os
from pathlib import Path

from lingwen_shared.mode import (
    CREATION_MODE_ADVANCE,
    CREATION_MODE_COMPANION,
    CREATION_MODE_STUDIO,
)

from lingwen_project_init.models import _SLUG_RE


def validate_slug(slug: str) -> str:
    normalized = slug.strip().lower().replace("_", "-")
    if not _SLUG_RE.match(normalized):
        raise ValueError(
            f"slug must be lowercase alphanumeric/hyphen, 2-64 chars, got {slug!r}",
        )
    return normalized


def default_project_parent(factory_root: Path | None = None) -> Path:
    """Always under projects/ (not active LINGWEN_PROJECT_ROOT).

    Resolution order (mirrors `lingwen_studio_registry.factory_root` P40a pattern):
    1. Explicit `factory_root` argument (caller override)
    2. ``LINGWEN_PROJECT_ROOT`` env var (matches `lingwen_paths.resolve_project_root`)
    3. Fallback: `Path(__file__).resolve().parents[4]` (LingWen repo root)
       - __file__ = packages/lingwen-project-init/src/lingwen_project_init/slug.py
       - parents[0..3] = lingwen_project_init/ src/ lingwen-project-init/ packages/
       - parents[4]    = LingWen repo root
    """
    if factory_root is not None:
        base = factory_root
    else:
        env = os.environ.get("LINGWEN_PROJECT_ROOT", "").strip()
        base = Path(env) if env else Path(__file__).resolve().parents[4]
    return base / "projects"


def _validate_chapter_count(*, creation_mode: str, chapter_count: int) -> None:
    if creation_mode == CREATION_MODE_STUDIO and chapter_count != 10:
        raise ValueError("studio template supports exactly 10 chapters")
    if creation_mode == CREATION_MODE_COMPANION and not 1 <= chapter_count <= 30:
        raise ValueError("companion mode supports 1–30 chapters")
    if creation_mode == CREATION_MODE_ADVANCE and not 1 <= chapter_count <= 360:
        raise ValueError("advance mode supports 1–360 chapters")

