"""verify subparser — chapter quality verification (QualityVerifier)."""
import argparse


def add_verify_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """注册 'verify' 子命令的参数解析器。

    用法:
        lingwen.py verify 50-60
        lingwen.py verify 50-60 --repaired
    """
    parser = subparsers.add_parser(
        "verify",
        help="验证章节质量",
        description="使用 QualityVerifier 验证章节质量",
    )
    parser.add_argument(
        "range",
        nargs="?",
        default="all",
        help="章节范围，如 1-10, 5, 20-30 或 all (默认: all)",
    )
    parser.add_argument("--repaired", action="store_true", help="仅验证已修复的章节")
    parser.add_argument("--parallel", type=int, default=4, help="并行处理数量 (默认: 4)")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    return parser
