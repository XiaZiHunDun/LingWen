"""ripple-audit command - Phase 9.14: print ripple_audit history for 1 ripple.

1:1 pattern with infra/cli/commands/backfill.py (Phase 9.11). Reads
ripple_audit table via RippleStorage.get_audit_history(). 0 启动 dashboard
server, 0 走 HTTP API (直连 SQLite, 跟 Phase 9.11 backfill 一致)。

Usage:
    lingwen.py ripple-audit rip-applied-1
    lingwen.py ripple-audit rip-applied-1 --limit 10
"""
import re
import sys
from pathlib import Path

from infra.cli.options import UnifiedOptions
from infra.cross_volume.storage import RippleStorage

from .base import Command

DEFAULT_RIPPLE_DB = Path(".state/ripple.db")
MAX_AUDIT_LIMIT = 1000


def _get_storage() -> RippleStorage:
    """Phase 9.14: 1:1 with Phase 9.11 backfill pattern (lazy import)."""
    return RippleStorage(db_path=DEFAULT_RIPPLE_DB)


def _sanitize_reason(reason: str) -> str:
    """Strip control chars + newlines from reason (log-injection hardening)."""
    return re.sub(r"[\x00-\x1f\x7f]", "", reason).strip()


class RippleAuditCommand(Command):
    """Print audit history for a ripple (newest first)."""

    name = "ripple-audit"
    description = "打印涟漪审计历史 (Phase 9.14)"

    def execute(self, options: UnifiedOptions) -> int:
        # lingwen.py:127 always passes RippleAuditOptions — direct attr access.
        ripple_id = options.ripple_id
        limit = options.limit
        if not ripple_id:
            print("Error: ripple_id is required", file=sys.stderr)
            return 1
        if limit < 1:
            print(f"Error: --limit must be >= 1 (got {limit})", file=sys.stderr)
            return 1
        if limit > MAX_AUDIT_LIMIT:
            print(
                f"Error: --limit too large, max {MAX_AUDIT_LIMIT} (got {limit})",
                file=sys.stderr,
            )
            return 1
        storage = _get_storage()
        if storage.get_ripple_by_id(ripple_id) is None:
            print(f"Error: ripple {ripple_id} not found", file=sys.stderr)
            return 1
        entries = storage.get_audit_history(ripple_id, limit=limit)
        if not entries:
            print(f"No audit entries for {ripple_id} (0 entries)")
            return 0
        print(f"Audit history for {ripple_id} ({len(entries)} entries):")
        for e in entries:
            prev = f"[{e.prev_status} -> " if e.prev_status else "["
            reason_str = f"  reason: {_sanitize_reason(e.reason)}" if e.reason else ""
            print(
                f"  {e.created_at:<19}  {prev}{e.new_status}]  "
                f"{e.action:<12} by {e.actor} ({e.origin}){reason_str}"
            )
        return 0
