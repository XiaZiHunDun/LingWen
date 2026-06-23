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
_CUSTOM_STATE_VERSION = "1"
_MAX_CUSTOM_TEMPLATES = 5
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _custom_templates_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "custom_volume_templates.json"


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


def _normalize_template_id(name: str) -> str:
    slug = _SLUG_RE.sub("-", name.strip().lower()).strip("-")
    return f"{_CUSTOM_PREFIX}{slug[:20]}-{uuid.uuid4().hex[:6]}"


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
        {"id": template_id, **meta, "builtin": True}
        for template_id, meta in _BUILTIN_META.items()
    ]
    if project_root is None:
        return rows
    store = _load_custom_store(project_root)
    for item in store.get("templates", []):
        rows.append(
            {
                "id": item["id"],
                "name": item["name"],
                "description": item.get("description", "项目自定义模板"),
                "builtin": False,
            },
        )
    return rows


def save_custom_volume_template(
    project_root: Path | str,
    *,
    name: str,
    volumes: list[dict[str, Any]],
    max_chapter: int,
    description: str | None = None,
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
    templates.insert(0, entry)
    store["templates"] = templates[:_MAX_CUSTOM_TEMPLATES]
    store["schema_version"] = _CUSTOM_STATE_VERSION
    _save_custom_store(project_root, store)
    return entry


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
    if tid not in _BUILTIN_META:
        raise ValueError(f"unknown template: {template_id!r}")
    return dict(_BUILTIN_META[tid])
