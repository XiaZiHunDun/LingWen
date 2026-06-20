"""CLI subparser subpackage.

Mirrors the per-command structure of `infra.cli.commands` — one file per
subcommand, each exposing an `add_X_parser(subparsers)` function that
registers the subparser and its arguments.

`create_parser()` is the single entry point used by `lingwen.py`.
"""
import argparse

from .anti_trope import add_anti_trope_parser
from .backfill import add_backfill_parser
from .cascade import add_cascade_parser
from .check import add_check_parser
from .doctor import add_doctor_parser
from .init_project import add_init_project_parser, register_init_project_args
from .llm_analyze import add_llm_analyze_parser
from .polish import add_polish_parser
from .repair import add_repair_parser
from .ripple_audit import add_ripple_audit_parser
from .ripple_reset import add_ripple_reset_parser
from .ripple_rollback import add_ripple_rollback_parser
from .ripple_scan import add_ripple_scan_parser
from .status import add_status_parser
from .story_contract import add_story_contract_parser
from .verify import add_verify_parser

__all__ = ["create_parser"]


def create_parser() -> argparse.ArgumentParser:
    """创建参数解析器 — 灵文 CLI 统一入口。

    9 个子命令由 9 个 per-command 文件分散定义,本函数只是编排:
    创建主解析器,逐个注册每个子命令的 subparser。
    """
    parser = argparse.ArgumentParser(
        prog="lingwen.py",
        description="灵文 · 工业化小说生产系统 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    lingwen.py check 1-10 --quick
    lingwen.py repair 1-30 --track worldview
    lingwen.py verify 50-60 --repaired
    lingwen.py status 1-100 --summary
    lingwen.py doctor
    lingwen.py backfill --vol 1
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 注册顺序与原 lingwen.py create_parser() 保持一致(--help 输出对齐)
    add_check_parser(subparsers)
    add_repair_parser(subparsers)
    add_verify_parser(subparsers)
    add_status_parser(subparsers)
    add_doctor_parser(subparsers)
    add_polish_parser(subparsers)
    add_anti_trope_parser(subparsers)
    add_llm_analyze_parser(subparsers)
    add_story_contract_parser(subparsers)
    add_backfill_parser(subparsers)
    # Phase 9.14 additive: 2 new subcommands (ripple-audit + ripple-rollback)
    add_ripple_audit_parser(subparsers)
    add_ripple_rollback_parser(subparsers)
    # Phase 9.18 additive: ripple-reset (test/dev tool, 1:1 with ripple-rollback)
    add_ripple_reset_parser(subparsers)
    # Phase 9.19 additive: cascade (re-run BFS, 1:1 with ripple-audit)
    add_cascade_parser(subparsers)
    add_ripple_scan_parser(subparsers)
    init_parser = add_init_project_parser(subparsers)
    register_init_project_args(init_parser)

    return parser
