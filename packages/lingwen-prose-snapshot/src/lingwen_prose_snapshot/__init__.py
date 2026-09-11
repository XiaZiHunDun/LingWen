"""lingwen-prose-snapshot — canonical prose snapshot package.

Phase 51 P3-ARCHDEBT: relocated from infra/prose_snapshot.py (195 LOC, 8 symbols).
NOT-LEAF (1 workspace dep: lingwen-prose-calibration).

Public surface: 2 consts + 6 funcs (8 total).
"""

from __future__ import annotations

from lingwen_prose_snapshot.snapshot import (
    SNAPSHOT_FILENAME,
    SNAPSHOT_VERSION,
    build_snapshot,
    diff_snapshots,
    format_diff_report,
    load_snapshot,
    save_snapshot,
    snapshot_path_for,
)

__all__ = [
    "SNAPSHOT_VERSION",
    "SNAPSHOT_FILENAME",
    "snapshot_path_for",
    "build_snapshot",
    "save_snapshot",
    "load_snapshot",
    "diff_snapshots",
    "format_diff_report",
]
