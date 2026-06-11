"""ripple-audit subparser (Phase 9.14 + 9.61 F52 purge)."""
import argparse


def add_ripple_audit_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """注册 'ripple-audit' 子命令的参数解析器.

    用法:
        lingwen.py ripple-audit rip-applied-1
        lingwen.py ripple-audit rip-applied-1 --limit 10
        lingwen.py ripple-audit purge --older-than 90d [--execute]
    """
    parser = subparsers.add_parser(
        "ripple-audit",
        help="打印涟漪审计历史 / 保留策略清理 (Phase 9.14 + 9.61)",
        description="Print ripple_audit history or purge old audit rows.",
    )
    audit_subs = parser.add_subparsers(dest="audit_action")

    purge_p = audit_subs.add_parser(
        "purge",
        help="Purge old ripple_audit rows (Phase 9.61 F52, default dry-run)",
        description="Delete ripple_audit rows older than --older-than (default dry-run).",
    )
    purge_p.add_argument(
        "--older-than",
        type=str,
        default="90d",
        help="Retention window to keep (delete older), e.g. 90d, 30d, 12h (default 90d)",
    )
    purge_p.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Apply deletion (default: dry-run count only)",
    )

    parser.add_argument(
        "ripple_id",
        nargs="?",
        type=str,
        default=None,
        help="Ripple id to inspect (e.g. 'rip-applied-1')",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Max audit entries to print (default 20)",
    )
    return parser
