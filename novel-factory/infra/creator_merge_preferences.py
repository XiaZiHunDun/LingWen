"""Persist last-used creator settings merge strategy per project and globally."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infra.creator_settings_docs import MERGE_SOURCES

_STATE_VERSION = "3"
_DEFAULT = {
    "pillars_merge_source": "editor",
    "global_outline_merge_source": "editor",
    "merge_snapshot_id": None,
    "pillars_merge_snapshot_id": None,
    "global_outline_merge_snapshot_id": None,
}


def _prefs_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_merge_preferences.json"


def _global_prefs_path() -> Path:
    from infra.studio_registry import factory_root

    return factory_root() / "infra" / ".state" / "creator_merge_preferences_global.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_prefs(data: dict[str, Any]) -> dict[str, Any]:
    pillars = str(data.get("pillars_merge_source", "editor"))
    outline = str(data.get("global_outline_merge_source", "editor"))
    if pillars not in MERGE_SOURCES:
        pillars = "editor"
    if outline not in MERGE_SOURCES:
        outline = "editor"
    legacy_snap = data.get("merge_snapshot_id")
    if legacy_snap is not None:
        legacy_snap = str(legacy_snap).strip() or None
    pillars_snap = data.get("pillars_merge_snapshot_id")
    if pillars_snap is not None:
        pillars_snap = str(pillars_snap).strip() or None
    if not pillars_snap:
        pillars_snap = legacy_snap
    outline_snap = data.get("global_outline_merge_snapshot_id")
    if outline_snap is not None:
        outline_snap = str(outline_snap).strip() or None
    if not outline_snap:
        outline_snap = legacy_snap
    return {
        "pillars_merge_source": pillars,
        "global_outline_merge_source": outline,
        "merge_snapshot_id": legacy_snap,
        "pillars_merge_snapshot_id": pillars_snap,
        "global_outline_merge_snapshot_id": outline_snap,
    }


def load_global_merge_preferences() -> dict[str, Any]:
    path = _global_prefs_path()
    if not path.is_file():
        return dict(_DEFAULT)
    data = json.loads(path.read_text(encoding="utf-8"))
    return _normalize_prefs(data)


def save_global_merge_preferences(
    *,
    pillars_merge_source: str,
    global_outline_merge_source: str,
    merge_snapshot_id: str | None = None,
    pillars_merge_snapshot_id: str | None = None,
    global_outline_merge_snapshot_id: str | None = None,
) -> dict[str, Any]:
    if pillars_merge_source not in MERGE_SOURCES:
        raise ValueError(f"invalid pillars merge source: {pillars_merge_source!r}")
    if global_outline_merge_source not in MERGE_SOURCES:
        raise ValueError(f"invalid outline merge source: {global_outline_merge_source!r}")
    path = _global_prefs_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    legacy = merge_snapshot_id.strip() if merge_snapshot_id else None
    if not legacy:
        legacy = None
    pillars_snap = pillars_merge_snapshot_id.strip() if pillars_merge_snapshot_id else None
    if not pillars_snap:
        pillars_snap = legacy
    outline_snap = (
        global_outline_merge_snapshot_id.strip()
        if global_outline_merge_snapshot_id
        else None
    )
    if not outline_snap:
        outline_snap = legacy
    data = {
        "schema_version": _STATE_VERSION,
        "pillars_merge_source": pillars_merge_source,
        "global_outline_merge_source": global_outline_merge_source,
        "merge_snapshot_id": legacy,
        "pillars_merge_snapshot_id": pillars_snap,
        "global_outline_merge_snapshot_id": outline_snap,
        "updated_at": _now_iso(),
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def load_merge_preferences(project_root: Path | str) -> dict[str, Any]:
    path = _prefs_path(project_root)
    if not path.is_file():
        prefs = load_global_merge_preferences()
        prefs["uses_global_default"] = True
        return prefs
    data = json.loads(path.read_text(encoding="utf-8"))
    prefs = _normalize_prefs(data)
    prefs["uses_global_default"] = False
    return prefs


def save_merge_preferences(
    project_root: Path | str,
    *,
    pillars_merge_source: str,
    global_outline_merge_source: str,
    merge_snapshot_id: str | None = None,
    pillars_merge_snapshot_id: str | None = None,
    global_outline_merge_snapshot_id: str | None = None,
) -> dict[str, Any]:
    if pillars_merge_source not in MERGE_SOURCES:
        raise ValueError(f"invalid pillars merge source: {pillars_merge_source!r}")
    if global_outline_merge_source not in MERGE_SOURCES:
        raise ValueError(f"invalid outline merge source: {global_outline_merge_source!r}")
    path = _prefs_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    legacy = merge_snapshot_id.strip() if merge_snapshot_id else None
    if not legacy:
        legacy = None
    pillars_snap = pillars_merge_snapshot_id.strip() if pillars_merge_snapshot_id else None
    if not pillars_snap:
        pillars_snap = legacy
    outline_snap = (
        global_outline_merge_snapshot_id.strip()
        if global_outline_merge_snapshot_id
        else None
    )
    if not outline_snap:
        outline_snap = legacy
    data = {
        "schema_version": _STATE_VERSION,
        "pillars_merge_source": pillars_merge_source,
        "global_outline_merge_source": global_outline_merge_source,
        "merge_snapshot_id": legacy,
        "pillars_merge_snapshot_id": pillars_snap,
        "global_outline_merge_snapshot_id": outline_snap,
        "updated_at": _now_iso(),
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    save_global_merge_preferences(
        pillars_merge_source=pillars_merge_source,
        global_outline_merge_source=global_outline_merge_source,
        merge_snapshot_id=legacy,
        pillars_merge_snapshot_id=pillars_snap,
        global_outline_merge_snapshot_id=outline_snap,
    )
    return data


_EXPORT_SCHEMA_VERSION = "1"


def _prefs_export_block(data: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_prefs(data)
    return {
        "pillars_merge_source": normalized["pillars_merge_source"],
        "global_outline_merge_source": normalized["global_outline_merge_source"],
        "merge_snapshot_id": normalized["merge_snapshot_id"],
        "pillars_merge_snapshot_id": normalized["pillars_merge_snapshot_id"],
        "global_outline_merge_snapshot_id": normalized["global_outline_merge_snapshot_id"],
    }


def export_merge_preferences(project_root: Path | str) -> dict[str, Any]:
    """Export project + global merge preferences as portable JSON."""
    project = load_merge_preferences(project_root)
    global_prefs = load_global_merge_preferences()
    return {
        "schema_version": _EXPORT_SCHEMA_VERSION,
        "project": _prefs_export_block(project),
        "global": _prefs_export_block(global_prefs),
    }


def import_merge_preferences(
    project_root: Path | str,
    payload: dict[str, Any],
    *,
    scope: str = "project",
) -> dict[str, Any]:
    """Import merge preferences from export JSON."""
    scope_norm = str(scope).strip().lower()
    if scope_norm not in {"project", "global", "both"}:
        raise ValueError("scope must be project, global, or both")

    def _apply_block(block: dict[str, Any], *, to_project: bool, to_global: bool) -> None:
        kwargs = {
            "pillars_merge_source": str(block.get("pillars_merge_source", "editor")),
            "global_outline_merge_source": str(block.get("global_outline_merge_source", "editor")),
            "merge_snapshot_id": block.get("merge_snapshot_id"),
            "pillars_merge_snapshot_id": block.get("pillars_merge_snapshot_id"),
            "global_outline_merge_snapshot_id": block.get("global_outline_merge_snapshot_id"),
        }
        if to_project:
            save_merge_preferences(project_root, **kwargs)
        if to_global:
            save_global_merge_preferences(**kwargs)

    if scope_norm == "both":
        project_block = payload.get("project")
        global_block = payload.get("global")
        if not isinstance(project_block, dict) or not isinstance(global_block, dict):
            raise ValueError("project and global blocks required for scope=both")
        _apply_block(project_block, to_project=True, to_global=False)
        _apply_block(global_block, to_project=False, to_global=True)
        return {
            "scope": "both",
            "project": load_merge_preferences(project_root),
            "global": load_global_merge_preferences(),
        }

    block = payload.get(scope_norm)
    if not isinstance(block, dict):
        raise ValueError(f"{scope_norm} block required")
    _apply_block(
        block,
        to_project=scope_norm == "project",
        to_global=scope_norm == "global",
    )
    if scope_norm == "global":
        return {"scope": "global", "global": load_global_merge_preferences()}
    return {"scope": "project", "project": load_merge_preferences(project_root)}


_EXPORT_SCHEMA_VERSION = "1"


def _prefs_export_block(data: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_prefs(data)
    return {
        "pillars_merge_source": normalized["pillars_merge_source"],
        "global_outline_merge_source": normalized["global_outline_merge_source"],
        "merge_snapshot_id": normalized["merge_snapshot_id"],
        "pillars_merge_snapshot_id": normalized["pillars_merge_snapshot_id"],
        "global_outline_merge_snapshot_id": normalized["global_outline_merge_snapshot_id"],
    }


def export_merge_preferences(project_root: Path | str) -> dict[str, Any]:
    """Export project + global merge preferences as portable JSON."""
    project = load_merge_preferences(project_root)
    global_prefs = load_global_merge_preferences()
    return {
        "schema_version": _EXPORT_SCHEMA_VERSION,
        "project": _prefs_export_block(project),
        "global": _prefs_export_block(global_prefs),
    }


def import_merge_preferences(
    project_root: Path | str,
    payload: dict[str, Any],
    *,
    scope: str = "project",
) -> dict[str, Any]:
    """Import merge preferences from export JSON."""
    scope_norm = str(scope).strip().lower()
    if scope_norm not in {"project", "global", "both"}:
        raise ValueError("scope must be project, global, or both")

    def _apply_block(block: dict[str, Any], *, to_project: bool, to_global: bool) -> None:
        kwargs = {
            "pillars_merge_source": str(block.get("pillars_merge_source", "editor")),
            "global_outline_merge_source": str(block.get("global_outline_merge_source", "editor")),
            "merge_snapshot_id": block.get("merge_snapshot_id"),
            "pillars_merge_snapshot_id": block.get("pillars_merge_snapshot_id"),
            "global_outline_merge_snapshot_id": block.get("global_outline_merge_snapshot_id"),
        }
        if to_project:
            save_merge_preferences(project_root, **kwargs)
        if to_global:
            save_global_merge_preferences(**kwargs)

    if scope_norm == "both":
        project_block = payload.get("project")
        global_block = payload.get("global")
        if not isinstance(project_block, dict) or not isinstance(global_block, dict):
            raise ValueError("project and global blocks required for scope=both")
        _apply_block(project_block, to_project=True, to_global=False)
        _apply_block(global_block, to_project=False, to_global=True)
        return {
            "scope": "both",
            "project": load_merge_preferences(project_root),
            "global": load_global_merge_preferences(),
        }

    block = payload.get(scope_norm)
    if not isinstance(block, dict):
        raise ValueError(f"{scope_norm} block required")
    _apply_block(
        block,
        to_project=scope_norm == "project",
        to_global=scope_norm == "global",
    )
    if scope_norm == "global":
        return {"scope": "global", "global": load_global_merge_preferences()}
    return {"scope": "project", "project": load_merge_preferences(project_root)}
