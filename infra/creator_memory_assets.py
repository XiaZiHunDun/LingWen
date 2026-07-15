"""Creator memory & asset listing for dashboard."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from infra.creator_dashboard import creator_overview
from infra.creator_settings_docs import creator_settings_docs_payload
from infra.studio_registry import StudioProject

_EXCERPT_LEN = 160


def _excerpt(text: str, *, limit: int = _EXCERPT_LEN) -> str:
    compact = re.sub(r"\s+", " ", text.strip())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def _chapter_range(start: int, end: int) -> list[int]:
    return list(range(start, end + 1))


def _memory_gateway_items() -> tuple[list[dict[str, Any]], bool]:
    """Return items from memory gateway and whether gateway is live."""
    items: list[dict[str, Any]] = []
    try:
        from infra.memory_service import get_memory_gateway

        gateway = get_memory_gateway()
        if getattr(gateway, "is_noop", False):
            return items, False

        characters = gateway.get_all_characters() if hasattr(gateway, "get_all_characters") else {}
        for name, state in (characters or {}).items():
            loc = state.get("current_location") or ""
            alive = state.get("alive")
            status = "存活" if alive is not False else "已故"
            excerpt_parts = [p for p in [loc, status] if p]
            ch = state.get("last_updated_chapter") or state.get("first_appearance_chapter")
            items.append(
                {
                    "id": f"memory-char-{name}",
                    "kind": "character",
                    "name": name,
                    "excerpt": _excerpt(" · ".join(excerpt_parts) or "角色状态已记录"),
                    "chapters": [int(ch)] if ch else [],
                    "editable": False,
                    "placeholder": False,
                    "source": "memory",
                },
            )

        pending = gateway.get_pending_foreshadows() if hasattr(gateway, "get_pending_foreshadows") else {}
        for fp_id, meta in (pending or {}).items():
            title = str(meta.get("title") or fp_id)
            planted = meta.get("planted_chapter")
            items.append(
                {
                    "id": f"memory-fp-{fp_id}",
                    "kind": "foreshadow",
                    "name": f"伏笔：{title}",
                    "excerpt": _excerpt(str(meta.get("description") or meta.get("summary") or "待回收伏笔")),
                    "chapters": [int(planted)] if planted else [],
                    "editable": False,
                    "placeholder": False,
                    "source": "memory",
                },
            )
        return items, True
    except Exception:
        return items, False


def creator_memory_assets_payload(project: StudioProject) -> dict[str, Any]:
    overview = creator_overview(project)
    settings = creator_settings_docs_payload(project)
    items: list[dict[str, Any]] = []

    pillars = (settings.get("pillars_text") or "").strip()
    if pillars:
        items.append(
            {
                "id": "asset-pillars",
                "kind": "setting",
                "name": "创作支柱",
                "excerpt": _excerpt(pillars),
                "chapters": [],
                "editable": True,
                "placeholder": False,
                "source": "settings",
            },
        )

    outline = (settings.get("global_outline_text") or "").strip()
    if outline:
        items.append(
            {
                "id": "asset-outline",
                "kind": "setting",
                "name": "全局大纲",
                "excerpt": _excerpt(outline),
                "chapters": [],
                "editable": True,
                "placeholder": False,
                "source": "settings",
            },
        )

    for vol in overview.get("volume_summaries") or []:
        label = vol.get("volume_label")
        name = f"第{label}卷摘要" if label else vol.get("name", "卷摘要")
        start = vol.get("start_chapter")
        end = vol.get("end_chapter")
        chapters = _chapter_range(int(start), int(end)) if start and end else []
        items.append(
            {
                "id": f"asset-vol-{vol.get('name', 'summary')}",
                "kind": "summary",
                "name": name,
                "excerpt": _excerpt(vol.get("excerpt") or ""),
                "chapters": chapters,
                "editable": False,
                "placeholder": False,
                "source": "summary",
            },
        )

    for row in overview.get("chapters") or []:
        if not row.get("has_body") or not row.get("excerpt"):
            continue
        ch = int(row["chapter"])
        items.append(
            {
                "id": f"memory-ch-{ch}",
                "kind": "memory",
                "name": f"第{ch}章记忆片段",
                "excerpt": _excerpt(str(row.get("excerpt") or "")),
                "chapters": [ch],
                "editable": False,
                "placeholder": False,
                "source": "chapter",
            },
        )
        if sum(1 for i in items if i["kind"] == "memory") >= 12:
            break

    memory_items, memory_live = _memory_gateway_items()
    existing_ids = {i["id"] for i in items}
    for entry in memory_items:
        if entry["id"] not in existing_ids:
            items.append(entry)

    if not any(i["kind"] == "character" for i in items):
        items.append(
            {
                "id": "asset-char-placeholder",
                "kind": "character",
                "name": "主要角色",
                "excerpt": "记忆系统未连接时将显示占位；连接后自动同步角色卡。",
                "chapters": [],
                "editable": False,
                "placeholder": True,
                "source": "placeholder",
            },
        )

    from infra.creator_memory_annotations import apply_memory_annotations, load_memory_annotations
    from infra.creator_preferences import load_creator_preferences

    prefs = load_creator_preferences(project.root)
    annotations = load_memory_annotations(project.root)
    items = apply_memory_annotations(items, annotations)

    return {
        "slug": project.slug,
        "memory_available": memory_live,
        "memory_rag_enabled": prefs.get("memory_rag_enabled", True),
        "items": items,
    }
