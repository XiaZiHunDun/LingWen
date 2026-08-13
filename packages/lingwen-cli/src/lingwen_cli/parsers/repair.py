"""repair subparser — batch chapter repair (WorldviewRepairer / AITraceRepairer)."""
import argparse


def add_repair_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """注册 'repair' 子命令的参数解析器。

    用法:
        lingwen.py repair 1-30 --track worldview
        lingwen.py repair 1-30 --track all --regression
    """
    parser = subparsers.add_parser(
        "repair",
        help="批量修复章节问题",
        description="使用 WorldviewRepairer/AITraceRepairer 批量修复章节问题",
    )
    parser.add_argument(
        "range",
        nargs="?",
        default="all",
        help="章节范围，如 1-10, 5, 20-30 或 all (默认: all)",
    )
    parser.add_argument(
        "--track",
        choices=["worldview", "ai_trace", "all"],
        default="all",
        help="修复追踪类型 (默认: all)",
    )
    parser.add_argument("--regression", action="store_true", help="执行回归测试")
    parser.add_argument("--parallel", type=int, default=4, help="并行处理数量 (默认: 4)")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--dry-run", action="store_true", help="干跑模式 (不实际修改)")
    return parser
