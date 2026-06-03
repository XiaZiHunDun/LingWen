"""llm-analyze subparser — LLM-based issue decision analysis."""
import argparse


def add_llm_analyze_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """注册 'llm-analyze' 子命令的参数解析器。

    用法:
        lingwen.py llm-analyze --chapter 42
        lingwen.py llm-analyze --chapter 42 --issue-file issues.json
    """
    parser = subparsers.add_parser(
        "llm-analyze",
        help="LLM质检决策分析",
        description="对检测到的问题进行严重性判断和修复建议",
    )
    parser.add_argument(
        "--chapter",
        type=int,
        required=True,
        help="章节号",
    )
    parser.add_argument(
        "--issue-file",
        type=str,
        help="问题JSON文件路径",
    )
    return parser
