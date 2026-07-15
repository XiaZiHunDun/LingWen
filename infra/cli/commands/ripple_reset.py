"""ripple-reset command - Phase 9.18: idempotent reset ripple status (test/dev tool).

1:1 pattern with infra/cli/commands/ripple_rollback.py (Phase 9.14). Calls
storage.reset_ripple_for_test() which writes reference_ripples.status +
applied_at=NULL + ripple_audit row (action=rolled_back, origin=system,
reason="reset to <status>"). Designed for e2e test idempotency
(ripples-audit.spec.js Test 2 beforeEach).

Usage:
    lingwen.py ripple-reset rip-pending-1 --to-status pending
    lingwen.py ripple-reset rip-rejected-1 --to-status rejected
"""
import re
import sys
from pathlib import Path

from infra.cli.options import UnifiedOptions
from infra.cross_volume.storage import RippleStorage

from .base import Command

DEFAULT_RIPPLE_DB = Path(".state/ripple.db")


def _get_storage() -> RippleStorage:
    """Phase 9.18: 1:1 with Phase 9.14 ripple_rollback pattern (lazy import)."""
    return RippleStorage(db_path=DEFAULT_RIPPLE_DB)


def _sanitize_reason(reason: str) -> str:
    """Strip control chars + newlines from reason (log-injection hardening)."""
    return re.sub(r"[\x00-\x1f\x7f]", "", reason).strip()


class RippleResetCommand(Command):
    """Idempotent reset ripple status (test/dev tool, Phase 9.18)."""

    name = "ripple-reset"
    description = "重置 ripple 状态 (test/dev 工具, Phase 9.18)"

    def execute(self, options: UnifiedOptions) -> int:
        # lingwen.py:144+ always passes RippleResetOptions — direct attr access.
        ripple_id = options.ripple_id
        to_status = options.to_status
        if not ripple_id:
            print("Error: ripple_id is required", file=sys.stderr)
            return 1
        if not to_status:
            print("Error: --to-status is required", file=sys.stderr)
            return 1
        reason = _sanitize_reason(f"reset to {to_status}")
        storage = _get_storage()
        existing = storage.get_ripple_by_id(ripple_id)
        if existing is None:
            print(f"Error: ripple {ripple_id} not found", file=sys.stderr)
            return 1
        try:
            updated = storage.reset_ripple_for_test(
                ripple_id=ripple_id,
                to_status=to_status,
                actor="cli:lingwen-ripple",
                origin="system",
                reason=reason,
            )
            print(
                f"Reset {ripple_id}: status={updated.status}, applied_at=NULL "
                f"(audit entry written)"
            )
            return 0
        except (KeyError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
