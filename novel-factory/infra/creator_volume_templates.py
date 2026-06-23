"""Preset volume plan templates for creator advance mode."""
from __future__ import annotations

from typing import Any

_TEMPLATE_META: dict[str, dict[str, str]] = {
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


def _chunk_end(max_chapter: int, part_index: int, part_count: int) -> int:
    if part_index >= part_count:
        return max_chapter
    return min(max_chapter, (max_chapter * part_index) // part_count)


def list_volume_templates() -> list[dict[str, str]]:
    return [
        {"id": template_id, **meta}
        for template_id, meta in _TEMPLATE_META.items()
    ]


def build_volume_template(template_id: str, max_chapter: int) -> list[dict[str, Any]]:
    if max_chapter < 1:
        raise ValueError("max_chapter must be >= 1")
    template_id = template_id.strip().lower()
    if template_id not in _TEMPLATE_META:
        raise ValueError(f"unknown template: {template_id!r}")

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

    # five_volume
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
