"""Project-scoped character names for consistency checkers (Phase 10.06)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from infra.paths import ProjectPaths

_DEFAULT_TESTBED_AGENCY = ("林夜", "苏琳", "星月")
_OUTLINE_CHAR_SECTION = re.compile(
    r"##\s*关键人物\s*\n(.*?)(?=\n##|\Z)",
    re.DOTALL,
)
_BULLET_NAME = re.compile(r"^[-*]\s*(.+)$", re.MULTILINE)


def _names_from_profiles(path: Path) -> list[str]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("characters") or []
    names: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name", "")).strip()
        role = str(row.get("role", "")).strip()
        if not name:
            continue
        if "已故" in role:
            continue
        names.append(name)
    return names


def _names_from_outlines(chapters_dir: Path, *, max_chapters: int = 10) -> list[str]:
    if not chapters_dir.is_dir():
        return []
    found: list[str] = []
    for path in sorted(chapters_dir.glob("ch*_大纲.md"))[:max_chapters]:
        text = path.read_text(encoding="utf-8")
        section = _OUTLINE_CHAR_SECTION.search(text)
        if not section:
            continue
        for line in section.group(1).splitlines():
            m = _BULLET_NAME.match(line.strip())
            if not m:
                continue
            for part in re.split(r"[,，、]", m.group(1)):
                name = part.strip()
                if name and name not in found:
                    found.append(name)
    return found


def load_project_character_names(paths: ProjectPaths | None = None) -> list[str]:
    """Names from character_profiles.json, then chapter outlines."""
    resolved = paths or ProjectPaths.get()
    profiles = resolved.root / "03_内容仓库" / "角色设定" / "character_profiles.json"
    names = _names_from_profiles(profiles)
    if names:
        return names
    outline_names = _names_from_outlines(resolved.chapters)
    if outline_names:
        return outline_names
    from infra.project_config import ProjectConfig

    cfg = ProjectConfig.load(resolved)
    if cfg.role == "testbed":
        return list(_DEFAULT_TESTBED_AGENCY)
    return []


def load_agency_target_characters(
    paths: ProjectPaths | None = None,
    *,
    chapter_content: str | None = None,
) -> list[str]:
    """Characters to score for agency; prefer those present in chapter text."""
    names = load_project_character_names(paths)
    if not names:
        return list(_DEFAULT_TESTBED_AGENCY)
    if chapter_content:
        present = [n for n in names if n in chapter_content]
        if present:
            return present
    return names[:3] if len(names) > 3 else names
