"""emit_chapter 落盘 — 将 workflow 合并润色后的正文写入 content_repo。"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any

from infra.paths import ProjectPaths


def emit_chapter_enabled() -> bool:
    """Opt-in disk emit: explicit LINGWEN_EMIT_CHAPTER or LINGWEN_REAL_LLM=1."""
    explicit = os.environ.get("LINGWEN_EMIT_CHAPTER", "").lower()
    if explicit in ("0", "false", "no"):
        return False
    if explicit in ("1", "true", "yes"):
        return True
    return os.environ.get("LINGWEN_REAL_LLM", "").lower() in ("1", "true", "yes")


def refresh_chapter_index(project_root: Path | None = None) -> bool:
    """Refresh 04_正文/index.json after a chapter write."""
    root = project_root or ProjectPaths.get().root
    script_path = root / "03_内容仓库" / "update_index.py"
    if not script_path.is_file():
        return False
    spec = importlib.util.spec_from_file_location("lw_content_update_index", script_path)
    if spec is None or spec.loader is None:
        return False
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.update_chapter_index()
    return True


def emit_chapter_to_repo(
    *,
    chapter_num: int,
    content: str,
    paths: ProjectPaths | None = None,
    update_index: bool = True,
) -> dict[str, Any]:
    """Write chapter markdown to 03_内容仓库/04_正文/chNNN.md."""
    if chapter_num <= 0:
        raise ValueError(f"invalid chapter_num: {chapter_num}")
    if not content or not str(content).strip():
        raise ValueError("emit_chapter: content is empty")

    resolved_paths = paths or ProjectPaths.get()
    path = resolved_paths.get_chapter_path(chapter_num)
    path.write_text(content, encoding="utf-8")

    index_updated = False
    if update_index:
        index_updated = refresh_chapter_index(resolved_paths.root)

    return {
        "chapter_num": chapter_num,
        "path": str(path),
        "written": True,
        "byte_count": path.stat().st_size,
        "index_updated": index_updated,
    }
