"""Phase 9.81 F73: sequential batch chapter production (3–10 chapters).

Gate: LINGWEN_REAL_LLM=1 (same as pilot).
Stop-on-fail + optional cumulative --budget-usd hard stop.

CLI:
  python -m infra.agent_system.chapter_production_batch --preflight-only
  python -m infra.agent_system.chapter_production_batch \\
    --start-chapter 361 --max-chapters 3 --budget-usd 0.15 \\
    --save-summary infra/.state/pilot_records/batch-361-363.json
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from infra.agent_system.chapter_production_pilot import (
    PilotResult,
    _json_safe,
    preflight_checklist,
    preflight_ok,
    run_production_pilot,
    save_pilot_record,
)

BATCH_BEHAVIOR: tuple[dict[str, str], ...] = (
    {
        "trigger": "sequential",
        "behavior": "run novel_writing per chapter; stop on first failure",
    },
    {
        "trigger": "budget-usd",
        "behavior": "cumulative cost hard stop before next chapter if exceeded",
    },
    {
        "trigger": "max-chapters",
        "behavior": "default cap 10; --max-chapters 1..10",
    },
)

MAX_BATCH_CHAPTERS = 10


@dataclass
class BatchResult:
    start_chapter: int
    max_chapters: int
    budget_usd: float | None
    stopped_reason: str
    total_cost_usd: float
    chapters_attempted: int
    chapters_succeeded: int
    chapter_results: list[dict[str, Any]] = field(default_factory=list)
    preflight_only: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _chapter_success(result: PilotResult) -> bool:
    if result.error:
        return False
    if result.failed > 0:
        return False
    return result.emit_chapter_completed


def _sum_cost(results: list[PilotResult]) -> float:
    total = 0.0
    for r in results:
        if r.total_cost_usd is not None:
            total += float(r.total_cost_usd)
    return total


def run_production_batch(
    *,
    start_chapter: int = 1,
    max_chapters: int = 3,
    state_dir: Path | None = None,
    budget_usd: float | None = None,
    preflight_only: bool = False,
    stop_on_fail: bool = True,
    operator: str = "operator",
    save_chapter_records_dir: Path | None = None,
    pilot_runner: Callable[..., PilotResult] | None = None,
) -> BatchResult:
    """Run up to max_chapters sequentially; stop on fail or budget."""
    if max_chapters < 1 or max_chapters > MAX_BATCH_CHAPTERS:
        raise ValueError(f"max_chapters must be 1..{MAX_BATCH_CHAPTERS}, got {max_chapters}")
    if start_chapter < 1:
        raise ValueError(f"start_chapter must be >= 1, got {start_chapter}")

    runner = pilot_runner or run_production_pilot
    checks = preflight_checklist(
        state_dir=state_dir,
        chapter_num=start_chapter,
        require_real_llm_gate=not preflight_only,
    )
    if not preflight_ok(checks):
        empty = PilotResult(
            chapter_num=start_chapter,
            workflow_name="novel_writing",
            provider=None,
            preflight_ok=False,
            preflight_checks=checks,
            preflight_only=preflight_only,
            error="batch preflight failed",
        )
        return BatchResult(
            start_chapter=start_chapter,
            max_chapters=max_chapters,
            budget_usd=budget_usd,
            stopped_reason="preflight_failed",
            total_cost_usd=0.0,
            chapters_attempted=0,
            chapters_succeeded=0,
            chapter_results=[empty.to_dict()],
            preflight_only=preflight_only,
        )

    if preflight_only:
        return BatchResult(
            start_chapter=start_chapter,
            max_chapters=max_chapters,
            budget_usd=budget_usd,
            stopped_reason="preflight_only",
            total_cost_usd=0.0,
            chapters_attempted=0,
            chapters_succeeded=0,
            preflight_only=True,
        )

    outcomes: list[PilotResult] = []
    stopped_reason = "completed"

    for offset in range(max_chapters):
        chapter_num = start_chapter + offset
        cumulative = _sum_cost(outcomes)
        if budget_usd is not None and cumulative >= budget_usd:
            stopped_reason = "budget_exceeded"
            break

        remaining = None
        if budget_usd is not None:
            remaining = max(budget_usd - cumulative, 0.0)
            if remaining <= 0:
                stopped_reason = "budget_exceeded"
                break

        result = runner(
            chapter_num=chapter_num,
            state_dir=state_dir,
            cost_budget_usd=remaining,
        )
        outcomes.append(result)

        if save_chapter_records_dir is not None:
            record_path = save_chapter_records_dir / f"ch{chapter_num:03d}.json"
            save_pilot_record(result, record_path, operator=operator)

        if stop_on_fail and not _chapter_success(result):
            stopped_reason = "chapter_failed"
            break

    succeeded = sum(1 for r in outcomes if _chapter_success(r))
    if stopped_reason == "completed" and len(outcomes) < max_chapters:
        if budget_usd is not None and _sum_cost(outcomes) >= budget_usd:
            stopped_reason = "budget_exceeded"

    return BatchResult(
        start_chapter=start_chapter,
        max_chapters=max_chapters,
        budget_usd=budget_usd,
        stopped_reason=stopped_reason,
        total_cost_usd=_sum_cost(outcomes),
        chapters_attempted=len(outcomes),
        chapters_succeeded=succeeded,
        chapter_results=[r.to_dict() for r in outcomes],
    )


def build_batch_summary(batch: BatchResult, *, batch_id: str | None = None) -> dict[str, Any]:
    """Batch summary JSON (chapter_results already serialized)."""
    from datetime import datetime, timezone

    if batch_id is None:
        end = batch.start_chapter + max(batch.chapters_attempted, 1) - 1
        batch_id = f"batch-ch{batch.start_chapter}-{end}"

    return {
        "batch_id": batch_id,
        "start_chapter": batch.start_chapter,
        "max_chapters": batch.max_chapters,
        "budget_usd": batch.budget_usd,
        "stopped_reason": batch.stopped_reason,
        "total_cost_usd": batch.total_cost_usd,
        "chapters_attempted": batch.chapters_attempted,
        "chapters_succeeded": batch.chapters_succeeded,
        "chapters": [_json_safe(ch) for ch in batch.chapter_results],
        "recorded_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


def save_batch_summary(batch: BatchResult, path: Path, *, batch_id: str | None = None) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = build_batch_summary(batch, batch_id=batch_id)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def describe_production_batch() -> list[dict[str, str]]:
    return list(BATCH_BEHAVIOR)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Sequential batch chapter production (LINGWEN_REAL_LLM=1)",
    )
    parser.add_argument("--start-chapter", type=int, default=1)
    parser.add_argument("--max-chapters", type=int, default=3)
    parser.add_argument("--state-dir", type=Path, default=None)
    parser.add_argument("--budget-usd", type=float, default=None)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument(
        "--save-summary",
        type=Path,
        default=None,
        metavar="PATH",
        help="Write batch summary JSON",
    )
    parser.add_argument(
        "--save-chapter-records-dir",
        type=Path,
        default=None,
        help="Write per-chapter pilot JSON into directory",
    )
    parser.add_argument("--operator", default="operator")
    parser.add_argument("--batch-id", default=None)
    args = parser.parse_args(argv)

    try:
        batch = run_production_batch(
            start_chapter=args.start_chapter,
            max_chapters=args.max_chapters,
            state_dir=args.state_dir,
            budget_usd=args.budget_usd,
            preflight_only=args.preflight_only,
            operator=args.operator,
            save_chapter_records_dir=args.save_chapter_records_dir,
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    if args.save_summary is not None:
        save_batch_summary(batch, args.save_summary, batch_id=args.batch_id)

    payload = batch.to_dict()
    if args.save_summary is not None:
        payload["summary_path"] = str(args.save_summary)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))

    if args.preflight_only:
        return 0 if batch.stopped_reason != "preflight_failed" else 1
    if batch.stopped_reason == "preflight_failed":
        return 1
    if batch.stopped_reason == "chapter_failed":
        return 1
    if batch.chapters_succeeded < batch.chapters_attempted:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
