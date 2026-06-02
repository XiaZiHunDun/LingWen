#!/usr/bin/env python3
"""
灵文 CLI - 统一命令行入口

Usage:
    lingwen.py <command> [options]

Commands:
    check      - 检查章节质量 (quick/full/llm)
    repair     - 批量修复章节问题
    verify     - 验证章节质量
    status     - 查看章节状态
    doctor     - 系统诊断
    polish     - 关键章节深度润色
    anti-trope - 生成反套路创意选项
    llm-analyze - LLM质检决策分析
"""

import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.cli import RangeParser, AntiTropeOptions, CheckOptions, LLMAnalyzeOptions, RepairOptions, VerifyOptions, PolishOptions, UnifiedOptions, StoryContractOptions
from infra.cli.commands import get_command, list_commands
from infra.cli.output import OutputFormatter


def create_parser() -> argparse.ArgumentParser:
    """创建参数解析器"""
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
        """
    )

    # 添加子命令解析器
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # =========================================================================
    # check 命令
    # =========================================================================
    check_parser = subparsers.add_parser(
        "check",
        help="检查章节质量",
        description="使用 QuickChecker/ComprehensiveChecker/LLMQualityChecker 检查章节质量"
    )
    check_parser.add_argument(
        "range",
        nargs="?",
        default="all",
        help="章节范围，如 1-10, 5, 20-30 或 all (默认: all)"
    )
    check_parser.add_argument(
        "--quick",
        action="store_true",
        help="快速检查 (QuickChecker)"
    )
    check_parser.add_argument(
        "--full",
        action="store_true",
        help="全面检查 (ComprehensiveChecker)"
    )
    check_parser.add_argument(
        "--llm",
        action="store_true",
        help="LLM深度检查 (LLMQualityChecker)"
    )
    check_parser.add_argument(
        "--parallel",
        type=int,
        default=4,
        help="并行处理数量 (默认: 4)"
    )
    check_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细输出"
    )
    check_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="干跑模式 (不实际修改)"
    )
    check_parser.add_argument(
        "-o", "--output",
        help="输出文件路径"
    )
    check_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="最大处理章节数 (默认: 20)"
    )

    # =========================================================================
    # repair 命令
    # =========================================================================
    repair_parser = subparsers.add_parser(
        "repair",
        help="批量修复章节问题",
        description="使用 WorldviewRepairer/AITraceRepairer 批量修复章节问题"
    )
    repair_parser.add_argument(
        "range",
        nargs="?",
        default="all",
        help="章节范围，如 1-10, 5, 20-30 或 all (默认: all)"
    )
    repair_parser.add_argument(
        "--track",
        choices=["worldview", "ai_trace", "all"],
        default="all",
        help="修复追踪类型 (默认: all)"
    )
    repair_parser.add_argument(
        "--regression",
        action="store_true",
        help="执行回归测试"
    )
    repair_parser.add_argument(
        "--parallel",
        type=int,
        default=4,
        help="并行处理数量 (默认: 4)"
    )
    repair_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细输出"
    )
    repair_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="干跑模式 (不实际修改)"
    )

    # =========================================================================
    # verify 命令
    # =========================================================================
    verify_parser = subparsers.add_parser(
        "verify",
        help="验证章节质量",
        description="使用 QualityVerifier 验证章节质量"
    )
    verify_parser.add_argument(
        "range",
        nargs="?",
        default="all",
        help="章节范围，如 1-10, 5, 20-30 或 all (默认: all)"
    )
    verify_parser.add_argument(
        "--repaired",
        action="store_true",
        help="仅验证已修复的章节"
    )
    verify_parser.add_argument(
        "--parallel",
        type=int,
        default=4,
        help="并行处理数量 (默认: 4)"
    )
    verify_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细输出"
    )

    # =========================================================================
    # status 命令
    # =========================================================================
    status_parser = subparsers.add_parser(
        "status",
        help="查看章节状态",
        description="查看章节的存在状态和文件大小"
    )
    status_parser.add_argument(
        "range",
        nargs="?",
        default="all",
        help="章节范围，如 1-10, 5, 20-30 或 all (默认: all)"
    )
    status_parser.add_argument(
        "--json",
        action="store_true",
        help="JSON格式输出"
    )
    status_parser.add_argument(
        "--summary",
        action="store_true",
        help="仅显示摘要"
    )

    # =========================================================================
    # doctor 命令
    # =========================================================================
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="系统诊断",
        description="检查环境、数据库、章节文件等系统状态"
    )

    # =========================================================================
    # polish 命令
    # =========================================================================
    polish_parser = subparsers.add_parser(
        "polish",
        help="关键章节Claude深度润色",
        description="使用 Claude Code 对关键章节进行深度润色"
    )
    polish_parser.add_argument(
        "range",
        nargs="?",
        default="all",
        help="章节范围，如 1-10, 5, 20-30 或 all (默认: all)"
    )
    polish_parser.add_argument(
        "--chapter",
        type=int,
        help="指定单个章节号"
    )
    polish_parser.add_argument(
        "--key-type",
        choices=["regular", "climax", "emotional", "foreshadow", "creation"],
        help="指定关键章节类型"
    )
    polish_parser.add_argument(
        "--auto-detect",
        action="store_true",
        help="自动检测关键章节"
    )
    polish_parser.add_argument(
        "--parallel",
        type=int,
        default=4,
        help="并行处理数量 (默认: 4)"
    )
    polish_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细输出"
    )
    polish_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="干跑模式 (不实际修改)"
    )

    # =========================================================================
    # anti-trope 命令
    # =========================================================================
    anti_trope_parser = subparsers.add_parser(
        "anti-trope",
        help="生成反套路创意选项",
        description="在章节大纲生成后、审核前，生成反套路创意选项供选择"
    )
    anti_trope_parser.add_argument(
        "--outline",
        type=str,
        required=True,
        help="章节大纲内容"
    )
    anti_trope_parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="生成数量 (默认: 3)"
    )
    anti_trope_parser.add_argument(
        "--format",
        action="store_true",
        default=True,
        help="格式化输出"
    )

    # =========================================================================
    # llm-analyze 命令
    # =========================================================================
    llm_analyze_parser = subparsers.add_parser(
        "llm-analyze",
        help="LLM质检决策分析",
        description="对检测到的问题进行严重性判断和修复建议"
    )
    llm_analyze_parser.add_argument(
        "--chapter",
        type=int,
        required=True,
        help="章节号"
    )
    llm_analyze_parser.add_argument(
        "--issue-file",
        type=str,
        help="问题JSON文件路径"
    )

    # =========================================================================
    # story-contract 命令
    # =========================================================================
    story_contract_parser = subparsers.add_parser(
        "story-contract",
        help="生成故事合约",
        description="根据题材和查询生成故事合约，包含反套路约束"
    )
    story_contract_parser.add_argument(
        "query",
        nargs="?",
        default="",
        help="查询文本，用于题材路由 (默认: 空字符串)"
    )
    story_contract_parser.add_argument(
        "--genre",
        type=str,
        help="指定题材 (如: 都市, 玄幻)"
    )
    story_contract_parser.add_argument(
        "--chapter",
        type=int,
        help="章节号，用于生成章节级合约"
    )
    story_contract_parser.add_argument(
        "--persist",
        action="store_true",
        help="持久化合约到 .story-system/ 目录"
    )
    story_contract_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细输出"
    )

    return parser


def parse_range(range_str: str, range_parser: RangeParser) -> list:
    """
    解析章节范围字符串

    Args:
        range_str: 范围字符串
        range_parser: RangeParser 实例

    Returns:
        章节编号列表
    """
    try:
        return range_parser.parse(range_str)
    except ValueError as e:
        print(f"[错误] 范围解析失败: {e}")
        sys.exit(1)


def build_options(args: argparse.Namespace) -> UnifiedOptions:
    """
    根据命令行参数构建选项对象

    Args:
        args: 解析后的命令行参数

    Returns:
        UnifiedOptions 或其子类实例
    """
    command = args.command

    # 不需要range的命令
    no_range_commands = {"doctor", "anti-trope", "llm-analyze"}
    if command in no_range_commands:
        range_parser = RangeParser()  # still need to create for parse_range calls below

    # doctor 命令没有 range 参数
    if command == "doctor":
        return UnifiedOptions(
            range=[],
            parallel=1,
            verbose=False,
        )
    elif command == "anti-trope":
        return AntiTropeOptions(
            range=[],
            parallel=1,
            verbose=False,
            outline=getattr(args, "outline", ""),
            count=getattr(args, "count", 3),
            format=getattr(args, "format", True),
        )
    elif command == "llm-analyze":
        return LLMAnalyzeOptions(
            range=[],
            parallel=1,
            verbose=False,
            chapter=args.chapter,
            issue_file=getattr(args, "issue_file", None),
        )
    elif command == "story-contract":
        return StoryContractOptions(
            range=[],
            parallel=1,
            verbose=args.verbose,
            query=args.query,
            genre=args.genre,
            chapter=args.chapter,
            persist=args.persist,
        )

    chapter_range = parse_range(args.range, RangeParser())

    if command == "check":
        return CheckOptions(
            range=chapter_range,
            parallel=args.parallel,
            verbose=args.verbose,
            dry_run=args.dry_run,
            output=args.output,
            quick=args.quick,
            full=args.full,
            llm=args.llm,
            limit=args.limit,
        )
    elif command == "repair":
        return RepairOptions(
            range=chapter_range,
            parallel=args.parallel,
            verbose=args.verbose,
            dry_run=args.dry_run,
            track=args.track,
            regression=args.regression,
        )
    elif command == "verify":
        return VerifyOptions(
            range=chapter_range,
            parallel=args.parallel,
            verbose=args.verbose,
            repaired=args.repaired,
        )
    elif command == "polish":
        return PolishOptions(
            range=chapter_range,
            parallel=args.parallel,
            verbose=args.verbose,
            dry_run=args.dry_run,
            chapter=args.chapter,
            key_type=args.key_type,
            auto_detect=args.auto_detect,
        )
    else:
        # status
        return UnifiedOptions(
            range=chapter_range,
            parallel=1,
            verbose=args.verbose if hasattr(args, "verbose") else False,
        )


def main() -> int:
    """主入口函数"""
    parser = create_parser()
    args = parser.parse_args()

    # 没有指定命令时显示帮助
    if args.command is None:
        parser.print_help()
        print("\n可用命令:")
        for cmd in list_commands():
            print(f"  {cmd['name']:12s} - {cmd['description']}")
        return 0

    # 获取命令实例
    cmd = get_command(args.command)
    if cmd is None:
        print(f"[错误] 未知命令: {args.command}")
        return 1

    # 构建选项
    options = build_options(args)

    # 执行命令
    try:
        return cmd.execute(options)
    except KeyboardInterrupt:
        print("\n[中断] 命令被用户中断")
        return 130
    except Exception as e:
        print(f"[错误] 命令执行失败: {e}")
        if args.verbose if hasattr(args, "verbose") else False:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())