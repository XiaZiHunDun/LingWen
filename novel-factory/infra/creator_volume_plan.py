"""Volume plan parse, lock state, and deviation diff for advance mode."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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


def save_volume_plan(
    project_root: Path | str,
    volumes: list[dict[str, Any]],
    *,
    sync_markdown: bool = True,
) -> list[VolumeEntry]:
    root = _root(project_root)
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


def _chapter_in_locked_range(chapter: int, volumes: list[VolumeEntry]) -> bool:
    for vol in volumes:
        if vol.locked and vol.start_chapter <= chapter <= vol.end_chapter:
            return True
    return False


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
    if not locked:
        return []

    deviations: list[dict[str, Any]] = []
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
        "volumes": [v.to_dict() for v in volumes],
        "locked_volume_count": locked_count,
        "deviations": deviations,
        "deviation_count": len(deviations),
        "alert_count": sum(1 for d in deviations if d["severity"] == "alert"),
    }
