"""ripple-audit subparser (Phase 9.14).

1:1 with infra/cli/parsers/backfill.py (Phase 9.11).
"""
import argparse


def add_ripple_audit_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """注册 'ripple-audit' 子命令的参数解析器.

    用法:
        lingwen.py ripple-audit rip-applied-1
        lingwen.py ripple-audit rip-applied-1 --limit 10
    """
    parser = subparsers.add_parser(
        "ripple-audit",
        help="打印涟漪审计历史 (Phase 9.14)",
        description="Print ripple_audit history for a single ripple (newest first).",
    )
    parser.add_argument(
        "ripple_id",
        type=str,
        help="Ripple id to inspect (e.g. 'rip-applied-1')",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Max audit entries to print (default 20)",
    )
    return parser
