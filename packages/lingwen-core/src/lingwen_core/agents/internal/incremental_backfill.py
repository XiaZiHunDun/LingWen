"""Phase 17.0 local stub for `infra.cross_volume.incremental_backfill`.
The three functions below provide the minimal runtime contract that
chapter_production_pilot, production_summary, and chapter_memory_hook
depend on, so they can decouple from the legacy cross_volume module
without a behavioral change for the default-off case.

Real upstream module (preserved at infra/cross_volume/incremental_backfill.py)
is still importable via the legacy path; this stub is the drop-in replacement
for Phase 17 callers. Phase 18 will replace it with a domain package entity.
"""
from __future__ import annotations

import os
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping


# True upstream behavior, preserved verbatim so callers see no regression.
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

    for node_id in ("write_chapter", "read_snapshot", "emit_chapter"):
        execution = executions.get(node_id)
        if execution is None:
            continue
        output = getattr(execution, "output", None)
        if output is None and isinstance(execution, dict):
            output = execution.get("output")
        if output is None:
            continue
        if isinstance(output, Mapping):
            for key in ("chapter_num", "chapter", "chapter_no"):
                if key in output:
                    try:
                        n = int(output[key])
                        if n >= 1:
                            return n
                    except (TypeError, ValueError):
                        continue
    return None


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
