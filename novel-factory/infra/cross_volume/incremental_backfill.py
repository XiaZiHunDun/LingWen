"""Phase 9.63 F54 + 9.68 F60: incremental CVG backfill after novel_writing workflow."""
from __future__ import annotations

import logging
import os
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

from infra.cross_volume.backfill import Backfiller, BackfillStats
from infra.got.data_structures import NodeStatus
from infra.got.scheduler import ExecutionSummary

logger = logging.getLogger(__name__)

EMIT_CHAPTER_NODE = "emit_chapter"
WORKFLOW_WITH_INCREMENTAL = frozenset({"novel_writing"})

# Phase 9.68 F60: hook 默认行为表 (runbook / Dashboard 引用)
INCREMENTAL_BACKFILL_HOOK_BEHAVIOR: tuple[dict[str, str], ...] = (
    {
        "trigger": "env LINGWEN_INCREMENTAL_BACKFILL",
        "behavior": "opt-in: 1|true|yes 启用; 默认 off",
    },
    {
        "trigger": "workflow_name",
        "behavior": "仅 novel_writing",
    },
    {
        "trigger": "ExecutionSummary",
        "behavior": "failed=0 且 paused=False",
    },
    {
        "trigger": EMIT_CHAPTER_NODE,
        "behavior": "NodeStatus.COMPLETED",
    },
    {
        "trigger": "chapter_num",
        "behavior": "initial_inputs 或 write_chapter/read_snapshot/emit_chapter output",
    },
    {
        "trigger": "Backfiller.run_chapters",
        "behavior": "单章规则抽取; 已有节点 idempotent skip (best-effort)",
    },
)


def incremental_backfill_enabled(explicit: bool | None = None) -> bool:
    """Opt-in via LINGWEN_INCREMENTAL_BACKFILL=1 (default off)."""
    if explicit is not None:
        return explicit
    return os.environ.get("LINGWEN_INCREMENTAL_BACKFILL", "").lower() in (
        "1",
        "true",
        "yes",
    )


def extract_chapter_num(
    initial_inputs: Mapping[str, Any] | None,
    executions: Mapping[str, Any] | None,
) -> int | None:
    """Resolve chapter_num from workflow seed inputs or node outputs."""
    if initial_inputs:
        raw = initial_inputs.get("chapter_num")
        if raw is not None:
            try:
                num = int(raw)
                if num >= 1:
                    return num
            except (TypeError, ValueError):
                pass

    if not executions:
        return None

    for node_id in ("write_chapter", "read_snapshot", EMIT_CHAPTER_NODE):
        execution = executions.get(node_id)
        if execution is None:
            continue
        output = getattr(execution, "output", None)
        if isinstance(output, dict):
            raw = output.get("chapter_num")
            if raw is not None:
                try:
                    num = int(raw)
                    if num >= 1:
                        return num
                except (TypeError, ValueError):
                    continue
    return None


def should_run_incremental_backfill(
    workflow_name: str,
    summary: ExecutionSummary,
    executions: Mapping[str, Any],
) -> bool:
    """True when novel_writing finished cleanly and emit_chapter completed."""
    if workflow_name not in WORKFLOW_WITH_INCREMENTAL:
        return False
    if summary.failed > 0 or summary.paused:
        return False
    emit = executions.get(EMIT_CHAPTER_NODE)
    if emit is None:
        return False
    status = getattr(emit, "status", None)
    return status == NodeStatus.COMPLETED


def run_incremental_backfill(
    chapter_num: int,
    *,
    execute: bool = True,
    backfiller: Backfiller | None = None,
) -> BackfillStats | None:
    """Run rule-based backfill for a single chapter (idempotent skip existing nodes)."""
    if chapter_num < 1:
        return None
    bf = backfiller or Backfiller()
    return bf.run_chapters([chapter_num], dry_run=not execute)


def maybe_after_workflow(
    workflow_name: str,
    initial_inputs: Mapping[str, Any] | None,
    executions: Mapping[str, Any],
    summary: ExecutionSummary,
    *,
    enabled: bool | None = None,
    backfiller: Backfiller | None = None,
) -> BackfillStats | None:
    """Workflow hook: incremental backfill when emit_chapter completes."""
    if not incremental_backfill_enabled(enabled):
        return None
    if not should_run_incremental_backfill(workflow_name, summary, executions):
        return None
    chapter_num = extract_chapter_num(initial_inputs, executions)
    if chapter_num is None:
        logger.debug("incremental backfill skipped: chapter_num unresolved")
        return None
    stats = run_incremental_backfill(
        chapter_num, execute=True, backfiller=backfiller
    )
    logger.info(
        "incremental backfill ch=%s workflow=%s stats=%s",
        chapter_num,
        workflow_name,
        stats.summary() if stats else None,
    )
    return stats


def describe_incremental_backfill_hook() -> list[dict[str, str]]:
    """Return hook behavior rows for runbook / CLI docs."""
    return [dict(row) for row in INCREMENTAL_BACKFILL_HOOK_BEHAVIOR]


def backfill_stats_to_dict(value: Any) -> dict[str, Any] | None:
    """Serialize BackfillStats (or passthrough dict) for Dashboard JSON."""
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if is_dataclass(value):
        return asdict(value)
    summary_fn = getattr(value, "summary", None)
    if callable(summary_fn):
        return {"summary": summary_fn()}
    return {"value": str(value)}


def explain_incremental_backfill_skip(
    workflow_name: str,
    initial_inputs: Mapping[str, Any] | None,
    executions: Mapping[str, Any],
    summary: ExecutionSummary,
    *,
    enabled: bool | None = None,
) -> str | None:
    """Human-readable skip reason; None when hook would invoke backfiller (if enabled)."""
    if not incremental_backfill_enabled(enabled):
        return "disabled: set LINGWEN_INCREMENTAL_BACKFILL=1"
    if workflow_name not in WORKFLOW_WITH_INCREMENTAL:
        return f"unsupported_workflow: {workflow_name!r}"
    if summary.failed > 0:
        return f"workflow_failed: failed={summary.failed}"
    if summary.paused:
        return "workflow_paused"
    emit = executions.get(EMIT_CHAPTER_NODE)
    if emit is None:
        return f"missing_node: {EMIT_CHAPTER_NODE}"
    status = getattr(emit, "status", None)
    if status != NodeStatus.COMPLETED:
        return f"emit_chapter_not_completed: {status!r}"
    if extract_chapter_num(initial_inputs, executions) is None:
        return "chapter_num_unresolved"
    return None
