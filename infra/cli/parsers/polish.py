"""polish subparser — Claude-based deep polish for key chapters."""
import argparse


def add_polish_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """注册 'polish' 子命令的参数解析器。

    用法:
        lingwen.py polish 1-30 --key-type climax
        lingwen.py polish 1-30 --auto-detect
        lingwen.py polish --chapter 42
    """
    parser = subparsers.add_parser(
        "polish",
        help="关键章节Claude深度润色",
        description="使用 Claude Code 对关键章节进行深度润色",
    )
    parser.add_argument(
        "range",
        nargs="?",
        default="all",
        help="章节范围，如 1-10, 5, 20-30 或 all (默认: all)",
    )
    parser.add_argument("--chapter", type=int, help="指定单个章节号")
    parser.add_argument(
        "--key-type",
        choices=["regular", "climax", "emotional", "foreshadow", "creation"],
        help="指定关键章节类型",
    )
    parser.add_argument("--auto-detect", action="store_true", help="自动检测关键章节")
    parser.add_argument("--parallel", type=int, default=4, help="并行处理数量 (默认: 4)")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--dry-run", action="store_true", help="干跑模式 (不实际修改)")
    return parser
