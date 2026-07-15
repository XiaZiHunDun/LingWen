"""Shared helpers for creator export (EPUB, DOCX)."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infra.creator_dashboard import creator_chapter_preview
from infra.creator_settings_docs import creator_settings_docs_payload
from infra.paths import ProjectPaths
from infra.project_config import ProjectConfig
from infra.studio_registry import StudioProject


def utc_modified_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def export_metadata(
    project: StudioProject,
    *,
    title: str | None = None,
    author: str | None = None,
    description: str | None = None,
) -> dict[str, str]:
    settings = creator_settings_docs_payload(project)
    book_title = title or project.name or project.slug or "灵文作品"
    book_author = author or project.name or "灵文作者"
    if description:
        book_description = description.strip()
    else:
        book_description = (settings.get("pillars_text") or "")[:280].strip() or book_title
    return {
        "title": book_title,
        "author": book_author,
        "description": book_description,
        "language": "zh-CN",
    }


def written_chapter_nums(project: StudioProject) -> list[int]:
    root = project.root if isinstance(project.root, Path) else Path(project.root)
    paths = ProjectPaths.get(root)
    config = ProjectConfig.load(paths)
    nums: list[int] = []
    for num in range(1, config.max_chapter + 1):
        body = paths.read_chapter(num)
        if body and body.strip():
            nums.append(num)
    return nums


def resolve_export_chapter_nums(
    project: StudioProject,
    *,
    mode: str,
    start_chapter: int | None,
    end_chapter: int | None,
    submission_sample_count: int = 3,
) -> list[int]:
    written = written_chapter_nums(project)
    if mode == "range" and start_chapter and end_chapter:
        lo = max(1, min(start_chapter, end_chapter))
        hi = max(start_chapter, end_chapter)
        return [n for n in written if lo <= n <= hi]
    if mode == "submission":
        count = max(1, min(int(submission_sample_count or 3), 12))
        return written[:count]
    return written


def load_export_chapters(
    project: StudioProject,
    chapter_nums: list[int],
) -> list[dict[str, Any]]:
    chapters: list[dict[str, Any]] = []
    for num in chapter_nums:
        preview = creator_chapter_preview(project, num, include_full_body=True)
        body = preview.get("body_text") or preview.get("body_preview") or ""
        chapters.append(
            {
                "chapter": num,
                "title": f"第{num}章",
                "body": body,
            },
        )
    return chapters


def split_paragraphs(body: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", body.strip()) if p.strip()]
