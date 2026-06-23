"""Preset and project-custom volume plan templates."""
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

_BUILTIN_META: dict[str, dict[str, str]] = {
    "three_act": {
        "name": "三幕式",
        "description": "建置 → 对抗 → 结局（约 25% / 50% / 25%）",
    },
    "five_volume": {
        "name": "五卷长篇",
        "description": "按章数均分为五卷",
    },
    "companion_short": {
        "name": "陪伴短篇",
        "description": "单卷覆盖全书（适合 ≤30 章）",
    },
}

_CUSTOM_PREFIX = "custom_"
_FACTORY_PREFIX = "factory_"
_CUSTOM_STATE_VERSION = "1"
_FACTORY_STATE_VERSION = "1"
_MAX_CUSTOM_TEMPLATES = 5
_MAX_FACTORY_TEMPLATES = 20
_MAX_VERSION_LABEL = 32
_MAX_CHANGELOG_ENTRIES = 20
_SLUG_RE = re.compile(r"[^a-z0-9]+")
_SEMVER_RE = re.compile(
    r"^v?(?P<major>\d+)\.(?P<minor>\d+)(?:\.(?P<patch>\d+))?(?:-(?P<prerelease>[a-zA-Z0-9][a-zA-Z0-9.-]*))?$",
    re.IGNORECASE,
)


def validate_version_label(raw: str) -> str:
    """Validate and canonicalize a semver version label."""
    label = str(raw).strip()
    if not label:
        raise ValueError("version label required")
    match = _SEMVER_RE.match(label)
    if not match:
        raise ValueError(
            f"invalid semver version label: {label!r} (expected v1.2.3 or 1.2.3-beta)",
        )
    major = int(match.group("major"))
    minor = int(match.group("minor"))
    patch = int(match.group("patch") or 0)
    prerelease = match.group("prerelease")
    canonical = f"v{major}.{minor}.{patch}"
    if prerelease:
        canonical += f"-{prerelease}"
    return canonical[:_MAX_VERSION_LABEL]


def is_valid_version_label(raw: str | None) -> bool:
    if raw is None:
        return True
    label = str(raw).strip()
    if not label:
        return True
    return _SEMVER_RE.match(label) is not None


def _normalize_version_label(raw: str | None, *, strict: bool = False) -> str | None:
    if raw is None:
        return None
    label = str(raw).strip()
    if not label:
        return None
    if strict:
        return validate_version_label(label)
    if _SEMVER_RE.match(label):
        return validate_version_label(label)
    return label[:_MAX_VERSION_LABEL]


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _append_version_changelog(
    item: dict[str, Any],
    *,
    new_label: str | None,
    old_label: str | None = None,
) -> None:
    """Append a version change entry when the label actually changes."""
    normalized_new = _normalize_version_label(new_label)
    normalized_old = _normalize_version_label(old_label)
    if normalized_new == normalized_old:
        return
    changelog: list[dict[str, Any]] = list(item.get("version_changelog") or [])
    changelog.insert(
        0,
        {
            "version_label": normalized_new,
            "previous_label": normalized_old,
            "changed_at": _now_iso(),
        },
    )
    item["version_changelog"] = changelog[:_MAX_CHANGELOG_ENTRIES]


def _changelog_for_list(item: dict[str, Any]) -> list[dict[str, Any]]:
    rows = item.get("version_changelog") or []
    return [
        {
            "version_label": row.get("version_label"),
            "previous_label": row.get("previous_label"),
            "changed_at": row.get("changed_at"),
        }
        for row in rows[:5]
    ]


def get_template_version_changelog(
    project_root: Path | str | None,
    template_id: str,
) -> list[dict[str, Any]]:
    """Return version changelog for a custom or factory template."""
    tid = template_id.strip().lower()
    if tid.startswith(_CUSTOM_PREFIX):
        if project_root is None:
            raise ValueError("project root required for custom templates")
        store = _load_custom_store(project_root)
        for item in store.get("templates", []):
            if item.get("id") == tid:
                return list(item.get("version_changelog") or [])
        raise ValueError(f"unknown template: {template_id!r}")
    if tid.startswith(_FACTORY_PREFIX):
        factory = _load_factory_store()
        for item in factory.get("templates", []):
            if item.get("id") == tid:
                return list(item.get("version_changelog") or [])
        raise ValueError(f"unknown factory template: {template_id!r}")
    raise ValueError(f"unknown template: {template_id!r}")


def _template_list_row(item: dict[str, Any], scope: str, *, default_description: str) -> dict[str, Any]:
    return {
        "id": item["id"],
        "name": item["name"],
        "description": str(item.get("description", default_description)),
        "builtin": False,
        "scope": scope,
        "version_label": _normalize_version_label(item.get("version_label")),
        "version_semver_valid": is_valid_version_label(item.get("version_label")),
        "version_changelog": _changelog_for_list(item),
    }


def _custom_templates_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "custom_volume_templates.json"


def _factory_templates_path() -> Path:
    from infra.studio_registry import factory_root

    return factory_root() / "infra" / ".state" / "factory_volume_templates.json"


def _chunk_end(max_chapter: int, part_index: int, part_count: int) -> int:
    if part_index >= part_count:
        return max_chapter
    return min(max_chapter, (max_chapter * part_index) // part_count)


def _load_custom_store(project_root: Path | str) -> dict[str, Any]:
    path = _custom_templates_path(project_root)
    if not path.is_file():
        return {"schema_version": _CUSTOM_STATE_VERSION, "templates": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_custom_store(project_root: Path | str, data: dict[str, Any]) -> None:
    path = _custom_templates_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_factory_store() -> dict[str, Any]:
    path = _factory_templates_path()
    if not path.is_file():
        return {"schema_version": _FACTORY_STATE_VERSION, "templates": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_factory_store(data: dict[str, Any]) -> None:
    path = _factory_templates_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _normalize_template_id(name: str) -> str:
    slug = _SLUG_RE.sub("-", name.strip().lower()).strip("-")
    return f"{_CUSTOM_PREFIX}{slug[:20]}-{uuid.uuid4().hex[:6]}"


def _normalize_factory_template_id(name: str) -> str:
    slug = _SLUG_RE.sub("-", name.strip().lower()).strip("-")
    return f"{_FACTORY_PREFIX}{slug[:20]}-{uuid.uuid4().hex[:6]}"


def _scale_volumes(
    volumes: list[dict[str, Any]],
    source_max: int,
    target_max: int,
) -> list[dict[str, Any]]:
    if source_max == target_max or source_max < 1:
        return [
            {
                "label": str(v["label"]),
                "start_chapter": int(v["start_chapter"]),
                "end_chapter": int(v["end_chapter"]),
                "core_conflict": str(v.get("core_conflict", "")),
                "locked": False,
            }
            for v in volumes
        ]
    scaled: list[dict[str, Any]] = []
    for vol in volumes:
        start = max(
            1,
            round((int(vol["start_chapter"]) - 1) * target_max / source_max) + 1,
        )
        end = max(
            start,
            round(int(vol["end_chapter"]) * target_max / source_max),
        )
        end = min(end, target_max)
        scaled.append(
            {
                "label": str(vol["label"]),
                "start_chapter": start,
                "end_chapter": end,
                "core_conflict": str(vol.get("core_conflict", "")),
                "locked": False,
            },
        )
    return scaled


def list_volume_templates(project_root: Path | str | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {"id": template_id, **meta, "builtin": True, "scope": "builtin"}
        for template_id, meta in _BUILTIN_META.items()
    ]
    for item in _load_factory_store().get("templates", []):
        rows.append(
            _template_list_row(item, "factory", default_description="工厂共享模板"),
        )
    if project_root is None:
        return rows
    store = _load_custom_store(project_root)
    for item in store.get("templates", []):
        rows.append(
            _template_list_row(item, "project", default_description="项目自定义模板"),
        )
    return rows


def list_factory_volume_templates() -> list[dict[str, Any]]:
    return [
        _template_list_row(item, "factory", default_description="工厂共享模板")
        for item in _load_factory_store().get("templates", [])
    ]


def save_custom_volume_template(
    project_root: Path | str,
    *,
    name: str,
    volumes: list[dict[str, Any]],
    max_chapter: int,
    description: str | None = None,
    version_label: str | None = None,
) -> dict[str, Any]:
    label = name.strip()
    if not label:
        raise ValueError("template name required")
    if not volumes:
        raise ValueError("volumes required")
    store = _load_custom_store(project_root)
    templates: list[dict[str, Any]] = store.get("templates", [])
    entry = {
        "id": _normalize_template_id(label),
        "name": label,
        "description": (description or "保存自当前卷纲").strip(),
        "version_label": _normalize_version_label(version_label, strict=True) if version_label else None,
        "version_changelog": [],
        "source_max_chapter": max_chapter,
        "volumes": [
            {
                "label": str(v["label"]),
                "start_chapter": int(v["start_chapter"]),
                "end_chapter": int(v["end_chapter"]),
                "core_conflict": str(v.get("core_conflict", "")),
                "locked": False,
            }
            for v in volumes
        ],
    }
    if entry["version_label"]:
        _append_version_changelog(entry, new_label=entry["version_label"], old_label=None)
    templates.insert(0, entry)
    store["templates"] = templates[:_MAX_CUSTOM_TEMPLATES]
    store["schema_version"] = _CUSTOM_STATE_VERSION
    _save_custom_store(project_root, store)
    return entry


def delete_custom_volume_template(project_root: Path | str, template_id: str) -> dict[str, Any]:
    """Remove a project-scoped custom template. Builtin templates cannot be deleted."""
    tid = template_id.strip().lower()
    if not tid.startswith(_CUSTOM_PREFIX):
        raise ValueError("builtin templates cannot be deleted")
    store = _load_custom_store(project_root)
    templates: list[dict[str, Any]] = store.get("templates", [])
    kept = [row for row in templates if row.get("id") != tid]
    if len(kept) == len(templates):
        raise ValueError(f"unknown template: {template_id!r}")
    store["templates"] = kept
    _save_custom_store(project_root, store)
    return {"id": tid, "deleted": True}


def rename_custom_volume_template(
    project_root: Path | str,
    template_id: str,
    *,
    name: str,
    description: str | None = None,
    version_label: str | None = None,
) -> dict[str, Any]:
    """Rename a project-scoped custom template."""
    tid = template_id.strip().lower()
    if not tid.startswith(_CUSTOM_PREFIX):
        raise ValueError("builtin templates cannot be renamed")
    label = name.strip()
    if not label:
        raise ValueError("template name required")
    store = _load_custom_store(project_root)
    for item in store.get("templates", []):
        if item.get("id") == tid:
            item["name"] = label
            if description is not None:
                item["description"] = description.strip()
            if version_label is not None:
                old_label = item.get("version_label")
                item["version_label"] = (
                    _normalize_version_label(version_label, strict=True)
                    if str(version_label).strip()
                    else None
                )
                _append_version_changelog(
                    item,
                    new_label=item.get("version_label"),
                    old_label=old_label,
                )
            _save_custom_store(project_root, store)
            return {
                "id": tid,
                "name": item["name"],
                "description": str(item.get("description", "")),
                "version_label": _normalize_version_label(item.get("version_label")),
            }
    raise ValueError(f"unknown template: {template_id!r}")


def set_custom_template_version_label(
    project_root: Path | str,
    template_id: str,
    *,
    version_label: str | None,
) -> dict[str, Any]:
    """Set version label on a project custom template."""
    tid = template_id.strip().lower()
    if not tid.startswith(_CUSTOM_PREFIX):
        raise ValueError("builtin templates cannot be versioned")
    store = _load_custom_store(project_root)
    for item in store.get("templates", []):
        if item.get("id") == tid:
            old_label = item.get("version_label")
            item["version_label"] = (
                _normalize_version_label(version_label, strict=True)
                if version_label and str(version_label).strip()
                else None
            )
            _append_version_changelog(
                item,
                new_label=item.get("version_label"),
                old_label=old_label,
            )
            _save_custom_store(project_root, store)
            return {
                "id": tid,
                "version_label": item["version_label"],
            }
    raise ValueError(f"unknown template: {template_id!r}")


def set_factory_template_version_label(
    template_id: str,
    *,
    version_label: str | None,
) -> dict[str, Any]:
    """Set version label on a factory shared template."""
    tid = template_id.strip().lower()
    if not tid.startswith(_FACTORY_PREFIX):
        raise ValueError("only factory templates support version labels here")
    factory = _load_factory_store()
    for item in factory.get("templates", []):
        if item.get("id") == tid:
            old_label = item.get("version_label")
            item["version_label"] = (
                _normalize_version_label(version_label, strict=True)
                if version_label and str(version_label).strip()
                else None
            )
            _append_version_changelog(
                item,
                new_label=item.get("version_label"),
                old_label=old_label,
            )
            _save_factory_store(factory)
            return {
                "id": tid,
                "version_label": item["version_label"],
            }
    raise ValueError(f"unknown factory template: {template_id!r}")


_EXPORT_SCHEMA_VERSION = "1"


def _normalize_import_entry(raw: dict[str, Any]) -> dict[str, Any]:
    name = str(raw.get("name", "")).strip()
    if not name:
        raise ValueError("import template name required")
    volumes = raw.get("volumes", [])
    if not isinstance(volumes, list) or not volumes:
        raise ValueError(f"import template {name!r} volumes required")
    max_chapter = int(raw.get("source_max_chapter") or raw.get("max_chapter") or 1)
    if max_chapter < 1:
        raise ValueError("source_max_chapter must be >= 1")
    return {
        "id": _normalize_template_id(name),
        "name": name,
        "description": str(raw.get("description", "导入模板")).strip(),
        "version_label": (
            _normalize_version_label(raw.get("version_label"), strict=True)
            if raw.get("version_label")
            else None
        ),
        "source_max_chapter": max_chapter,
        "volumes": [
            {
                "label": str(v["label"]),
                "start_chapter": int(v["start_chapter"]),
                "end_chapter": int(v["end_chapter"]),
                "core_conflict": str(v.get("core_conflict", "")),
                "locked": False,
            }
            for v in volumes
        ],
    }


def export_custom_volume_templates(project_root: Path | str) -> dict[str, Any]:
    """Export project custom templates as portable JSON."""
    store = _load_custom_store(project_root)
    return {
        "schema_version": _EXPORT_SCHEMA_VERSION,
        "templates": store.get("templates", []),
        "count": len(store.get("templates", [])),
    }


def import_custom_volume_templates(
    project_root: Path | str,
    payload: dict[str, Any],
    *,
    replace: bool = False,
) -> dict[str, Any]:
    """Import custom templates from export JSON."""
    raw_templates = payload.get("templates", [])
    if not isinstance(raw_templates, list):
        raise ValueError("templates must be a list")
    normalized = [_normalize_import_entry(row) for row in raw_templates]
    if replace:
        merged = normalized
    else:
        store = _load_custom_store(project_root)
        existing = store.get("templates", [])
        merged = normalized + existing
    store = {
        "schema_version": _CUSTOM_STATE_VERSION,
        "templates": merged[:_MAX_CUSTOM_TEMPLATES],
    }
    _save_custom_store(project_root, store)
    return {
        "imported": len(normalized),
        "total": len(store["templates"]),
        "replaced": replace,
    }


def list_template_sync_sources(*, exclude_slug: str | None = None) -> list[dict[str, Any]]:
    """List other factory projects that have custom volume templates."""
    from infra.studio_registry import list_projects

    rows: list[dict[str, Any]] = []
    for project in list_projects():
        if exclude_slug and project.slug == exclude_slug:
            continue
        exported = export_custom_volume_templates(project.root)
        count = int(exported.get("count") or 0)
        if count > 0:
            rows.append(
                {
                    "slug": project.slug,
                    "name": project.name,
                    "template_count": count,
                },
            )
    return rows


def sync_custom_volume_templates_from_projects(
    target_root: Path | str,
    *,
    source_slugs: list[str],
    exclude_slug: str | None = None,
) -> dict[str, Any]:
    """Import custom templates from other projects into the active project."""
    from infra.studio_registry import list_projects

    if not source_slugs:
        raise ValueError("source_slugs required")
    by_slug = {project.slug: project for project in list_projects()}
    collected: list[dict[str, Any]] = []
    resolved_sources: list[str] = []
    for slug in source_slugs:
        sid = str(slug).strip()
        if not sid or sid == exclude_slug:
            continue
        project = by_slug.get(sid)
        if project is None:
            raise ValueError(f"unknown project slug: {sid!r}")
        exported = export_custom_volume_templates(project.root)
        templates = exported.get("templates", [])
        if not templates:
            continue
        resolved_sources.append(sid)
        for tpl in templates:
            name = str(tpl.get("name", "模板"))
            if f"({sid})" not in name:
                name = f"{name} ({sid})"
            collected.append(
                {
                    **tpl,
                    "name": name,
                    "description": f"同步自 {sid} · {tpl.get('description', '')}".strip(),
                },
            )
    if not collected:
        store = _load_custom_store(target_root)
        return {
            "imported": 0,
            "total": len(store.get("templates", [])),
            "sources": resolved_sources,
        }
    result = import_custom_volume_templates(target_root, {"templates": collected}, replace=False)
    result["sources"] = resolved_sources
    return result


def publish_custom_to_factory_library(
    project_root: Path | str,
    template_id: str,
) -> dict[str, Any]:
    """Copy a project custom template into the factory-wide library."""
    tid = template_id.strip().lower()
    if not tid.startswith(_CUSTOM_PREFIX):
        raise ValueError("only project custom templates can be published to factory")
    store = _load_custom_store(project_root)
    match = next(
        (row for row in store.get("templates", []) if row.get("id") == tid),
        None,
    )
    if match is None:
        raise ValueError(f"unknown template: {template_id!r}")
    factory = _load_factory_store()
    templates: list[dict[str, Any]] = factory.get("templates", [])
    entry = {
        "id": _normalize_factory_template_id(str(match["name"])),
        "name": str(match["name"]),
        "description": str(match.get("description", "工厂共享模板")),
        "version_label": _normalize_version_label(match.get("version_label")),
        "source_max_chapter": int(match.get("source_max_chapter") or 1),
        "volumes": match.get("volumes", []),
        "published_from": str(tid),
    }
    templates.insert(0, entry)
    factory["templates"] = templates[:_MAX_FACTORY_TEMPLATES]
    factory["schema_version"] = _FACTORY_STATE_VERSION
    _save_factory_store(factory)
    return {
        "id": entry["id"],
        "name": entry["name"],
        "description": entry["description"],
        "version_label": entry.get("version_label"),
    }


def pull_factory_templates_to_project(
    project_root: Path | str,
    *,
    template_ids: list[str],
) -> dict[str, Any]:
    """Import selected factory templates into the active project."""
    if not template_ids:
        raise ValueError("template_ids required")
    factory = _load_factory_store()
    by_id = {row["id"]: row for row in factory.get("templates", [])}
    collected: list[dict[str, Any]] = []
    resolved: list[str] = []
    for raw_id in template_ids:
        tid = str(raw_id).strip().lower()
        if not tid.startswith(_FACTORY_PREFIX):
            raise ValueError(f"not a factory template: {raw_id!r}")
        match = by_id.get(tid)
        if match is None:
            raise ValueError(f"unknown factory template: {raw_id!r}")
        resolved.append(tid)
        collected.append(
            {
                **match,
                "id": _normalize_template_id(str(match["name"])),
                "name": str(match["name"]),
                "description": f"工厂库 · {match.get('description', '')}".strip(),
            },
        )
    result = import_custom_volume_templates(project_root, {"templates": collected}, replace=False)
    result["template_ids"] = resolved
    return result


def delete_factory_volume_template(template_id: str) -> dict[str, Any]:
    """Remove a template from the factory-wide library."""
    tid = template_id.strip().lower()
    if not tid.startswith(_FACTORY_PREFIX):
        raise ValueError("only factory templates can be deleted from factory library")
    factory = _load_factory_store()
    templates: list[dict[str, Any]] = factory.get("templates", [])
    kept = [row for row in templates if row.get("id") != tid]
    if len(kept) == len(templates):
        raise ValueError(f"unknown factory template: {template_id!r}")
    factory["templates"] = kept
    _save_factory_store(factory)
    return {"id": tid, "deleted": True}


def _resolve_factory_template(tid: str) -> dict[str, Any] | None:
    if not tid.startswith(_FACTORY_PREFIX):
        return None
    return next(
        (row for row in _load_factory_store().get("templates", []) if row.get("id") == tid),
        None,
    )


def _build_builtin_template(template_id: str, max_chapter: int) -> list[dict[str, Any]]:
    if template_id == "companion_short":
        return [
            {
                "label": "全书",
                "start_chapter": 1,
                "end_chapter": max_chapter,
                "core_conflict": "主线冲突（待填）",
                "locked": False,
            },
        ]

    if template_id == "three_act":
        act1_end = max(1, max_chapter // 4)
        act2_end = max(act1_end + 1, (max_chapter * 3) // 4)
        if act2_end >= max_chapter:
            act2_end = max_chapter - 1
        return [
            {
                "label": "第一幕",
                "start_chapter": 1,
                "end_chapter": act1_end,
                "core_conflict": "建置世界与诱因",
                "locked": False,
            },
            {
                "label": "第二幕",
                "start_chapter": act1_end + 1,
                "end_chapter": act2_end,
                "core_conflict": "对抗与升级",
                "locked": False,
            },
            {
                "label": "第三幕",
                "start_chapter": act2_end + 1,
                "end_chapter": max_chapter,
                "core_conflict": "高潮与结局",
                "locked": False,
            },
        ]

    volumes: list[dict[str, Any]] = []
    labels = ["卷一", "卷二", "卷三", "卷四", "卷五"]
    conflicts = ["开篇", "发展", "转折", "高潮", "收束"]
    for idx in range(5):
        start = _chunk_end(max_chapter, idx, 5) + 1 if idx > 0 else 1
        end = _chunk_end(max_chapter, idx + 1, 5)
        if start > end:
            continue
        volumes.append(
            {
                "label": labels[idx],
                "start_chapter": start,
                "end_chapter": end,
                "core_conflict": conflicts[idx],
                "locked": False,
            },
        )
    if not volumes:
        volumes.append(
            {
                "label": "卷一",
                "start_chapter": 1,
                "end_chapter": max_chapter,
                "core_conflict": "开篇",
                "locked": False,
            },
        )
    return volumes


def build_volume_template(
    template_id: str,
    max_chapter: int,
    project_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    if max_chapter < 1:
        raise ValueError("max_chapter must be >= 1")
    tid = template_id.strip().lower()
    if tid.startswith(_CUSTOM_PREFIX):
        if project_root is None:
            raise ValueError("custom template requires project root")
        store = _load_custom_store(project_root)
        match = next(
            (row for row in store.get("templates", []) if row.get("id") == tid),
            None,
        )
        if match is None:
            raise ValueError(f"unknown template: {template_id!r}")
        source_max = int(match.get("source_max_chapter") or max_chapter)
        return _scale_volumes(match.get("volumes", []), source_max, max_chapter)

    factory_match = _resolve_factory_template(tid)
    if factory_match is not None:
        source_max = int(factory_match.get("source_max_chapter") or max_chapter)
        return _scale_volumes(factory_match.get("volumes", []), source_max, max_chapter)

    if tid not in _BUILTIN_META:
        raise ValueError(f"unknown template: {template_id!r}")
    return _build_builtin_template(tid, max_chapter)


def template_meta(
    template_id: str,
    project_root: Path | str | None = None,
) -> dict[str, str]:
    tid = template_id.strip().lower()
    if tid.startswith(_CUSTOM_PREFIX):
        if project_root is None:
            raise ValueError("custom template requires project root")
        store = _load_custom_store(project_root)
        match = next(
            (row for row in store.get("templates", []) if row.get("id") == tid),
            None,
        )
        if match is None:
            raise ValueError(f"unknown template: {template_id!r}")
        return {
            "name": str(match["name"]),
            "description": str(match.get("description", "")),
        }
    factory_match = _resolve_factory_template(tid)
    if factory_match is not None:
        return {
            "name": str(factory_match["name"]),
            "description": str(factory_match.get("description", "")),
        }
    if tid not in _BUILTIN_META:
        raise ValueError(f"unknown template: {template_id!r}")
    return dict(_BUILTIN_META[tid])
