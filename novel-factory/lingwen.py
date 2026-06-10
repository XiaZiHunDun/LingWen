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
    backfill   - 跨卷涟漪 4 维规则回填 (Phase 9.11)
    ripple-audit - 打印涟漪审计历史 (Phase 9.14)
    ripple-rollback - 回滚已应用/已拒绝涟漪 (Phase 9.14)
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.cli import (
    AntiTropeOptions,
    BackfillOptions,
    CheckOptions,
    LLMAnalyzeOptions,
    PolishOptions,
    RangeParser,
    RepairOptions,
    RippleAuditOptions,
    RippleRollbackOptions,
    StoryContractOptions,
    UnifiedOptions,
    VerifyOptions,
)
from infra.cli.commands import get_command, list_commands
from infra.cli.parsers import create_parser


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

    # 不需要 range 的命令
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
    elif command == "backfill":
        return BackfillOptions(
            range=[],
            parallel=1,
            verbose=args.verbose,
            dry_run=args.dry_run,
            vol=args.vol,
            rules=args.rules,
            # Phase 9.12 additive: LLM opt-in 4 flag (getattr 容错, 0 改 Phase 9.11 tests)
            use_llm=getattr(args, "use_llm", False),
            apply=getattr(args, "apply", False),
            cache_path=getattr(args, "cache_path", None),
            llm_confidence_threshold=getattr(args, "llm_confidence_threshold", 3),
        )
    # Phase 9.14 additive: 2 new top-level subcommands (0 改 backfill 分支)
    elif command == "ripple-audit":
        return RippleAuditOptions(
            range=[],
            parallel=1,
            verbose=False,
            dry_run=False,
            ripple_id=args.ripple_id,
            limit=args.limit,
        )
    elif command == "ripple-rollback":
        return RippleRollbackOptions(
            range=[],
            parallel=1,
            verbose=False,
            dry_run=False,
            ripple_id=args.ripple_id,
            reason=args.reason,
            actor=getattr(args, "actor", "cli:lingwen-ripple"),
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
