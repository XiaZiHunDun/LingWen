"""cascade subparser (Phase 9.19). 1:1 with ripple_audit."""
import argparse


def add_cascade_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """注册 'cascade' 子命令的参数解析器.

    用法:
        lingwen.py cascade rip-1
        lingwen.py cascade rip-1 --max-depth 5
    """
    parser = subparsers.add_parser(
        "cascade",
        help="重新运行涟漪扩散 BFS (Phase 9.19)",
        description="Re-run cascade BFS with caller-specified max_depth (not persisted).",
    )
    parser.add_argument(
        "ripple_id",
        type=str,
        help="Ripple id to trace (e.g. 'rip-1')",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=3,
        choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        help="Max BFS depth 1..10 (default 3)",
    )
    return parser
