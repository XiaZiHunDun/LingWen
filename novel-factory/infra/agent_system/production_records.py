"""Phase 9.82 F74: read pilot / batch JSON records for Dashboard (read-only)."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal


RecordType = Literal["pilot", "batch"]


@dataclass(frozen=True)
class ProductionRecordItem:
    record_id: str
    record_type: RecordType
    chapter_num: int | None
    chapter_range: str | None
    operator: str | None
    recorded_at: str | None
    provider: str | None
    total_cost_usd: float | None
    emit_chapter_completed: bool | None
    memory_context_source: str | None
    stopped_reason: str | None
    source_file: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_pilot_records_dir() -> Path:
    """Default: novel-factory/infra/.state/pilot_records (override via env)."""
    env = os.environ.get("LINGWEN_PILOT_RECORDS_DIR", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parents[1] / ".state" / "pilot_records"


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_pilot(data: dict[str, Any], source_file: str) -> ProductionRecordItem:
    run = data.get("run") if isinstance(data.get("run"), dict) else {}
    env = data.get("env") if isinstance(data.get("env"), dict) else {}
    hooks = data.get("hooks") if isinstance(data.get("hooks"), dict) else {}
    chapter = data.get("chapter_num")
    return ProductionRecordItem(
        record_id=str(data.get("pilot_id") or Path(source_file).stem),
        record_type="pilot",
        chapter_num=int(chapter) if chapter is not None else None,
        chapter_range=None,
        operator=data.get("operator") if isinstance(data.get("operator"), str) else None,
        recorded_at=data.get("recorded_at") if isinstance(data.get("recorded_at"), str) else None,
        provider=env.get("primary_provider") if isinstance(env.get("primary_provider"), str) else None,
        total_cost_usd=_safe_float(run.get("total_cost_usd")),
        emit_chapter_completed=run.get("emit_chapter_completed")
        if isinstance(run.get("emit_chapter_completed"), bool)
        else None,
        memory_context_source=hooks.get("memory_context_source")
        if isinstance(hooks.get("memory_context_source"), str)
        else None,
        stopped_reason=None,
        source_file=source_file,
    )


def _parse_batch(data: dict[str, Any], source_file: str) -> ProductionRecordItem:
    start = data.get("start_chapter")
    attempted = data.get("chapters_attempted")
    chapter_range = None
    if isinstance(start, int) and isinstance(attempted, int) and attempted > 0:
        end = start + attempted - 1
        chapter_range = f"{start}-{end}" if end >= start else str(start)
    return ProductionRecordItem(
        record_id=str(data.get("batch_id") or Path(source_file).stem),
        record_type="batch",
        chapter_num=int(start) if isinstance(start, int) else None,
        chapter_range=chapter_range,
        operator=None,
        recorded_at=data.get("recorded_at") if isinstance(data.get("recorded_at"), str) else None,
        provider=None,
        total_cost_usd=_safe_float(data.get("total_cost_usd")),
        emit_chapter_completed=(
            data.get("chapters_succeeded") == data.get("chapters_attempted")
            if data.get("chapters_attempted")
            else None
        ),
        memory_context_source=None,
        stopped_reason=data.get("stopped_reason")
        if isinstance(data.get("stopped_reason"), str)
        else None,
        source_file=source_file,
    )


def _load_json_file(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def parse_record_file(path: Path) -> ProductionRecordItem | None:
    """Parse one pilot or batch JSON file."""
    data = _load_json_file(path)
    if not data or not isinstance(data, dict):
        return None
    name = path.name.lower()
    if name.startswith("batch") or "chapters_attempted" in data:
        return _parse_batch(data, path.name)
    if "chapter_num" in data or "pilot_id" in data:
        return _parse_pilot(data, path.name)
    return None


def list_production_records(
    records_dir: Path | None = None,
    *,
    chapter_num: int | None = None,
    limit: int = 50,
) -> list[ProductionRecordItem]:
    """List records newest-first; optional filter by chapter_num."""
    root = Path(records_dir or default_pilot_records_dir())
    if not root.is_dir():
        return []

    items: list[ProductionRecordItem] = []
    for path in sorted(root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        item = parse_record_file(path)
        if item is None:
            continue
        if chapter_num is not None:
            if item.record_type == "pilot" and item.chapter_num != chapter_num:
                continue
            if item.record_type == "batch" and item.chapter_range:
                parts = item.chapter_range.split("-")
                try:
                    lo, hi = int(parts[0]), int(parts[-1])
                    if not (lo <= chapter_num <= hi):
                        continue
                except (ValueError, IndexError):
                    if item.chapter_num != chapter_num:
                        continue
            elif item.chapter_num != chapter_num:
                continue
        items.append(item)
        if len(items) >= limit:
            break
    return items


def latest_record_by_chapter(
    records: list[ProductionRecordItem],
) -> dict[int, ProductionRecordItem]:
    """Map chapter_num → latest pilot record (batch ranges expand to each chapter)."""
    by_chapter: dict[int, ProductionRecordItem] = {}
    for rec in records:
        if rec.record_type == "pilot" and rec.chapter_num is not None:
            by_chapter.setdefault(rec.chapter_num, rec)
        elif rec.record_type == "batch" and rec.chapter_range:
            parts = rec.chapter_range.split("-")
            try:
                lo, hi = int(parts[0]), int(parts[-1])
                for ch in range(lo, hi + 1):
                    by_chapter.setdefault(ch, rec)
            except (ValueError, IndexError):
                if rec.chapter_num is not None:
                    by_chapter.setdefault(rec.chapter_num, rec)
    return by_chapter
