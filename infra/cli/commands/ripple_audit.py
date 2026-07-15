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
from infra.cli.path_utils import resolve_project_db_path
from infra.cross_volume.storage import RippleStorage

from .base import Command

MAX_AUDIT_LIMIT = 1000


def _get_storage() -> RippleStorage:
    """Phase 9.14: 1:1 with Phase 9.11 backfill pattern (lazy import).

    Phase 13.0 T4 M4: db path resolves via $LINGWEN_PROJECT_ROOT (preferred)
    or CWD fallback with WARNING (1-version deprecation).
    """
    return RippleStorage(db_path=resolve_project_db_path())


def _sanitize_reason(reason: str) -> str:
    """Strip control chars + newlines from reason (log-injection hardening)."""
    return re.sub(r"[\x00-\x1f\x7f]", "", reason).strip()


class RippleAuditCommand(Command):
    """Print audit history for a ripple (newest first)."""

    name = "ripple-audit"
    description = "打印涟漪审计历史 (Phase 9.14)"

    def execute(self, options: UnifiedOptions) -> int:
        action = getattr(options, "action", "show") or "show"
        if action == "purge":
            return self._execute_purge(options)
        return self._execute_show(options)

    def _execute_purge(self, options: UnifiedOptions) -> int:
        """Phase 9.61 F52: retention cleanup for ripple_audit."""
        from infra.cross_volume.audit_retention import (
            parse_older_than,
            purge_audit_entries_older_than,
        )

        try:
            delta = parse_older_than(options.older_than)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        storage = _get_storage()
        mode = "execute" if options.execute else "dry-run"
        result = purge_audit_entries_older_than(
            storage, delta, execute=options.execute
        )
        print(
            f"[PURGE] mode={mode} older_than={options.older_than}"
            f" cutoff={result.cutoff_iso}"
        )
        print(f"  matched={result.matched} deleted={result.deleted}")
        if not options.execute and result.matched:
            print("  (re-run with --execute to delete)")
        return 0

    def _execute_show(self, options: UnifiedOptions) -> int:
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
