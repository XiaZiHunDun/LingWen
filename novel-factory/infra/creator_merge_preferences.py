"""Persist last-used creator settings merge strategy per project."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infra.creator_settings_docs import MERGE_SOURCES

_STATE_VERSION = "1"
_DEFAULT = {
    "pillars_merge_source": "editor",
    "global_outline_merge_source": "editor",
}


def _prefs_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_merge_preferences.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_merge_preferences(project_root: Path | str) -> dict[str, str]:
    path = _prefs_path(project_root)
    if not path.is_file():
        return dict(_DEFAULT)
    data = json.loads(path.read_text(encoding="utf-8"))
    pillars = str(data.get("pillars_merge_source", "editor"))
    outline = str(data.get("global_outline_merge_source", "editor"))
    if pillars not in MERGE_SOURCES:
        pillars = "editor"
    if outline not in MERGE_SOURCES:
        outline = "editor"
    return {
        "pillars_merge_source": pillars,
        "global_outline_merge_source": outline,
    }


def save_merge_preferences(
    project_root: Path | str,
    *,
    pillars_merge_source: str,
    global_outline_merge_source: str,
) -> dict[str, Any]:
    if pillars_merge_source not in MERGE_SOURCES:
        raise ValueError(f"invalid pillars merge source: {pillars_merge_source!r}")
    if global_outline_merge_source not in MERGE_SOURCES:
        raise ValueError(f"invalid outline merge source: {global_outline_merge_source!r}")
    path = _prefs_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": _STATE_VERSION,
        "pillars_merge_source": pillars_merge_source,
        "global_outline_merge_source": global_outline_merge_source,
        "updated_at": _now_iso(),
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data
