"""ripple-reset subparser (Phase 9.18).

1:1 with infra/cli/parsers/ripple_rollback.py (Phase 9.14).
"""
import argparse


def add_ripple_reset_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """注册 'ripple-reset' 子命令的参数解析器.

    用法:
        lingwen.py ripple-reset rip-pending-1 --to-status pending
        lingwen.py ripple-reset rip-rejected-1 --to-status rejected
    """
    parser = subparsers.add_parser(
        "ripple-reset",
        help="重置 ripple 状态 (test/dev 工具, Phase 9.18)",
        description="Idempotent reset ripple status + write audit entry. "
                    "For e2e test idempotency (ripples-audit.spec.js Test 2 beforeEach).",
    )
    parser.add_argument(
        "ripple_id",
        type=str,
        help="Ripple id to reset (e.g. 'rip-pending-1')",
    )
    parser.add_argument(
        "--to-status",
        type=str,
        required=True,
        choices=("pending", "applied", "rejected", "failed", "created"),
        help="Target status to reset ripple to",
    )
    return parser
