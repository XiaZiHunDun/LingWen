"""ripple-rollback subparser (Phase 9.14).

1:1 with infra/cli/parsers/backfill.py (Phase 9.11).
"""
import argparse


def add_ripple_rollback_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """注册 'ripple-rollback' 子命令的参数解析器.

    用法:
        lingwen.py ripple-rollback rip-applied-1 --reason "误判,需要重新评估"
        lingwen.py ripple-rollback rip-applied-1 --reason "..." --actor "user:alice"
    """
    parser = subparsers.add_parser(
        "ripple-rollback",
        help="回滚已应用/已拒绝涟漪 (Phase 9.14)",
        description="Soft-rollback applied/rejected ripple to pending + write audit entry.",
    )
    parser.add_argument(
        "ripple_id",
        type=str,
        help="Ripple id to rollback (e.g. 'rip-applied-1')",
    )
    parser.add_argument(
        "--reason",
        type=str,
        required=True,
        help="Why rolling back (required, non-empty). E.g. '误判,需要重新评估'.",
    )
    parser.add_argument(
        "--actor",
        type=str,
        default="cli:lingwen-ripple",
        help="Actor identifier (default 'cli:lingwen-ripple')",
    )
    return parser
