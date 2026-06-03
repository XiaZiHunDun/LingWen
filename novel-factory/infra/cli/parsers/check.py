"""check subparser — quality checking (QuickChecker/ConsistencyEngine/LLMQualityChecker)."""
import argparse


def add_check_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """注册 'check' 子命令的参数解析器。

    用法:
        lingwen.py check 1-10 --quick
        lingwen.py check 1-10 --full
        lingwen.py check 1-10 --llm
    """
    parser = subparsers.add_parser(
        "check",
        help="检查章节质量",
        description="使用 QuickChecker/ComprehensiveChecker/LLMQualityChecker 检查章节质量",
    )
    parser.add_argument(
        "range",
        nargs="?",
        default="all",
        help="章节范围，如 1-10, 5, 20-30 或 all (默认: all)",
    )
    parser.add_argument("--quick", action="store_true", help="快速检查 (QuickChecker)")
    parser.add_argument("--full", action="store_true", help="全面检查 (ComprehensiveChecker)")
    parser.add_argument("--llm", action="store_true", help="LLM深度检查 (LLMQualityChecker)")
    parser.add_argument("--parallel", type=int, default=4, help="并行处理数量 (默认: 4)")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--dry-run", action="store_true", help="干跑模式 (不实际修改)")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument("--limit", type=int, default=20, help="最大处理章节数 (默认: 20)")
    return parser
