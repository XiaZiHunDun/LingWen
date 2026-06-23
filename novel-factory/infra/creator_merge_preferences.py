"""Persist last-used creator settings merge strategy per project and globally."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infra.creator_settings_docs import MERGE_SOURCES
from infra.creator_volume_templates import is_valid_version_label, validate_version_label

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
        "depends_on": ["all_disk", "all_editor"],
        "pillars_merge_source": "disk",
        "global_outline_merge_source": "editor",
    },
    {
        "id": "pillars_editor_outline_disk",
        "name": "支柱编辑器·大纲磁盘",
        "description": "支柱保留编辑器，大纲信任磁盘",
        "builtin": True,
        "depends_on": ["all_editor", "all_disk"],
        "pillars_merge_source": "editor",
        "global_outline_merge_source": "disk",
    },
    {
        "id": "pillars_history_outline_editor",
        "name": "支柱历史·大纲编辑器",
        "description": "支柱取历史快照，大纲保留编辑器",
        "builtin": True,
        "depends_on": ["all_history", "all_editor"],
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


_FACTORY_PRESET_PACKAGES_VERSION = "1"
_FACTORY_PRESET_PREFIX = "factory_preset_"
_MAX_FACTORY_PRESET_PACKAGES = 30


def _factory_preset_packages_path() -> Path:
    from infra.studio_registry import factory_root

    return factory_root() / "infra" / ".state" / "factory_merge_preset_packages.json"


def _load_factory_preset_store() -> dict[str, Any]:
    path = _factory_preset_packages_path()
    if not path.is_file():
        return {"schema_version": _FACTORY_PRESET_PACKAGES_VERSION, "packages": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_factory_preset_store(data: dict[str, Any]) -> None:
    path = _factory_preset_packages_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _normalize_factory_preset_id(package_id: str) -> str:
    pid = str(package_id).strip().lower()
    if pid.startswith(_FACTORY_PRESET_PREFIX):
        return pid
    slug = pid.replace(" ", "_")[:24]
    return f"{_FACTORY_PRESET_PREFIX}{slug}"


def _normalize_preset_version(raw: str | None) -> str | None:
    if raw is None:
        return None
    label = str(raw).strip()
    if not label:
        return None
    return validate_version_label(label)


def _preset_row(raw: dict[str, Any], *, builtin: bool, scope: str = "project") -> dict[str, Any]:
    pillars = str(raw.get("pillars_merge_source", "editor"))
    outline = str(raw.get("global_outline_merge_source", "editor"))
    if pillars not in MERGE_SOURCES:
        pillars = "editor"
    if outline not in MERGE_SOURCES:
        outline = "editor"
    version_label = None
    if raw.get("version_label"):
        try:
            version_label = _normalize_preset_version(str(raw.get("version_label")))
        except ValueError:
            version_label = str(raw.get("version_label")).strip()[:32] or None
    depends_on_raw = raw.get("depends_on") or []
    depends_on = [str(dep).strip() for dep in depends_on_raw if str(dep).strip()] if isinstance(depends_on_raw, list) else []
    return {
        "id": str(raw["id"]),
        "name": str(raw.get("name", raw["id"])),
        "description": str(raw.get("description", "")),
        "builtin": builtin,
        "scope": scope,
        "version_label": version_label,
        "version_semver_valid": is_valid_version_label(version_label),
        "depends_on": depends_on,
        "pillars_merge_source": pillars,
        "global_outline_merge_source": outline,
    }


def list_factory_merge_preset_packages() -> list[dict[str, Any]]:
    rows = _load_factory_preset_store().get("packages") or []
    return [_preset_row(row, builtin=False, scope="factory") for row in rows if row.get("id")]


def list_merge_preset_packages(project_root: Path | str) -> list[dict[str, Any]]:
    """List built-in, project-saved, and factory merge strategy preset packages."""
    builtin = [_preset_row(row, builtin=True, scope="builtin") for row in _BUILTIN_MERGE_PRESET_PACKAGES]
    custom = [_preset_row(row, builtin=False, scope="project") for row in _load_custom_preset_packages(project_root)]
    factory = list_factory_merge_preset_packages()
    return builtin + custom + factory


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
    version_label: str | None = None,
    depends_on: list[str] | None = None,
) -> dict[str, Any]:
    if pillars_merge_source not in MERGE_SOURCES:
        raise ValueError(f"invalid pillars merge source: {pillars_merge_source!r}")
    if global_outline_merge_source not in MERGE_SOURCES:
        raise ValueError(f"invalid outline merge source: {global_outline_merge_source!r}")
    label = name.strip()
    if not label:
        raise ValueError("preset package name required")
    normalized_version = _normalize_preset_version(version_label) if version_label else None
    pid = str(package_id).strip() or label.lower().replace(" ", "_")
    path = _custom_preset_packages_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    custom = _load_custom_preset_packages(project_root)
    previous = next((row for row in custom if row.get("id") == pid), None)
    entry = {
        "id": pid,
        "name": label,
        "description": description.strip(),
        "pillars_merge_source": pillars_merge_source,
        "global_outline_merge_source": global_outline_merge_source,
        "updated_at": _now_iso(),
    }
    if normalized_version:
        entry["version_label"] = normalized_version
    if depends_on:
        deps = [dep for dep in depends_on if str(dep).strip() and dep != pid]
        if deps:
            entry["depends_on"] = list(dict.fromkeys(str(dep).strip() for dep in deps))
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
    _append_merge_preset_changelog(project_root, pid, previous, entry)
    return _preset_row(entry, builtin=False, scope="project")


def publish_merge_preset_to_factory(
    project_root: Path | str,
    package_id: str,
) -> dict[str, Any]:
    """Publish a project custom preset package to the factory library."""
    pid = str(package_id).strip()
    custom = _load_custom_preset_packages(project_root)
    match = next((row for row in custom if row.get("id") == pid), None)
    if match is None:
        raise ValueError(f"unknown project preset package: {package_id!r}")
    factory = _load_factory_preset_store()
    packages: list[dict[str, Any]] = factory.get("packages", [])
    entry = {
        "id": _normalize_factory_preset_id(pid),
        "name": str(match.get("name", pid)),
        "description": f"工厂库 · {match.get('description', '')}".strip(),
        "pillars_merge_source": match.get("pillars_merge_source", "editor"),
        "global_outline_merge_source": match.get("global_outline_merge_source", "editor"),
        "published_from": pid,
        "updated_at": _now_iso(),
    }
    if match.get("version_label"):
        entry["version_label"] = match.get("version_label")
    if match.get("depends_on"):
        entry["depends_on"] = list(match.get("depends_on") or [])
    kept = [row for row in packages if row.get("id") != entry["id"]]
    kept.insert(0, entry)
    factory["packages"] = kept[:_MAX_FACTORY_PRESET_PACKAGES]
    factory["schema_version"] = _FACTORY_PRESET_PACKAGES_VERSION
    _save_factory_preset_store(factory)
    return _preset_row(entry, builtin=False, scope="factory")


def pull_factory_merge_presets_to_project(
    project_root: Path | str,
    *,
    package_ids: list[str],
    conflict_strategies: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Import factory preset packages into the active project."""
    if not package_ids:
        raise ValueError("package_ids required")
    strategies = {
        str(key).strip(): str(value).strip()
        for key, value in (conflict_strategies or {}).items()
        if str(key).strip()
    }
    preflight = preflight_factory_merge_preset_pull(project_root, package_ids=package_ids)
    conflict_ids = {row["package_id"] for row in preflight.get("conflicts") or []}
    factory = _load_factory_preset_store()
    by_id = {row["id"]: row for row in factory.get("packages", [])}
    imported = 0
    skipped = 0
    resolved: list[str] = []
    skipped_ids: list[str] = []
    for raw_id in package_ids:
        fid = str(raw_id).strip().lower()
        if not fid.startswith(_FACTORY_PRESET_PREFIX):
            raise ValueError(f"not a factory preset package: {raw_id!r}")
        match = by_id.get(fid)
        if match is None:
            raise ValueError(f"unknown factory preset package: {raw_id!r}")
        local_id = fid.removeprefix(_FACTORY_PRESET_PREFIX) or fid
        source_id = str(match.get("published_from") or local_id).strip()
        if source_id in conflict_ids:
            strategy = (
                strategies.get(source_id)
                or strategies.get(fid)
                or strategies.get(local_id)
                or "prefer_factory"
            )
            if strategy in {"skip", "prefer_project"}:
                skipped += 1
                skipped_ids.append(source_id)
                continue
        resolved.append(fid)
        save_merge_preset_package(
            project_root,
            package_id=local_id,
            name=str(match.get("name", local_id)),
            description=str(match.get("description", "")).replace("工厂库 ·", "").strip(),
            pillars_merge_source=str(match.get("pillars_merge_source", "editor")),
            global_outline_merge_source=str(match.get("global_outline_merge_source", "editor")),
        )
        imported += 1
    return {
        "imported": imported,
        "skipped": skipped,
        "total": len(package_ids),
        "package_ids": resolved,
        "skipped_package_ids": skipped_ids,
        "packages": list_merge_preset_packages(project_root),
    }


def delete_factory_merge_preset_package(package_id: str) -> dict[str, Any]:
    fid = str(package_id).strip().lower()
    if not fid.startswith(_FACTORY_PRESET_PREFIX):
        raise ValueError("only factory preset packages can be deleted here")
    factory = _load_factory_preset_store()
    packages: list[dict[str, Any]] = factory.get("packages", [])
    kept = [row for row in packages if row.get("id") != fid]
    if len(kept) == len(packages):
        raise ValueError(f"unknown factory preset package: {package_id!r}")
    factory["packages"] = kept
    _save_factory_preset_store(factory)
    return {"id": fid, "deleted": True}


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
                "version_label": row.get("version_label"),
                "depends_on": row.get("depends_on") or [],
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
        raw_version = raw.get("version_label")
        version_label = None
        if raw_version is not None:
            version_label = str(raw_version).strip() or None
        save_merge_preset_package(
            project_root,
            package_id=pkg_id,
            name=name,
            description=str(raw.get("description", "")),
            pillars_merge_source=str(raw.get("pillars_merge_source", "editor")),
            global_outline_merge_source=str(raw.get("global_outline_merge_source", "editor")),
            version_label=version_label,
            depends_on=[str(dep) for dep in (raw.get("depends_on") or []) if str(dep).strip()],
        )
        imported += 1
    return {
        "imported": imported,
        "total": len(packages),
        "replaced": replace,
        "packages": list_merge_preset_packages(project_root),
    }


def build_merge_preset_graph(project_root: Path | str) -> dict[str, Any]:
    """Build a dependency graph for merge preset packages."""
    packages = list_merge_preset_packages(project_root)
    known_ids = {pkg["id"] for pkg in packages}
    nodes = [
        {
            "id": pkg["id"],
            "name": pkg["name"],
            "scope": pkg["scope"],
            "version_label": pkg.get("version_label"),
        }
        for pkg in packages
    ]
    edges: list[dict[str, str]] = []
    for pkg in packages:
        for dep_id in pkg.get("depends_on") or []:
            if dep_id in known_ids and dep_id != pkg["id"]:
                edges.append(
                    {
                        "from": pkg["id"],
                        "to": dep_id,
                        "relation": "depends_on",
                    },
                )
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
    }


def _semver_tuple(label: str | None) -> tuple[int, ...] | None:
    from infra.creator_volume_templates import is_valid_version_label, validate_version_label

    if not label or not is_valid_version_label(label):
        return None
    canonical = validate_version_label(str(label))
    core = canonical.lstrip("v").split("-", 1)[0]
    parts: list[int] = []
    for piece in core.split("."):
        try:
            parts.append(int(piece))
        except ValueError:
            return None
    return tuple(parts)


def _conflicts_from_packages(packages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Detect conflicts on a package list (builtin + factory + custom rows)."""
    by_id = {pkg["id"]: pkg for pkg in packages}
    adjacency: dict[str, list[str]] = {
        pkg["id"]: [dep for dep in (pkg.get("depends_on") or []) if dep in by_id]
        for pkg in packages
    }
    conflicts: list[dict[str, Any]] = []

    for pkg in packages:
        for dep_id in pkg.get("depends_on") or []:
            if dep_id not in by_id:
                conflicts.append(
                    {
                        "type": "missing_dependency",
                        "package_id": pkg["id"],
                        "dependency_id": dep_id,
                        "message": f"{pkg['id']} depends on unknown package {dep_id}",
                    },
                )
            elif dep_id == pkg["id"]:
                conflicts.append(
                    {
                        "type": "self_dependency",
                        "package_id": pkg["id"],
                        "dependency_id": dep_id,
                        "message": f"{pkg['id']} depends on itself",
                    },
                )
            else:
                pkg_ver = _semver_tuple(pkg.get("version_label"))
                dep_ver = _semver_tuple(by_id[dep_id].get("version_label"))
                if pkg_ver and dep_ver and pkg_ver < dep_ver:
                    conflicts.append(
                        {
                            "type": "semver_downgrade",
                            "package_id": pkg["id"],
                            "dependency_id": dep_id,
                            "message": (
                                f"{pkg['id']} ({pkg.get('version_label')}) "
                                f"is older than dependency {dep_id} ({by_id[dep_id].get('version_label')})"
                            ),
                        },
                    )

    visited: set[str] = set()
    stack: set[str] = set()
    cycle_path: list[str] = []

    def _dfs(node: str, path: list[str]) -> bool:
        if node in stack:
            cycle_path.extend(path[path.index(node) :] + [node])
            return True
        if node in visited:
            return False
        visited.add(node)
        stack.add(node)
        for nxt in adjacency.get(node, []):
            if _dfs(nxt, path + [node]):
                return True
        stack.remove(node)
        return False

    for node_id in adjacency:
        cycle_path.clear()
        if _dfs(node_id, []):
            conflicts.append(
                {
                    "type": "circular_dependency",
                    "package_id": cycle_path[0] if cycle_path else node_id,
                    "path": cycle_path,
                    "message": " -> ".join(cycle_path),
                },
            )
            break

    return conflicts


def detect_merge_preset_conflicts(project_root: Path | str) -> dict[str, Any]:
    """Detect dependency cycles, missing deps, and semver downgrade conflicts."""
    packages = list_merge_preset_packages(project_root)
    conflicts = _conflicts_from_packages(packages)
    return {
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
    }


def _virtual_packages_after_import(
    project_root: Path | str,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    incoming = payload.get("packages")
    if not isinstance(incoming, list):
        raise ValueError("packages array required")
    custom_by_id = {row["id"]: dict(row) for row in _load_custom_preset_packages(project_root)}
    for raw in incoming:
        if not isinstance(raw, dict):
            continue
        pkg_id = str(raw.get("id", "")).strip()
        name = str(raw.get("name", "")).strip()
        if not pkg_id or not name:
            continue
        entry = {
            "id": pkg_id,
            "name": name,
            "description": str(raw.get("description", "")),
            "pillars_merge_source": str(raw.get("pillars_merge_source", "editor")),
            "global_outline_merge_source": str(raw.get("global_outline_merge_source", "editor")),
        }
        raw_version = raw.get("version_label")
        if raw_version is not None and str(raw_version).strip():
            entry["version_label"] = str(raw_version).strip()
        deps = [str(dep) for dep in (raw.get("depends_on") or []) if str(dep).strip()]
        if deps:
            entry["depends_on"] = deps
        custom_by_id[pkg_id] = entry
    builtin = [_preset_row(row, builtin=True, scope="builtin") for row in _BUILTIN_MERGE_PRESET_PACKAGES]
    factory = list_factory_merge_preset_packages()
    custom = [_preset_row(row, builtin=False, scope="project") for row in custom_by_id.values()]
    return builtin + factory + custom


def preflight_merge_preset_import(
    project_root: Path | str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Detect conflicts if import payload were applied without saving."""
    packages = _virtual_packages_after_import(project_root, payload)
    incoming = payload.get("packages") or []
    conflicts = _conflicts_from_packages(packages)
    return {
        "would_import": len([raw for raw in incoming if isinstance(raw, dict)]),
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
        "blocked": len(conflicts) > 0,
    }


def suggest_merge_preset_fixes(project_root: Path | str) -> dict[str, Any]:
    """Suggest one-click fixes for detected merge preset conflicts."""
    report = detect_merge_preset_conflicts(project_root)
    packages = {pkg["id"]: pkg for pkg in list_merge_preset_packages(project_root)}
    fixes: list[dict[str, Any]] = []

    for idx, conflict in enumerate(report["conflicts"]):
        pkg_id = str(conflict.get("package_id", ""))
        pkg = packages.get(pkg_id, {})
        editable = pkg.get("scope") == "project" and not pkg.get("builtin")
        ctype = str(conflict.get("type", ""))

        if ctype in {"missing_dependency", "self_dependency"}:
            dep_id = str(conflict.get("dependency_id", ""))
            fixes.append(
                {
                    "id": f"fix_{idx}",
                    "conflict_type": ctype,
                    "package_id": pkg_id,
                    "action": "remove_dependency",
                    "dependency_id": dep_id,
                    "label": f"从 {pkg_id} 移除依赖 {dep_id}",
                    "applicable": editable,
                },
            )
        elif ctype == "semver_downgrade":
            dep_id = str(conflict.get("dependency_id", ""))
            dep_ver = packages.get(dep_id, {}).get("version_label")
            fixes.append(
                {
                    "id": f"fix_{idx}",
                    "conflict_type": ctype,
                    "package_id": pkg_id,
                    "action": "bump_version",
                    "version_label": dep_ver,
                    "label": f"将 {pkg_id} 版本提升至 {dep_ver or '依赖版本'}",
                    "applicable": editable and bool(dep_ver),
                },
            )
        elif ctype == "circular_dependency":
            path = list(conflict.get("path") or [])
            if len(path) >= 2:
                from_pkg = str(path[-2])
                dep_id = str(path[-1])
                from_meta = packages.get(from_pkg, {})
                fixes.append(
                    {
                        "id": f"fix_{idx}",
                        "conflict_type": ctype,
                        "package_id": from_pkg,
                        "action": "remove_dependency",
                        "dependency_id": dep_id,
                        "label": f"打断环：从 {from_pkg} 移除对 {dep_id} 的依赖",
                        "applicable": from_meta.get("scope") == "project" and not from_meta.get("builtin"),
                    },
                )

    return {"fix_count": len(fixes), "fixes": fixes}


def apply_merge_preset_fix(
    project_root: Path | str,
    *,
    package_id: str,
    action: str,
    dependency_id: str | None = None,
    version_label: str | None = None,
) -> dict[str, Any]:
    """Apply a suggested fix to a project custom merge preset package."""
    pid = str(package_id).strip()
    if not pid:
        raise ValueError("package_id required")
    custom = _load_custom_preset_packages(project_root)
    target: dict[str, Any] | None = None
    for row in custom:
        if row.get("id") == pid:
            target = row
            break
    if target is None:
        raise ValueError(f"editable package not found: {package_id!r}")

    act = str(action).strip().lower()
    if act == "remove_dependency":
        dep = str(dependency_id or "").strip()
        if not dep:
            raise ValueError("dependency_id required for remove_dependency")
        deps = [d for d in (target.get("depends_on") or []) if d != dep]
        if deps:
            target["depends_on"] = deps
        else:
            target.pop("depends_on", None)
    elif act == "bump_version":
        label = _normalize_preset_version(version_label)
        if not label:
            raise ValueError("version_label required for bump_version")
        target["version_label"] = label
    else:
        raise ValueError(f"unsupported fix action: {action!r}")

    path = _custom_preset_packages_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"schema_version": _PRESET_PACKAGES_VERSION, "packages": custom[:20]},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    remaining = detect_merge_preset_conflicts(project_root)
    return {
        "package_id": pid,
        "action": act,
        "conflict_count": remaining["conflict_count"],
        "package": _preset_row(target, builtin=False, scope="project"),
    }


def apply_all_merge_preset_fixes(project_root: Path | str) -> dict[str, Any]:
    """Apply all applicable suggested fixes until no more apply in one pass."""
    applied = 0
    last_conflict_count = -1
    while True:
        fixes = suggest_merge_preset_fixes(project_root)
        applicable = [row for row in fixes["fixes"] if row.get("applicable")]
        if not applicable:
            break
        report = detect_merge_preset_conflicts(project_root)
        if report["conflict_count"] == last_conflict_count:
            break
        last_conflict_count = report["conflict_count"]
        fix = applicable[0]
        apply_merge_preset_fix(
            project_root,
            package_id=str(fix["package_id"]),
            action=str(fix["action"]),
            dependency_id=fix.get("dependency_id"),
            version_label=fix.get("version_label"),
        )
        applied += 1
        if applied > 20:
            break
    remaining = detect_merge_preset_conflicts(project_root)
    return {
        "applied": applied,
        "conflict_count": remaining["conflict_count"],
    }


def _preset_import_fields(pkg: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": str(pkg.get("name", "")),
        "description": str(pkg.get("description", "")),
        "pillars_merge_source": str(pkg.get("pillars_merge_source", "editor")),
        "global_outline_merge_source": str(pkg.get("global_outline_merge_source", "editor")),
        "version_label": pkg.get("version_label"),
        "depends_on": list(pkg.get("depends_on") or []),
    }


def preview_merge_preset_import_diff(
    project_root: Path | str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Preview added/updated/removed packages before import."""
    existing = {row["id"]: row for row in _load_custom_preset_packages(project_root)}
    incoming = payload.get("packages") or []
    if not isinstance(incoming, list):
        raise ValueError("packages array required")
    replace = bool(payload.get("replace"))
    added: list[str] = []
    updated: list[dict[str, Any]] = []
    unchanged: list[str] = []
    incoming_ids: set[str] = set()
    for raw in incoming:
        if not isinstance(raw, dict):
            continue
        pkg_id = str(raw.get("id", "")).strip()
        if not pkg_id:
            continue
        incoming_ids.add(pkg_id)
        if pkg_id not in existing:
            added.append(pkg_id)
            continue
        before = _preset_import_fields(existing[pkg_id])
        after = _preset_import_fields(raw)
        if before != after:
            changed_fields = [key for key in before if before[key] != after[key]]
            updated.append({"package_id": pkg_id, "changed_fields": changed_fields})
        else:
            unchanged.append(pkg_id)
    removed = [pid for pid in existing if pid not in incoming_ids] if replace else []
    return {
        "added": added,
        "updated": updated,
        "removed": removed,
        "unchanged_count": len(unchanged),
        "replace": replace,
    }


def toposort_merge_preset_packages(project_root: Path | str) -> dict[str, Any]:
    """Topological order for project custom preset packages."""
    all_pkgs = list_merge_preset_packages(project_root)
    known = {pkg["id"]: pkg for pkg in all_pkgs}
    project_ids = [pkg["id"] for pkg in all_pkgs if pkg.get("scope") == "project"]
    in_degree = {pid: 0 for pid in project_ids}
    adjacency: dict[str, list[str]] = {pid: [] for pid in project_ids}
    for pid in project_ids:
        pkg = known[pid]
        for dep_id in pkg.get("depends_on") or []:
            if dep_id in project_ids and dep_id != pid:
                adjacency[dep_id].append(pid)
                in_degree[pid] += 1
    queue = [pid for pid in project_ids if in_degree[pid] == 0]
    order: list[str] = []
    while queue:
        node = queue.pop(0)
        order.append(node)
        for nxt in adjacency.get(node, []):
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                queue.append(nxt)
    cyclic = len(order) != len(project_ids)
    graph = build_merge_preset_graph(project_root)
    order_index = {pid: idx for idx, pid in enumerate(order)}
    nodes = [
        {**node, "topo_index": order_index.get(node["id"])}
        for node in graph.get("nodes", [])
        if node.get("id") in order_index or node.get("scope") != "project"
    ]
    project_edges = [
        edge
        for edge in graph.get("edges", [])
        if edge.get("from") in order_index and edge.get("to") in order_index
    ]
    return {
        "order": order,
        "cyclic": cyclic,
        "package_count": len(project_ids),
        "nodes": nodes,
        "edges": project_edges,
        "edge_count": len(project_edges),
    }


def apply_toposort_merge_preset_order(project_root: Path | str) -> dict[str, Any]:
    """Reorder project custom packages file by topological sort."""
    topo = toposort_merge_preset_packages(project_root)
    if topo["cyclic"]:
        raise ValueError("cannot reorder: cyclic dependencies among project packages")
    custom = _load_custom_preset_packages(project_root)
    by_id = {row["id"]: row for row in custom}
    ordered = [by_id[pid] for pid in topo["order"] if pid in by_id]
    for row in custom:
        if row["id"] not in topo["order"]:
            ordered.append(row)
    path = _custom_preset_packages_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"schema_version": _PRESET_PACKAGES_VERSION, "packages": ordered[:20]},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {"reordered": len(ordered), "order": topo["order"]}


def _preset_content_signature(pkg: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": str(pkg.get("name", "")),
        "description": str(pkg.get("description", "")),
        "pillars_merge_source": str(pkg.get("pillars_merge_source", "editor")),
        "global_outline_merge_source": str(pkg.get("global_outline_merge_source", "editor")),
        "version_label": pkg.get("version_label"),
        "depends_on": sorted(str(d) for d in (pkg.get("depends_on") or [])),
    }


def detect_factory_merge_preset_conflicts(project_root: Path | str) -> dict[str, Any]:
    """Detect project/factory preset packages that collide on id or published_from."""
    packages = list_merge_preset_packages(project_root)
    project = {p["id"]: p for p in packages if p.get("scope") == "project"}
    factory = {p["id"]: p for p in packages if p.get("scope") == "factory"}
    conflicts: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _append_conflict(*, package_id: str, factory_package_id: str, project_pkg: dict, factory_pkg: dict) -> None:
        key = f"{package_id}:{factory_package_id}"
        if key in seen:
            return
        seen.add(key)
        conflicts.append(
            {
                "type": "factory_project_collision",
                "package_id": package_id,
                "factory_package_id": factory_package_id,
                "message": f"project {package_id} differs from factory {factory_package_id}",
            },
        )

    for pkg_id in sorted(set(project) & set(factory)):
        if _preset_content_signature(project[pkg_id]) != _preset_content_signature(factory[pkg_id]):
            _append_conflict(
                package_id=pkg_id,
                factory_package_id=pkg_id,
                project_pkg=project[pkg_id],
                factory_pkg=factory[pkg_id],
            )

    for factory_id, factory_pkg in factory.items():
        source_id = str(factory_pkg.get("published_from") or "").strip()
        if not source_id and factory_id.startswith(_FACTORY_PRESET_PREFIX):
            source_id = factory_id[len(_FACTORY_PRESET_PREFIX) :]
        if not source_id or source_id not in project:
            continue
        if _preset_content_signature(project[source_id]) != _preset_content_signature(factory_pkg):
            _append_conflict(
                package_id=source_id,
                factory_package_id=factory_id,
                project_pkg=project[source_id],
                factory_pkg=factory_pkg,
            )

    return {"conflict_count": len(conflicts), "conflicts": conflicts}


def resolve_factory_merge_preset_conflict(
    project_root: Path | str,
    *,
    package_id: str,
    strategy: str = "prefer_factory",
) -> dict[str, Any]:
    """Resolve factory/project preset collision."""
    pid = str(package_id).strip()
    if not pid:
        raise ValueError("package_id required")
    strat = str(strategy).strip().lower()
    factory_pkgs = {p["id"]: p for p in list_factory_merge_preset_packages()}
    if pid not in factory_pkgs:
        raise ValueError(f"factory preset not found: {package_id!r}")
    custom = _load_custom_preset_packages(project_root)
    if strat == "prefer_factory":
        kept = [row for row in custom if row.get("id") != pid]
        path = _custom_preset_packages_path(project_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {"schema_version": _PRESET_PACKAGES_VERSION, "packages": kept[:20]},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return {
            "package_id": pid,
            "strategy": strat,
            "action": "removed_project_copy",
            "packages": list_merge_preset_packages(project_root),
        }
    if strat == "prefer_project":
        return {
            "package_id": pid,
            "strategy": strat,
            "action": "kept_project_copy",
            "packages": list_merge_preset_packages(project_root),
        }
    raise ValueError(f"unsupported strategy: {strategy!r}")


_PRESET_CHANGELOG_VERSION = "1"
_MAX_PRESET_CHANGELOG = 20


def _preset_changelog_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_merge_preset_changelog.json"


def _load_preset_changelog_store(project_root: Path | str) -> dict[str, Any]:
    path = _preset_changelog_path(project_root)
    if not path.is_file():
        return {"schema_version": _PRESET_CHANGELOG_VERSION, "packages": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _append_merge_preset_changelog(
    project_root: Path | str,
    package_id: str,
    before: dict[str, Any] | None,
    after: dict[str, Any],
) -> None:
    before_sig = _preset_content_signature(before) if before else None
    after_sig = _preset_content_signature(after)
    if before_sig == after_sig:
        return
    changed_fields = []
    if before_sig:
        changed_fields = [key for key in after_sig if before_sig.get(key) != after_sig.get(key)]
    else:
        changed_fields = list(after_sig.keys())
    store = _load_preset_changelog_store(project_root)
    packages = store.setdefault("packages", {})
    rows: list[dict[str, Any]] = list(packages.get(package_id) or [])
    rows.insert(
        0,
        {
            "changed_at": _now_iso(),
            "action": "update" if before else "create",
            "changed_fields": changed_fields,
            "snapshot": after_sig,
        },
    )
    packages[package_id] = rows[:_MAX_PRESET_CHANGELOG]
    path = _preset_changelog_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def list_merge_preset_changelog(
    project_root: Path | str,
    *,
    package_id: str,
    limit: int = 10,
) -> dict[str, Any]:
    pid = str(package_id).strip()
    if not pid:
        raise ValueError("package_id required")
    store = _load_preset_changelog_store(project_root)
    rows = list((store.get("packages") or {}).get(pid) or [])
    return {"package_id": pid, "entry_count": len(rows), "entries": rows[:limit]}


def preflight_factory_merge_preset_pull(
    project_root: Path | str,
    *,
    package_ids: list[str],
) -> dict[str, Any]:
    """Detect conflicts before pulling factory presets into the project."""
    if not package_ids:
        raise ValueError("package_ids required")
    factory = _load_factory_preset_store()
    by_id = {row["id"]: row for row in factory.get("packages", [])}
    custom = {row["id"]: row for row in _load_custom_preset_packages(project_root)}
    conflicts: list[dict[str, Any]] = []
    for raw_id in package_ids:
        fid = str(raw_id).strip().lower()
        if not fid.startswith(_FACTORY_PRESET_PREFIX):
            raise ValueError(f"not a factory preset package: {raw_id!r}")
        match = by_id.get(fid)
        if match is None:
            raise ValueError(f"unknown factory preset package: {raw_id!r}")
        local_id = fid.removeprefix(_FACTORY_PRESET_PREFIX) or fid
        source_id = str(match.get("published_from") or local_id).strip()
        if source_id in custom:
            factory_row = {
                "id": source_id,
                "name": match.get("name"),
                "description": match.get("description"),
                "pillars_merge_source": match.get("pillars_merge_source"),
                "global_outline_merge_source": match.get("global_outline_merge_source"),
                "version_label": match.get("version_label"),
                "depends_on": match.get("depends_on"),
            }
            if _preset_content_signature(custom[source_id]) != _preset_content_signature(factory_row):
                conflicts.append(
                    {
                        "type": "factory_pull_overwrite",
                        "package_id": source_id,
                        "factory_package_id": fid,
                        "message": f"pulling {fid} would overwrite project preset {source_id}",
                    },
                )
    return {
        "would_import": len(package_ids),
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
        "blocked": bool(conflicts),
    }


def preview_merge_preset_changelog_diff(
    project_root: Path | str,
    *,
    package_id: str,
    entry_index: int = 0,
) -> dict[str, Any]:
    """Field-level diff between a changelog entry and the previous snapshot."""
    pid = str(package_id).strip()
    if not pid:
        raise ValueError("package_id required")
    if entry_index < 0:
        raise ValueError("entry_index must be >= 0")
    changelog = list_merge_preset_changelog(project_root, package_id=pid, limit=entry_index + 2)
    entries = changelog.get("entries") or []
    if entry_index >= len(entries):
        raise ValueError(f"changelog entry index out of range: {entry_index}")
    current_entry = entries[entry_index]
    current = current_entry.get("snapshot") or {}
    previous_entry = entries[entry_index + 1] if entry_index + 1 < len(entries) else None
    previous = previous_entry.get("snapshot") if previous_entry else None
    keys = sorted(set(current.keys()) | (set(previous.keys()) if isinstance(previous, dict) else set()))
    changes: list[dict[str, Any]] = []
    for key in keys:
        before = previous.get(key) if isinstance(previous, dict) else None
        after = current.get(key)
        if before != after:
            changes.append({"field": key, "before": before, "after": after})
    return {
        "package_id": pid,
        "entry_index": entry_index,
        "changed_at": current_entry.get("changed_at"),
        "action": current_entry.get("action"),
        "change_count": len(changes),
        "changes": changes,
    }

