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
    """Default pilot records dir: project .state, env override, or infra/.state."""
    env = os.environ.get("LINGWEN_PILOT_RECORDS_DIR", "").strip()
    if env:
        return Path(env).expanduser().resolve()

    project_root = os.environ.get("LINGWEN_PROJECT_ROOT", "").strip()
    if project_root:
        candidate = Path(project_root) / ".state" / "pilot_records"
        if candidate.is_dir():
            return candidate.resolve()

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


def chapters_covered_by_record(rec: ProductionRecordItem) -> set[int]:
    """Chapter numbers referenced by one pilot or batch record."""
    covered: set[int] = set()
    if rec.record_type == "pilot" and rec.chapter_num is not None:
        covered.add(rec.chapter_num)
    elif rec.record_type == "batch" and rec.chapter_range:
        parts = rec.chapter_range.split("-")
        try:
            lo, hi = int(parts[0]), int(parts[-1])
            covered.update(range(lo, hi + 1))
        except (ValueError, IndexError):
            if rec.chapter_num is not None:
                covered.add(rec.chapter_num)
    return covered


def chapters_covered_by_batches(records: list[ProductionRecordItem]) -> set[int]:
    """Union of chapters included in any batch record."""
    covered: set[int] = set()
    for rec in records:
        if rec.record_type == "batch":
            covered |= chapters_covered_by_record(rec)
    return covered


def compute_deduplicated_cost_usd(records: list[ProductionRecordItem]) -> float:
    """Sum batch totals + pilot-only chapters (skip pilots inside batch ranges)."""
    in_batch = chapters_covered_by_batches(records)
    total = 0.0
    for rec in records:
        if rec.total_cost_usd is None:
            continue
        if rec.record_type == "batch":
            total += float(rec.total_cost_usd)
        elif rec.record_type == "pilot":
            ch = rec.chapter_num
            if ch is not None and ch not in in_batch:
                total += float(rec.total_cost_usd)
    return total


@dataclass(frozen=True)
class ProductionBatchRollupItem:
    record_id: str
    chapter_range: str | None
    total_cost_usd: float | None
    stopped_reason: str | None
    recorded_at: str | None
    source_file: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def rollup_production_records(
    records_dir: Path | None = None,
    *,
    limit: int = 100,
) -> dict[str, Any]:
    """Aggregate pilot/batch records for Analytics (F81)."""
    root = Path(records_dir or default_pilot_records_dir())
    records = list_production_records(root, limit=limit)
    pilot_count = sum(1 for r in records if r.record_type == "pilot")
    batch_count = sum(1 for r in records if r.record_type == "batch")
    chapters: set[int] = set()
    for rec in records:
        chapters |= chapters_covered_by_record(rec)

    latest_at: str | None = None
    for rec in records:
        if rec.recorded_at and (latest_at is None or rec.recorded_at > latest_at):
            latest_at = rec.recorded_at

    batches: list[dict[str, Any]] = []
    for rec in records:
        if rec.record_type != "batch":
            continue
        batches.append(ProductionBatchRollupItem(
            record_id=rec.record_id,
            chapter_range=rec.chapter_range,
            total_cost_usd=rec.total_cost_usd,
            stopped_reason=rec.stopped_reason,
            recorded_at=rec.recorded_at,
            source_file=rec.source_file,
        ).to_dict())

    return {
        "records_dir": str(root),
        "record_count": len(records),
        "pilot_count": pilot_count,
        "batch_count": batch_count,
        "total_cost_usd": round(compute_deduplicated_cost_usd(records), 6),
        "chapters_with_records": len(chapters),
        "latest_recorded_at": latest_at,
        "batches": batches,
    }


def _record_label(rec: ProductionRecordItem) -> str:
    if rec.record_type == "batch" and rec.chapter_range:
        return f"ch{rec.chapter_range}"
    if rec.chapter_num is not None:
        return f"ch{rec.chapter_num}"
    return rec.record_id


def production_cost_trend(
    records_dir: Path | None = None,
    *,
    limit: int = 100,
) -> dict[str, Any]:
    """Time-ordered production cost series for Analytics chart (F87)."""
    root = Path(records_dir or default_pilot_records_dir())
    records = list_production_records(root, limit=limit)
    ordered = sorted(
        records,
        key=lambda rec: (rec.recorded_at or "", rec.source_file),
    )

    batch_covered: set[int] = set()
    cumulative = 0.0
    points: list[dict[str, Any]] = []

    for rec in ordered:
        incremental = 0.0
        if rec.total_cost_usd is not None:
            if rec.record_type == "batch":
                incremental = float(rec.total_cost_usd)
                batch_covered |= chapters_covered_by_record(rec)
            elif rec.record_type == "pilot":
                ch = rec.chapter_num
                if ch is None or ch not in batch_covered:
                    incremental = float(rec.total_cost_usd)

        cumulative += incremental
        points.append({
            "recorded_at": rec.recorded_at,
            "record_id": rec.record_id,
            "record_type": rec.record_type,
            "label": _record_label(rec),
            "cost_usd": rec.total_cost_usd,
            "incremental_cost_usd": round(incremental, 6),
            "cumulative_cost_usd": round(cumulative, 6),
        })

    return {
        "records_dir": str(root),
        "point_count": len(points),
        "total_cost_usd": round(cumulative, 6),
        "points": points,
    }
