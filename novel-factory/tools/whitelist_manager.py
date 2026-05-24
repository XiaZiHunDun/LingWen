#!/usr/bin/env python3
"""
白名单管理工具

用法:
    python tools/whitelist_manager.py --list-whitelist
    python tools/whitelist_manager.py --add-feedback --checker timeline_checker --type false_positive
    python tools/whitelist_manager.py --check-skip --checker timeline_checker --scene cosmic
    python tools/whitelist_manager.py --statistics
"""

import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.consistency.engine.whitelist_manager import WhitelistManager


def main():
    parser = argparse.ArgumentParser(description='白名单管理工具')
    parser.add_argument('--list-whitelist', action='store_true', help='列出所有白名单')
    parser.add_argument('--add-feedback', action='store_true', help='添加反馈条目')
    parser.add_argument('--check-skip', action='store_true', help='检查是否应跳过')
    parser.add_argument('--statistics', action='store_true', help='显示统计信息')
    parser.add_argument('--checker', type=str, help='检查器类型')
    parser.add_argument('--scene', type=str, help='场景类型')
    parser.add_argument('--type', type=str, choices=['false_positive', 'confirmed'], help='反馈类型')
    parser.add_argument('--chapter', type=int, help='章节号')

    args = parser.parse_args()

    manager = WhitelistManager()

    if args.list_whitelist:
        print("=== 白名单摘要 ===")
        summary = manager.get_whitelist_summary()
        for key, value in summary.items():
            print(f"  {key}: {value}")

        print("\n=== 场景白名单 ===")
        for entry in manager.whitelist_data.get("scene_whitelist", []):
            print(f"  {entry.get('scene_type')}: skip {entry.get('skip_checkers')}")

        print("\n=== 角色白名单 ===")
        for entry in manager.whitelist_data.get("character_whitelist", []):
            print(f"  {entry.get('character')}: skip {entry.get('skip_checkers')}")

        print("\n=== 词汇白名单 ===")
        for entry in manager.whitelist_data.get("vocabulary_whitelist", []):
            print(f"  {entry.get('keyword')}: skip {entry.get('skip_checker')}")

    elif args.statistics:
        print("=== 统计信息 ===")
        stats = manager.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")

    elif args.check_skip:
        if not args.checker or not args.scene:
            print("错误: --check-skip 需要 --checker 和 --scene")
            return 1

        context = {'scene_type': {'type': args.scene}, 'content': ''}
        should_skip, reason = manager.should_skip(args.checker, context)
        print(f"{args.checker} + {args.scene}: skip={should_skip}, reason={reason}")

    elif args.add_feedback:
        if not args.checker or not args.type:
            print("错误: --add-feedback 需要 --checker 和 --type")
            return 1

        issue_data = {
            'issue_type': 'manual_feedback',
            'checker_type': args.checker,
            'severity': 'P1',
            'content': ''
        }
        is_false_positive = (args.type == 'false_positive')
        manager.add_feedback_entry(issue_data, is_false_positive)
        print(f"已添加反馈: {args.checker} = {'误报' if is_false_positive else '确认问题'}")
        print(f"当前统计: {manager.get_statistics()}")

    else:
        parser.print_help()

    return 0


if __name__ == '__main__':
    sys.exit(main())