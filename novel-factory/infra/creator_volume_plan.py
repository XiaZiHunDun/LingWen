"""Volume plan parse, lock state, and deviation diff for advance mode."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infra.creator_revision import CreatorDocConflictError, content_revision
from infra.paths import ProjectPaths
from infra.project_config import ProjectConfig

_VOLUME_TABLE_HEADER = re.compile(r"^\|\s*卷\s*\|", re.MULTILINE)
_VOLUME_ROW = re.compile(
    r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$",
    re.MULTILINE,
)
_RANGE = re.compile(
    r"(?P<a>\d{1,3})\s*[–\-—~～至到]\s*(?P<b>\d{1,3})",
)
_STATE_VERSION = "1"
_SECTION_TITLE = "## 卷纲占位（推进模式请在此锁定）"


@dataclass(frozen=True)
class VolumeEntry:
    label: str
    start_chapter: int
    end_chapter: int
    core_conflict: str
    locked: bool
    locked_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "start_chapter": self.start_chapter,
            "end_chapter": self.end_chapter,
            "core_conflict": self.core_conflict,
            "locked": self.locked,
            "locked_at": self.locked_at,
        }


def _root(project_root: Path | str) -> Path:
    return project_root if isinstance(project_root, Path) else Path(project_root)


def global_outline_path(project_root: Path | str) -> Path:
    root = _root(project_root)
    return root / "03_内容仓库" / "01_全文总体大纲" / "全局大纲.md"


def volume_plan_state_path(project_root: Path | str) -> Path:
    return _root(project_root) / ".state" / "volume_plan.json"


def parse_chapter_range(text: str) -> tuple[int, int] | None:
    match = _RANGE.search(text.replace(" ", ""))
    if not match:
        single = re.search(r"\d{1,3}", text)
        if not single:
            return None
        num = int(single.group())
        return num, num
    start = int(match.group("a"))
    end = int(match.group("b"))
    if start > end:
        start, end = end, start
    return start, end


def parse_volume_table_from_markdown(text: str) -> list[VolumeEntry]:
    if _SECTION_TITLE not in text:
        return []
    section = text.split(_SECTION_TITLE, 1)[1]
    # Stop at next ## heading
    if "\n## " in section:
        section = section.split("\n## ", 1)[0]

    volumes: list[VolumeEntry] = []
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        if _VOLUME_TABLE_HEADER.match(line) or re.match(r"^\|\s*[-:]+", line):
            continue
        match = _VOLUME_ROW.match(line.strip())
        if not match:
            continue
        label, range_text, conflict, status = (g.strip() for g in match.groups())
        parsed = parse_chapter_range(range_text)
        if not parsed:
            continue
        start, end = parsed
        locked = status in {"锁定", "已锁定", "locked"}
        volumes.append(
            VolumeEntry(
                label=label,
                start_chapter=start,
                end_chapter=end,
                core_conflict=conflict,
                locked=locked,
            ),
        )
    return volumes


def _load_state(path: Path) -> list[VolumeEntry]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    volumes: list[VolumeEntry] = []
    for raw in data.get("volumes", []):
        volumes.append(
            VolumeEntry(
                label=str(raw.get("label", "")),
                start_chapter=int(raw["start_chapter"]),
                end_chapter=int(raw["end_chapter"]),
                core_conflict=str(raw.get("core_conflict", "")),
                locked=bool(raw.get("locked")),
                locked_at=raw.get("locked_at"),
            ),
        )
    return volumes


def _save_state(path: Path, volumes: list[VolumeEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": _STATE_VERSION,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "volumes": [v.to_dict() for v in volumes],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _format_range(start: int, end: int) -> str:
    if start == end:
        return f"{start:03d}"
    return f"{start:03d}–{end:03d}"


def _status_label(vol: VolumeEntry) -> str:
    return "锁定" if vol.locked else "草稿"


def render_volume_table_markdown(volumes: list[VolumeEntry]) -> str:
    lines = [
        _SECTION_TITLE,
        "",
        "| 卷 | 章范围 | 核心冲突 | 状态 |",
        "|----|--------|----------|------|",
    ]
    for vol in volumes:
        lines.append(
            f"| {vol.label} | {_format_range(vol.start_chapter, vol.end_chapter)} "
            f"| {vol.core_conflict} | {_status_label(vol)} |",
        )
    return "\n".join(lines)


def sync_volume_table_in_outline(outline_path: Path, volumes: list[VolumeEntry]) -> None:
    if not outline_path.is_file():
        outline_path.parent.mkdir(parents=True, exist_ok=True)
        outline_path.write_text(render_volume_table_markdown(volumes) + "\n", encoding="utf-8")
        return

    text = outline_path.read_text(encoding="utf-8")
    table_block = render_volume_table_markdown(volumes)
    if _SECTION_TITLE in text:
        before, rest = text.split(_SECTION_TITLE, 1)
        after = ""
        if "\n## " in rest:
            _, after = rest.split("\n## ", 1)
            after = "\n## " + after
        text = before.rstrip() + "\n\n" + table_block + after
    else:
        text = text.rstrip() + "\n\n" + table_block + "\n"
    outline_path.write_text(text.rstrip() + "\n", encoding="utf-8")


def load_volume_plan(project_root: Path | str) -> list[VolumeEntry]:
    root = _root(project_root)
    state_path = volume_plan_state_path(root)
    if state_path.is_file():
        return _load_state(state_path)

    outline_path = global_outline_path(project_root)
    if outline_path.is_file():
        return parse_volume_table_from_markdown(
            outline_path.read_text(encoding="utf-8"),
        )
    return []


def volume_plan_revision(project_root: Path | str) -> str:
    root = _root(project_root)
    state_path = volume_plan_state_path(root)
    if state_path.is_file():
        return content_revision(state_path.read_text(encoding="utf-8"))
    outline_path = global_outline_path(root)
    if outline_path.is_file():
        return content_revision(outline_path.read_text(encoding="utf-8"))
    return content_revision("")


def _entries_from_raw(volumes: list[dict[str, Any]] | list[VolumeEntry]) -> list[VolumeEntry]:
    normalized: list[VolumeEntry] = []
    for raw in volumes:
        if isinstance(raw, VolumeEntry):
            normalized.append(raw)
            continue
        normalized.append(
            VolumeEntry(
                label=str(raw.get("label", "")),
                start_chapter=int(raw["start_chapter"]),
                end_chapter=int(raw["end_chapter"]),
                core_conflict=str(raw.get("core_conflict", "")).strip(),
                locked=bool(raw.get("locked")),
                locked_at=raw.get("locked_at"),
            ),
        )
    return normalized


def merge_volume_range(
    volumes: list[dict[str, Any]] | list[VolumeEntry],
    start_idx: int,
    end_idx: int,
    *,
    label: str | None = None,
    core_conflict: str | None = None,
) -> tuple[list[VolumeEntry], VolumeEntry]:
    """Merge a contiguous slice of volumes into one entry."""
    entries = _entries_from_raw(volumes)
    if start_idx < 0 or end_idx >= len(entries) or start_idx > end_idx:
        raise ValueError("invalid merge range")
    chunk = entries[start_idx : end_idx + 1]
    merged_label = (label or "·".join(v.label for v in chunk)).strip()
    if not merged_label:
        raise ValueError("merged label required")
    start = min(v.start_chapter for v in chunk)
    end = max(v.end_chapter for v in chunk)
    conflicts = [v.core_conflict.strip() for v in chunk if v.core_conflict.strip()]
    merged_conflict = (core_conflict or " / ".join(conflicts)).strip()
    locked = any(v.locked for v in chunk)
    locked_at = next((v.locked_at for v in chunk if v.locked and v.locked_at), None)
    merged = VolumeEntry(
        label=merged_label,
        start_chapter=start,
        end_chapter=end,
        core_conflict=merged_conflict,
        locked=locked,
        locked_at=locked_at if locked else None,
    )
    return entries[:start_idx] + [merged] + entries[end_idx + 1 :], merged


def split_volume(
    volumes: list[dict[str, Any]] | list[VolumeEntry],
    volume_index: int,
    split_at_chapter: int,
    *,
    first_label: str | None = None,
    second_label: str | None = None,
    first_conflict: str | None = None,
    second_conflict: str | None = None,
) -> tuple[list[VolumeEntry], VolumeEntry, VolumeEntry]:
    """Split one volume at split_at_chapter (first chapter of the lower segment)."""
    entries = _entries_from_raw(volumes)
    if volume_index < 0 or volume_index >= len(entries):
        raise ValueError("invalid volume index")
    vol = entries[volume_index]
    if split_at_chapter <= vol.start_chapter or split_at_chapter > vol.end_chapter:
        raise ValueError("split chapter must be inside volume (exclusive of start)")
    first_end = split_at_chapter - 1
    if first_end < vol.start_chapter:
        raise ValueError("split would create empty first volume")

    first = VolumeEntry(
        label=(first_label or f"{vol.label}上").strip(),
        start_chapter=vol.start_chapter,
        end_chapter=first_end,
        core_conflict=(first_conflict or vol.core_conflict).strip(),
        locked=vol.locked,
        locked_at=vol.locked_at if vol.locked else None,
    )
    second = VolumeEntry(
        label=(second_label or f"{vol.label}下").strip(),
        start_chapter=split_at_chapter,
        end_chapter=vol.end_chapter,
        core_conflict=(second_conflict or vol.core_conflict).strip(),
        locked=vol.locked,
        locked_at=vol.locked_at if vol.locked else None,
    )
    if not first.label or not second.label:
        raise ValueError("split volume labels required")
    return entries[:volume_index] + [first, second] + entries[volume_index + 1 :], first, second


def save_volume_plan(
    project_root: Path | str,
    volumes: list[dict[str, Any]],
    *,
    sync_markdown: bool = True,
    expected_revision: str | None = None,
) -> list[VolumeEntry]:
    root = _root(project_root)
    if expected_revision is not None:
        current = volume_plan_revision(root)
        if current != expected_revision:
            raise CreatorDocConflictError(
                "卷纲已在别处修改，请重新加载后再保存",
                fields=["volume_plan"],
            )
    existing = {v.label: v for v in load_volume_plan(root)}
    normalized: list[VolumeEntry] = []
    now = datetime.now(timezone.utc).isoformat()

    for raw in volumes:
        label = str(raw.get("label", "")).strip()
        if not label:
            continue
        start = int(raw["start_chapter"])
        end = int(raw["end_chapter"])
        if start > end:
            start, end = end, start
        locked = bool(raw.get("locked"))
        prev = existing.get(label)
        locked_at = prev.locked_at if prev and prev.locked and locked else None
        if locked and not locked_at:
            locked_at = now
        if not locked:
            locked_at = None
        normalized.append(
            VolumeEntry(
                label=label,
                start_chapter=start,
                end_chapter=end,
                core_conflict=str(raw.get("core_conflict", "")).strip(),
                locked=locked,
                locked_at=locked_at,
            ),
        )

    state_path = volume_plan_state_path(root)
    _save_state(state_path, normalized)
    if sync_markdown:
        sync_volume_table_in_outline(global_outline_path(root), normalized)
    return normalized


_PLACEHOLDER_CONFLICTS = frozenset({"（待填）", "待填", "...", "—", "-", "（", "）"})


def _conflict_terms(conflict: str) -> list[str]:
    text = conflict.strip()
    if not text or text in _PLACEHOLDER_CONFLICTS:
        return []
    parts = re.split(r"[，,、；;。．/\s]+", text)
    return [part for part in parts if len(part) >= 2]


def _outline_matches_conflict(outline_text: str, terms: list[str]) -> bool:
    if not terms:
        return True
    for term in terms:
        if term in outline_text:
            return True
    return False


def _chapter_in_locked_range(chapter: int, volumes: list[VolumeEntry]) -> bool:
    for vol in volumes:
        if vol.locked and vol.start_chapter <= chapter <= vol.end_chapter:
            return True
    return False


def detect_volume_overlaps(volumes: list[VolumeEntry]) -> list[dict[str, Any]]:
    overlaps: list[dict[str, Any]] = []
    for i, left in enumerate(volumes):
        for right in volumes[i + 1 :]:
            start = max(left.start_chapter, right.start_chapter)
            end = min(left.end_chapter, right.end_chapter)
            if start > end:
                continue
            overlaps.append(
                {
                    "type": "volume_overlap",
                    "severity": "alert",
                    "chapter": start,
                    "volume_label": f"{left.label}/{right.label}",
                    "message": (
                        f"卷「{left.label}」与「{right.label}」"
                        f"在 ch{start:03d}–ch{end:03d} 章范围重叠"
                    ),
                },
            )
    return overlaps


def compute_volume_deviations(
    project_root: Path | str,
    volumes: list[VolumeEntry],
    *,
    paths: ProjectPaths | None = None,
) -> list[dict[str, Any]]:
    root = _root(project_root)
    resolved_paths = paths or ProjectPaths.get(root)
    config = ProjectConfig.load(resolved_paths)
    locked = [v for v in volumes if v.locked]
    deviations: list[dict[str, Any]] = list(detect_volume_overlaps(volumes))
    if not locked:
        return deviations
    written: list[int] = []
    for num in range(1, config.max_chapter + 1):
        if resolved_paths.read_chapter(num):
            written.append(num)

    for vol in locked:
        for num in range(vol.start_chapter, vol.end_chapter + 1):
            outline = config.chapter_outline_path(num, resolved_paths)
            body = resolved_paths.read_chapter(num)
            if not outline.is_file():
                deviations.append(
                    {
                        "type": "missing_outline",
                        "severity": "warn",
                        "chapter": num,
                        "volume_label": vol.label,
                        "message": f"卷「{vol.label}」ch{num:03d} 缺分章大纲",
                    },
                )
            if not body:
                deviations.append(
                    {
                        "type": "missing_body",
                        "severity": "warn",
                        "chapter": num,
                        "volume_label": vol.label,
                        "message": f"卷「{vol.label}」ch{num:03d} 尚无正文",
                    },
                )

        terms = _conflict_terms(vol.core_conflict)
        if terms:
            for num in range(vol.start_chapter, vol.end_chapter + 1):
                outline = config.chapter_outline_path(num, resolved_paths)
                if not outline.is_file():
                    continue
                outline_text = outline.read_text(encoding="utf-8")
                if not _outline_matches_conflict(outline_text, terms):
                    deviations.append(
                        {
                            "type": "semantic_drift",
                            "severity": "warn",
                            "chapter": num,
                            "volume_label": vol.label,
                            "message": (
                                f"卷「{vol.label}」ch{num:03d} 分章大纲与核心冲突"
                                f"「{vol.core_conflict}」关键词不匹配"
                            ),
                        },
                    )

    for num in written:
        if not _chapter_in_locked_range(num, volumes):
            deviations.append(
                {
                    "type": "outside_locked_plan",
                    "severity": "alert",
                    "chapter": num,
                    "volume_label": None,
                    "message": f"ch{num:03d} 已写但不在任何已锁定卷范围内",
                },
            )

    return deviations


def preview_volume_plan_diff(
    baseline: list[dict[str, Any]],
    draft: list[dict[str, Any]],
) -> dict[str, Any]:
    baseline_by_label = {str(row.get("label", "")).strip(): row for row in baseline if row.get("label")}
    draft_by_label = {str(row.get("label", "")).strip(): row for row in draft if row.get("label")}
    changes: list[dict[str, str]] = []

    for label, row in draft_by_label.items():
        if label not in baseline_by_label:
            changes.append({"type": "added", "label": label, "message": f"新增卷「{label}」"})
            continue
        prev = baseline_by_label[label]
        parts: list[str] = []
        if int(prev.get("start_chapter", 0)) != int(row.get("start_chapter", 0)) or int(
            prev.get("end_chapter", 0),
        ) != int(row.get("end_chapter", 0)):
            parts.append(
                f"章范围 ch{int(prev.get('start_chapter', 0)):03d}–ch{int(prev.get('end_chapter', 0)):03d}"
                f" → ch{int(row.get('start_chapter', 0)):03d}–ch{int(row.get('end_chapter', 0)):03d}",
            )
        if str(prev.get("core_conflict", "")).strip() != str(row.get("core_conflict", "")).strip():
            parts.append("核心冲突已修改")
        if bool(prev.get("locked")) != bool(row.get("locked")):
            parts.append("锁定" if row.get("locked") else "解锁")
        if parts:
            changes.append({"type": "changed", "label": label, "message": " · ".join(parts)})

    for label in baseline_by_label:
        if label not in draft_by_label:
            changes.append({"type": "removed", "label": label, "message": f"移除卷「{label}」"})

    return {"has_changes": bool(changes), "changes": changes}


def volume_plan_payload(project_root: Path | str) -> dict[str, Any]:
    root = _root(project_root)
    paths = ProjectPaths.get(root)
    config = ProjectConfig.load(paths)
    volumes = load_volume_plan(root)
    deviations = compute_volume_deviations(root, volumes, paths=paths)
    locked_count = sum(1 for v in volumes if v.locked)
    return {
        "slug": config.slug,
        "global_outline_path": str(global_outline_path(root)),
        "state_path": str(volume_plan_state_path(root)),
        "revision": volume_plan_revision(root),
        "volumes": [v.to_dict() for v in volumes],
        "locked_volume_count": locked_count,
        "deviations": deviations,
        "deviation_count": len(deviations),
        "alert_count": sum(1 for d in deviations if d["severity"] == "alert"),
    }
