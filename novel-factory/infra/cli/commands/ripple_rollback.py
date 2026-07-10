"""ripple-rollback command - Phase 9.14: soft-rollback applied/rejected ripple.

1:1 pattern with infra/cli/commands/backfill.py (Phase 9.11). Writes
'rolled_back' audit row + clears applied_at via RippleStorage.rollback_ripple().
0 启动 dashboard server, 0 走 HTTP API.

--reason 强需 (argparse 拦 layer 1, command.execute 再 double-check 空字符串)。
"""
import sys
from pathlib import Path

from infra.cli.options import UnifiedOptions
from infra.cli.path_utils import resolve_project_db_path
from infra.cross_volume.storage import RippleStorage

from .base import Command

DEFAULT_RIPPLE_DB = Path(".state/ripple.db")


def _get_storage() -> RippleStorage:
    """Phase 9.14: 1:1 with Phase 9.11 backfill pattern (lazy import).

    Phase 13.0 T4 M4: db path resolves via $LINGWEN_PROJECT_ROOT (preferred)
    or CWD fallback with WARNING (1-version deprecation).
    """
    return RippleStorage(db_path=resolve_project_db_path())


class RippleRollbackCommand(Command):
    """Rollback an applied/rejected ripple to pending."""

    name = "ripple-rollback"
    description = "回滚已应用/已拒绝涟漪 (Phase 9.14)"

    def execute(self, options: UnifiedOptions) -> int:
        # lingwen.py:136 always passes RippleRollbackOptions — direct attr access.
        ripple_id = options.ripple_id
        reason = options.reason
        if not reason or not reason.strip():
            # argparse 应该已经拦截,这里兜底 (test 中绕过 parser)
            print("Error: --reason cannot be empty", file=sys.stderr)
            return 1
        storage = _get_storage()
        try:
            updated = storage.rollback_ripple(
                ripple_id,
                actor=options.actor,
                origin="cli",
                reason=reason,
            )
            print(
                f"Rolled back {ripple_id} -> status={updated.status} "
                f"(audit entry written, broadcast sent)"
            )
            return 0
        except KeyError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
