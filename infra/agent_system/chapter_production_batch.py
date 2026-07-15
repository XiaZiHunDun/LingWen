"""Phase 9.81 F73: sequential batch chapter production (3–10 chapters).

Gate: LINGWEN_REAL_LLM=1 (same as pilot).
Stop-on-fail + optional cumulative --budget-usd hard stop.

CLI:
  python -m infra.agent_system.chapter_production_batch --preflight-only
  python -m infra.agent_system.chapter_production_batch --dry-run \\
    --start-chapter 364 --max-chapters 3 --budget-usd 0.15 \\
    --calibrate-from infra/.state/pilot_records/batch-361-363.json
  python -m infra.agent_system.chapter_production_batch \\
    --start-chapter 361 --max-chapters 3 --budget-usd 0.15 \\
    --save-summary infra/.state/pilot_records/batch-361-363.json
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from infra.agent_system.chapter_production_pilot import (
    PilotResult,
    PreflightCheck,
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
    {
        "trigger": "dry-run",
        "behavior": "preflight + batch_plan cost estimate; 0 LLM (F80)",
    },
    {
        "trigger": "calibrate-from",
        "behavior": "per-chapter USD from prior batch JSON or LINGWEN_BATCH_COST_ESTIMATE_USD",
    },
)

MAX_BATCH_CHAPTERS = 10
# F79 ch361-363: $0.082694 / 3 chapters
DEFAULT_COST_PER_CHAPTER_USD = 0.027565
# Do not start a chapter if remaining batch budget is below this fraction of estimate
# (prevents last-chapter partial runs that fail emit mid-workflow).
MIN_CHAPTER_BUDGET_FRACTION = 0.75


def resolve_chapter_cost_budget(
    *,
    budget_usd: float | None,
    cumulative_cost: float,
    cost_per_chapter_usd: float,
    chapters_remaining: int,
    min_fraction: float = MIN_CHAPTER_BUDGET_FRACTION,
) -> tuple[float | None, str | None]:
    """Allocate per-chapter pilot budget; skip chapter if headroom is too thin."""
    if budget_usd is None:
        return None, None
    remaining_pool = budget_usd - cumulative_cost
    if remaining_pool <= 0 or chapters_remaining <= 0:
        return None, "budget_exceeded"
    if chapters_remaining == 1:
        chapter_budget = remaining_pool
    else:
        chapter_budget = min(cost_per_chapter_usd, remaining_pool)
    floor = cost_per_chapter_usd * min_fraction
    if chapter_budget < floor:
        return None, "budget_exceeded"
    return chapter_budget, None


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
    dry_run: bool = False
    batch_plan: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def chapter_range_label(start_chapter: int, max_chapters: int) -> str:
    if max_chapters <= 1:
        return str(start_chapter)
    end = start_chapter + max_chapters - 1
    return f"{start_chapter}-{end}"


def load_calibration_from_batch(path: Path) -> tuple[float, str] | None:
    """Derive per-chapter USD from a prior batch summary JSON."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    attempted = data.get("chapters_attempted") or data.get("chapters_succeeded")
    total = data.get("total_cost_usd")
    if not isinstance(attempted, int) or attempted < 1:
        return None
    try:
        cost = float(total)
    except (TypeError, ValueError):
        return None
    return cost / attempted, f"calibrated:{path.name}"


def auto_resolve_calibrate_from() -> Path | None:
    """Pick latest batch summary JSON under the active project's pilot_records."""
    project_root = os.environ.get("LINGWEN_PROJECT_ROOT", "").strip()
    if not project_root:
        return None
    records = Path(project_root) / ".state" / "pilot_records"
    if not records.is_dir():
        return None
    batches = sorted(
        list(records.glob("batch-*.json")) + list(records.glob("studio-dod-batch-*.json")),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return batches[0] if batches else None


def resolve_cost_per_chapter_usd(
    *,
    calibrate_from: Path | None = None,
) -> tuple[float, str]:
    """Resolve estimate for batch_plan (env > calibrate file > F79 default)."""
    env = os.environ.get("LINGWEN_BATCH_COST_ESTIMATE_USD", "").strip()
    if env:
        try:
            return float(env), "env:LINGWEN_BATCH_COST_ESTIMATE_USD"
        except ValueError:
            pass
    if calibrate_from is not None:
        loaded = load_calibration_from_batch(Path(calibrate_from))
        if loaded is not None:
            return loaded
    return DEFAULT_COST_PER_CHAPTER_USD, "default:F79-ch361-363"


def build_batch_plan(
    *,
    start_chapter: int,
    max_chapters: int,
    budget_usd: float | None,
    checks: list[PreflightCheck],
    cost_per_chapter_usd: float,
    calibration_source: str,
) -> dict[str, Any]:
    """Dry-run / preflight plan: chapter range + cost ceiling estimate."""
    chapters = list(range(start_chapter, start_chapter + max_chapters))
    estimated_total = cost_per_chapter_usd * max_chapters
    within_budget = max_chapters
    if budget_usd is not None and cost_per_chapter_usd > 0:
        within_budget = min(max_chapters, int(budget_usd // cost_per_chapter_usd))
    headroom = None
    if budget_usd is not None:
        headroom = round(budget_usd - estimated_total, 6)
    return {
        "chapter_range": chapter_range_label(start_chapter, max_chapters),
        "chapters": chapters,
        "max_chapters": max_chapters,
        "cost_per_chapter_usd": round(cost_per_chapter_usd, 6),
        "estimated_total_cost_usd": round(estimated_total, 6),
        "budget_usd": budget_usd,
        "estimated_chapters_within_budget": within_budget,
        "budget_headroom_usd": headroom,
        "calibration_source": calibration_source,
        "preflight_ok": preflight_ok(checks),
        "preflight_checks": [c.to_dict() for c in checks],
    }


def _batch_result_shell(
    *,
    start_chapter: int,
    max_chapters: int,
    budget_usd: float | None,
    stopped_reason: str,
    batch_plan: dict[str, Any] | None,
    preflight_only: bool = False,
    dry_run: bool = False,
    chapter_results: list[dict[str, Any]] | None = None,
) -> BatchResult:
    return BatchResult(
        start_chapter=start_chapter,
        max_chapters=max_chapters,
        budget_usd=budget_usd,
        stopped_reason=stopped_reason,
        total_cost_usd=0.0,
        chapters_attempted=0,
        chapters_succeeded=0,
        chapter_results=chapter_results or [],
        preflight_only=preflight_only,
        dry_run=dry_run,
        batch_plan=batch_plan,
    )


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
    dry_run: bool = False,
    calibrate_from: Path | None = None,
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
    require_gate = not preflight_only and not dry_run
    checks = preflight_checklist(
        state_dir=state_dir,
        chapter_num=start_chapter,
        require_real_llm_gate=require_gate,
    )
    resolved_calibrate = calibrate_from
    if resolved_calibrate is None and budget_usd is not None:
        resolved_calibrate = auto_resolve_calibrate_from()
    cost_per_chapter, cal_source = resolve_cost_per_chapter_usd(
        calibrate_from=resolved_calibrate,
    )
    batch_plan = build_batch_plan(
        start_chapter=start_chapter,
        max_chapters=max_chapters,
        budget_usd=budget_usd,
        checks=checks,
        cost_per_chapter_usd=cost_per_chapter,
        calibration_source=cal_source,
    )

    if not preflight_ok(checks):
        empty = PilotResult(
            chapter_num=start_chapter,
            workflow_name="novel_writing",
            provider=None,
            preflight_ok=False,
            preflight_checks=checks,
            preflight_only=preflight_only or dry_run,
            error="batch preflight failed",
        )
        return _batch_result_shell(
            start_chapter=start_chapter,
            max_chapters=max_chapters,
            budget_usd=budget_usd,
            stopped_reason="preflight_failed",
            batch_plan=batch_plan,
            preflight_only=preflight_only,
            dry_run=dry_run,
            chapter_results=[empty.to_dict()],
        )

    if preflight_only:
        return _batch_result_shell(
            start_chapter=start_chapter,
            max_chapters=max_chapters,
            budget_usd=budget_usd,
            stopped_reason="preflight_only",
            batch_plan=batch_plan,
            preflight_only=True,
        )

    if dry_run:
        return _batch_result_shell(
            start_chapter=start_chapter,
            max_chapters=max_chapters,
            budget_usd=budget_usd,
            stopped_reason="dry_run",
            batch_plan=batch_plan,
            dry_run=True,
        )

    outcomes: list[PilotResult] = []
    stopped_reason = "completed"

    for offset in range(max_chapters):
        chapter_num = start_chapter + offset
        cumulative = _sum_cost(outcomes)
        chapters_remaining = max_chapters - offset
        chapter_budget, budget_stop = resolve_chapter_cost_budget(
            budget_usd=budget_usd,
            cumulative_cost=cumulative,
            cost_per_chapter_usd=cost_per_chapter,
            chapters_remaining=chapters_remaining,
        )
        if budget_stop:
            stopped_reason = budget_stop
            break

        result = runner(
            chapter_num=chapter_num,
            state_dir=state_dir,
            cost_budget_usd=chapter_budget,
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
        "--dry-run",
        action="store_true",
        help="Preflight + batch_plan cost estimate; 0 LLM (requires LINGWEN_REAL_LLM=1)",
    )
    parser.add_argument(
        "--calibrate-from",
        type=Path,
        default=None,
        metavar="PATH",
        help="Prior batch JSON for per-chapter cost estimate (F80)",
    )
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
            preflight_only=args.preflight_only and not args.dry_run,
            dry_run=args.dry_run,
            calibrate_from=args.calibrate_from,
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

    if args.preflight_only and not args.dry_run:
        return 0 if batch.stopped_reason != "preflight_failed" else 1
    if args.dry_run:
        return 0 if batch.stopped_reason == "dry_run" else 1
    if batch.stopped_reason == "preflight_failed":
        return 1
    if batch.stopped_reason == "chapter_failed":
        return 1
    if batch.chapters_succeeded < batch.chapters_attempted:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
