"""Load real golden chapters for benchmark fixture.

Reads from projects/<slug>/golden-set/chapters/ch{NNN}.md in the LingWen
project tree.
"""
from __future__ import annotations

import os
from pathlib import Path

CHARACTER_SLUG = "林栀"
CHAPTER_IDS = [1, 3, 10]


def _projects_root() -> Path:
    """Resolve projects/ root. Allow override via LINGWEN_PROJECTS_ROOT env."""
    env = os.environ.get("LINGWEN_PROJECTS_ROOT")
    if env:
        return Path(env)
    # Walk up from this file to find projects/ — repo root is 4 levels up
    return Path(__file__).resolve().parents[3] / "projects"


def _chapter_path(slug: str, chapter_id: int) -> Path:
    return _projects_root() / slug / "golden-set" / "chapters" / f"ch{chapter_id:03d}.md"


def load_golden_chapters(slug: str, chapter_ids: list[int]) -> list[str]:
    """Load chapter texts in chapter_ids ascending order.

    Raises FileNotFoundError with the missing filename if any chapter is missing.
    """
    texts: list[str] = []
    for cid in sorted(chapter_ids):
        path = _chapter_path(slug, cid)
        if not path.exists():
            raise FileNotFoundError(f"missing fixture chapter: {path}")
        texts.append(path.read_text(encoding="utf-8"))
    return texts
