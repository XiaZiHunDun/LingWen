"""Detect chapters that need pilot retry after batch (Phase 10.03)."""
from __future__ import annotations

import json
from pathlib import Path


def extract_previous_chapter_excerpt(
    body: str,
    *,
    max_chars: int = 800,
) -> str:
    """Return tail of previous chapter for continuity (B-lite)."""
    text = body.strip()
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    tail = text[-max_chars:]
    # Prefer starting at paragraph break
    cut = tail.find("\n\n")
    if 0 <= cut < 120:
        tail = tail[cut + 2 :]
    return tail.strip()


def _body_ok(chapters_dir: Path, chapter_num: int, min_body_chars: int) -> bool:
    body_path = chapters_dir / f"ch{chapter_num:03d}.md"
    return body_path.is_file() and body_path.stat().st_size >= min_body_chars


def chapters_needing_retry(
    start_chapter: int,
    end_chapter: int,
    *,
    chapters_dir: Path,
    batch_summary_path: Path | None = None,
    min_body_chars: int = 200,
) -> list[int]:
    """Chapters missing body or with failed emit in batch summary."""
    if start_chapter > end_chapter:
        raise ValueError("start_chapter must be <= end_chapter")

    needs: set[int] = set()
    for ch in range(start_chapter, end_chapter + 1):
        if not _body_ok(chapters_dir, ch, min_body_chars):
            needs.add(ch)

    if batch_summary_path and batch_summary_path.is_file():
        data = json.loads(batch_summary_path.read_text(encoding="utf-8"))
        rows = data.get("chapter_results") or data.get("chapters") or []
        for row in rows:
            ch = int(row.get("chapter_num", 0))
            if start_chapter <= ch <= end_chapter and not row.get("emit_chapter_completed"):
                if not _body_ok(chapters_dir, ch, min_body_chars):
                    needs.add(ch)

    return sorted(needs)
