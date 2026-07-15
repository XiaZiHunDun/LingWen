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
    ripple-reset - 重置涟漪状态 (Phase 9.18)
    init-project - 新建 minimal-short 项目脚手架
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.cli import (
    AntiTropeOptions,
    BackfillOptions,
    CascadeOptions,
    CheckOptions,
    InitProjectOptions,
    LLMAnalyzeOptions,
    PolishOptions,
    RangeParser,
    RepairOptions,
    RippleAuditOptions,
    RippleResetOptions,
    RippleRollbackOptions,
    RippleScanOptions,
    StoryContractOptions,
    VerifyOptions,
)
from infra.cli.commands import get_command, list_commands
from infra.cli.options import UnifiedOptions
from infra.cli.parsers import create_parser
from infra.cli.project_range import project_max_chapter


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
    elif command == "init-project":
        return InitProjectOptions(
            range=[],
            parallel=1,
            verbose=False,
            slug=args.slug,
            title=args.title,
            protagonist=getattr(args, "protagonist", "沈柯"),
            genre=getattr(args, "genre", "科幻悬疑"),
            out=getattr(args, "out", None),
            overwrite=getattr(args, "overwrite", False),
            creation_mode=getattr(args, "creation_mode", "companion"),
            chapters=getattr(args, "chapters", 10),
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
            corpus_root=getattr(args, "corpus_root", None),
            # Phase 9.12 additive: LLM opt-in 4 flag (getattr 容错, 0 改 Phase 9.11 tests)
            use_llm=getattr(args, "use_llm", False),
            apply=getattr(args, "apply", False),
            cache_path=getattr(args, "cache_path", None),
            llm_confidence_threshold=getattr(args, "llm_confidence_threshold", None),
            calibration_path=getattr(args, "calibration_path", None),
        )
    elif command == "ripple-scan":
        return RippleScanOptions(
            range=[],
            parallel=1,
            verbose=False,
            dry_run=False,
            calibrate=getattr(args, "calibrate", False),
            yaml_example=getattr(args, "yaml_example", False),
            gold_path=getattr(args, "gold_path", None),
            fixture_dir=getattr(args, "fixture_dir", None),
            calibration=getattr(args, "calibration", None),
            chapter=getattr(args, "chapter", 1),
        )
    # Phase 9.14 additive: 2 new top-level subcommands (0 改 backfill 分支)
    elif command == "ripple-audit":
        action = getattr(args, "audit_action", None) or "show"
        return RippleAuditOptions(
            range=[],
            parallel=1,
            verbose=False,
            dry_run=False,
            ripple_id=args.ripple_id or "",
            limit=args.limit,
            action=action,
            older_than=getattr(args, "older_than", "90d") or "90d",
            execute=getattr(args, "execute", False),
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
    elif command == "ripple-reset":
        return RippleResetOptions(
            range=[],
            parallel=1,
            verbose=False,
            dry_run=False,
            ripple_id=args.ripple_id,
            to_status=args.to_status,
        )
    elif command == "cascade":
        action = getattr(args, "cascade_action", None) or "run"
        return CascadeOptions(
            range=[],
            parallel=1,
            verbose=False,
            dry_run=False,
            ripple_id=getattr(args, "ripple_id", "") or "",
            max_depth=getattr(args, "max_depth", 3) or 3,
            max_nodes_cap=getattr(args, "max_nodes_cap", 100) or 100,
            persist=args.persist,
            # Phase 9.21 NEW
            action=action,
            run_id=getattr(args, "run_id", 0) or 0,
            reason=getattr(args, "reason", "") or "",
            execute=getattr(args, "execute", False),
            migrate_ripple_id=getattr(args, "migrate_ripple_id", None),
            older_than=getattr(args, "older_than", "90d") or "90d",
        )

    chapter_range = parse_range(args.range, RangeParser(all_chapters=project_max_chapter()))

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
            fail_severity=getattr(args, "fail_severity", None),
            fail_severity_explicit="--fail-severity" in sys.argv,
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
