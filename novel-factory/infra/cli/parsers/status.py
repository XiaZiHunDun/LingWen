"""status subparser — chapter existence and size stats."""
import argparse


def add_status_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """注册 'status' 子命令的参数解析器。

    用法:
        lingwen.py status 1-100
        lingwen.py status 1-100 --summary
        lingwen.py status 1-100 --json
    """
    parser = subparsers.add_parser(
        "status",
        help="查看章节状态",
        description="查看章节的存在状态和文件大小",
    )
    parser.add_argument(
        "range",
        nargs="?",
        default="all",
        help="章节范围，如 1-10, 5, 20-30 或 all (默认: all)",
    )
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    parser.add_argument("--summary", action="store_true", help="仅显示摘要")
    return parser
