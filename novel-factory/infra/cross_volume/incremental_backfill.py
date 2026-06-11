"""Phase 9.63 F54: incremental CVG backfill after novel_writing workflow."""
from __future__ import annotations

import logging
import os
from typing import Any, Mapping

from infra.cross_volume.backfill import Backfiller, BackfillStats
from infra.got.data_structures import NodeStatus
from infra.got.scheduler import ExecutionSummary

logger = logging.getLogger(__name__)

EMIT_CHAPTER_NODE = "emit_chapter"
WORKFLOW_WITH_INCREMENTAL = frozenset({"novel_writing"})


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
