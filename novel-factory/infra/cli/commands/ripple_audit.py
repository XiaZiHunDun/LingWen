"""ripple-audit command - Phase 9.14: print ripple_audit history for 1 ripple.

1:1 pattern with infra/cli/commands/backfill.py (Phase 9.11). Reads
ripple_audit table via RippleStorage.get_audit_history(). 0 启动 dashboard
server, 0 走 HTTP API (直连 SQLite, 跟 Phase 9.11 backfill 一致)。

Usage:
    lingwen.py ripple-audit rip-applied-1
    lingwen.py ripple-audit rip-applied-1 --limit 10
"""
import sys
from pathlib import Path

from infra.cli.options import RippleAuditOptions, UnifiedOptions
from infra.cross_volume.storage import RippleStorage

from .base import Command

DEFAULT_RIPPLE_DB = Path(".state/ripple.db")


def _get_storage() -> RippleStorage:
    """Phase 9.14: 1:1 with Phase 9.11 backfill pattern (lazy import)."""
    return RippleStorage(db_path=DEFAULT_RIPPLE_DB)


class RippleAuditCommand(Command):
    """Print audit history for a ripple (newest first)."""

    name = "ripple-audit"
    description = "打印涟漪审计历史 (Phase 9.14)"

    def execute(self, options: UnifiedOptions) -> int:
        audit_options = options if isinstance(options, RippleAuditOptions) else RippleAuditOptions()
        ripple_id = audit_options.ripple_id
        if not ripple_id:
            print("Error: ripple_id is required", file=sys.stderr)
            return 1
        storage = _get_storage()
        if storage.get_ripple_by_id(ripple_id) is None:
            print(f"Error: ripple {ripple_id} not found", file=sys.stderr)
            return 1
        entries = storage.get_audit_history(ripple_id, limit=audit_options.limit)
        if not entries:
            print(f"No audit entries for {ripple_id} (0 entries)")
            return 0
        print(f"Audit history for {ripple_id} ({len(entries)} entries):")
        for e in entries:
            prev = f"[{e.prev_status} -> " if e.prev_status else "["
            reason_str = f"  reason: {e.reason}" if e.reason else ""
            print(
                f"  {e.created_at}  {prev}{e.new_status}]  "
                f"{e.action} by {e.actor} ({e.origin}){reason_str}"
            )
        return 0
