"""Phase 9.74 F66: per-run chapter production summary for Dashboard observability."""
from __future__ import annotations

from typing import Any, Mapping

from infra.cross_volume.incremental_backfill import (
    backfill_stats_to_dict,
    extract_chapter_num,
)

CHAPTER_WORKFLOWS = frozenset({"novel_writing", "chapter_golden"})
EMIT_CHAPTER_NODE = "emit_chapter"


def _node_completed(executions: Mapping[str, Any] | None, node_id: str) -> bool:
    if not executions:
        return False
    ex = executions.get(node_id)
    if ex is None:
        return False
    if isinstance(ex, dict):
        return ex.get("status") == "completed"
    status = getattr(ex, "status", None)
    if status is None:
        return False
    value = getattr(status, "value", status)
    return value == "completed"


def build_production_summary(
    *,
    workflow_name: str | None,
    initial_inputs: Mapping[str, Any] | None,
    executions: Mapping[str, Any] | None,
    incremental_backfill: Any,
    memory_context: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Build per-run production summary for chapter workflows."""
    if workflow_name not in CHAPTER_WORKFLOWS:
        return None

    mem = memory_context
    if mem is None and initial_inputs:
        raw = initial_inputs.get("memory_context")
        mem = raw if isinstance(raw, dict) else None

    memory_source = mem.get("source") if isinstance(mem, dict) else None
    chapter_num = extract_chapter_num(initial_inputs, executions)
    bf_dict = backfill_stats_to_dict(incremental_backfill)

    return {
        "chapter_num": chapter_num,
        "memory_context_source": memory_source,
        "incremental_backfill": bf_dict,
        "emit_chapter_completed": _node_completed(executions, EMIT_CHAPTER_NODE),
    }


def build_production_summary_from_controller(controller: Any) -> dict[str, Any] | None:
    """Read MC._last_* cache after run_workflow / resume_workflow."""
    graph = getattr(controller, "_last_graph", None)
    if graph is None:
        return None

    executions: dict[str, Any] = {}
    for nid in graph.node_ids():
        if graph.has_execution(nid):
            executions[nid] = graph.get_execution(nid)

    return build_production_summary(
        workflow_name=getattr(controller, "_last_workflow_name", None),
        initial_inputs=getattr(controller, "_last_initial_inputs", None),
        executions=executions,
        incremental_backfill=getattr(controller, "_last_incremental_backfill", None),
        memory_context=getattr(controller, "_last_memory_context", None),
    )
