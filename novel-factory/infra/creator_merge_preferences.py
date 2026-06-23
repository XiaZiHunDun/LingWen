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


_PRESET_PACKAGES_VERSION = "1"

_BUILTIN_MERGE_PRESET_PACKAGES: list[dict[str, Any]] = [
    {
        "id": "all_disk",
        "name": "全选磁盘",
        "description": "支柱与全局大纲均取磁盘版本",
        "builtin": True,
        "pillars_merge_source": "disk",
        "global_outline_merge_source": "disk",
    },
    {
        "id": "all_history",
        "name": "全选历史",
        "description": "支柱与全局大纲均取历史快照",
        "builtin": True,
        "pillars_merge_source": "history",
        "global_outline_merge_source": "history",
    },
    {
        "id": "all_editor",
        "name": "全选编辑器",
        "description": "支柱与全局大纲均保留编辑器内容",
        "builtin": True,
        "pillars_merge_source": "editor",
        "global_outline_merge_source": "editor",
    },
    {
        "id": "pillars_disk_outline_editor",
        "name": "支柱磁盘·大纲编辑器",
        "description": "支柱信任磁盘，大纲保留编辑器",
        "builtin": True,
        "pillars_merge_source": "disk",
        "global_outline_merge_source": "editor",
    },
    {
        "id": "pillars_editor_outline_disk",
        "name": "支柱编辑器·大纲磁盘",
        "description": "支柱保留编辑器，大纲信任磁盘",
        "builtin": True,
        "pillars_merge_source": "editor",
        "global_outline_merge_source": "disk",
    },
    {
        "id": "pillars_history_outline_editor",
        "name": "支柱历史·大纲编辑器",
        "description": "支柱取历史快照，大纲保留编辑器",
        "builtin": True,
        "pillars_merge_source": "history",
        "global_outline_merge_source": "editor",
    },
]


def _custom_preset_packages_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_merge_preset_packages.json"


def _load_custom_preset_packages(project_root: Path | str) -> list[dict[str, Any]]:
    path = _custom_preset_packages_path(project_root)
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("packages") or []
    return [row for row in rows if isinstance(row, dict) and row.get("id")]


def _preset_row(raw: dict[str, Any], *, builtin: bool) -> dict[str, Any]:
    pillars = str(raw.get("pillars_merge_source", "editor"))
    outline = str(raw.get("global_outline_merge_source", "editor"))
    if pillars not in MERGE_SOURCES:
        pillars = "editor"
    if outline not in MERGE_SOURCES:
        outline = "editor"
    return {
        "id": str(raw["id"]),
        "name": str(raw.get("name", raw["id"])),
        "description": str(raw.get("description", "")),
        "builtin": builtin,
        "pillars_merge_source": pillars,
        "global_outline_merge_source": outline,
    }


def list_merge_preset_packages(project_root: Path | str) -> list[dict[str, Any]]:
    """List built-in and project-saved merge strategy preset packages."""
    builtin = [_preset_row(row, builtin=True) for row in _BUILTIN_MERGE_PRESET_PACKAGES]
    custom = [_preset_row(row, builtin=False) for row in _load_custom_preset_packages(project_root)]
    return builtin + custom


def get_merge_preset_package(project_root: Path | str, package_id: str) -> dict[str, Any]:
    pid = str(package_id).strip()
    for row in list_merge_preset_packages(project_root):
        if row["id"] == pid:
            return row
    raise ValueError(f"unknown merge preset package: {package_id!r}")


def save_merge_preset_package(
    project_root: Path | str,
    *,
    package_id: str,
    name: str,
    description: str = "",
    pillars_merge_source: str,
    global_outline_merge_source: str,
) -> dict[str, Any]:
    if pillars_merge_source not in MERGE_SOURCES:
        raise ValueError(f"invalid pillars merge source: {pillars_merge_source!r}")
    if global_outline_merge_source not in MERGE_SOURCES:
        raise ValueError(f"invalid outline merge source: {global_outline_merge_source!r}")
    label = name.strip()
    if not label:
        raise ValueError("preset package name required")
    pid = str(package_id).strip() or label.lower().replace(" ", "_")
    entry = {
        "id": pid,
        "name": label,
        "description": description.strip(),
        "pillars_merge_source": pillars_merge_source,
        "global_outline_merge_source": global_outline_merge_source,
        "updated_at": _now_iso(),
    }
    path = _custom_preset_packages_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    custom = _load_custom_preset_packages(project_root)
    kept = [row for row in custom if row.get("id") != pid]
    kept.insert(0, entry)
    path.write_text(
        json.dumps(
            {"schema_version": _PRESET_PACKAGES_VERSION, "packages": kept[:20]},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return _preset_row(entry, builtin=False)


_PRESET_PACKAGES_EXPORT_VERSION = "1"


def export_merge_preset_packages(project_root: Path | str) -> dict[str, Any]:
    """Export project custom merge preset packages for sharing."""
    custom = _load_custom_preset_packages(project_root)
    return {
        "schema_version": _PRESET_PACKAGES_EXPORT_VERSION,
        "packages": [
            {
                "id": row["id"],
                "name": row.get("name", row["id"]),
                "description": row.get("description", ""),
                "pillars_merge_source": row.get("pillars_merge_source", "editor"),
                "global_outline_merge_source": row.get("global_outline_merge_source", "editor"),
            }
            for row in custom
        ],
        "count": len(custom),
    }


def import_merge_preset_packages(
    project_root: Path | str,
    payload: dict[str, Any],
    *,
    replace: bool = False,
) -> dict[str, Any]:
    """Import shared merge preset packages into the project."""
    packages = payload.get("packages")
    if not isinstance(packages, list):
        raise ValueError("packages array required")
    if replace:
        path = _custom_preset_packages_path(project_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"schema_version": _PRESET_PACKAGES_VERSION, "packages": []}, ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
    imported = 0
    for raw in packages:
        if not isinstance(raw, dict):
            continue
        pkg_id = str(raw.get("id", "")).strip()
        name = str(raw.get("name", "")).strip()
        if not pkg_id or not name:
            continue
        save_merge_preset_package(
            project_root,
            package_id=pkg_id,
            name=name,
            description=str(raw.get("description", "")),
            pillars_merge_source=str(raw.get("pillars_merge_source", "editor")),
            global_outline_merge_source=str(raw.get("global_outline_merge_source", "editor")),
        )
        imported += 1
    return {
        "imported": imported,
        "total": len(packages),
        "replaced": replace,
        "packages": list_merge_preset_packages(project_root),
    }

