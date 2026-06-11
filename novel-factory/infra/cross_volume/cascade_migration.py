"""Phase 9.36 F21: opt-in v1 → v2_weighted cascade_runs migration.

Recomputes BFS with weighted=True (preview_cascade) and rewrites algorithm +
nodes/edges/actions JSON on existing cascade_runs rows. 0 schema change.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from infra.cross_volume.storage import RippleStorage

logger = logging.getLogger(__name__)


@dataclass
class CascadeMigrationStats:
    scanned: int = 0
    migrated: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


def migrate_v1_cascade_runs(
    storage: RippleStorage,
    *,
    execute: bool,
    ripple_id: str | None = None,
) -> CascadeMigrationStats:
    """Scan cascade_runs with algorithm='v1', optionally recompute as v2_weighted.

    Default (execute=False): dry-run counts only.
    execute=True: UPDATE rows in-place (idempotent — v2 rows skipped).
    """
    stats = CascadeMigrationStats()
    targets = storage.list_cascade_runs_v1(ripple_id=ripple_id)
    stats.scanned = len(targets)

    for run in targets:
        try:
            cascaded = storage.preview_cascade(run.ripple_id, max_depth=run.max_depth)
        except (KeyError, ValueError) as e:
            stats.failed += 1
            msg = f"run id={run.id} ripple={run.ripple_id}: {e}"
            stats.errors.append(msg)
            logger.warning("cascade migrate: %s", msg)
            continue

        if not execute:
            stats.migrated += 1
            continue

        updated = storage.update_cascade_run_v2(run.id, cascaded)
        if updated:
            stats.migrated += 1
        else:
            stats.skipped += 1

    return stats
