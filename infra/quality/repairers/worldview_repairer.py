#!/usr/bin/env python3
"""
世界观统一修复器
将科幻术语替换为修真术语
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.quality import YAMLRuleRepairer


class WorldviewRepairer(YAMLRuleRepairer):
    """
    世界观统一修复器

    使用YAML规则文件进行术语替换
    """

    def __init__(self, paths=None):
        super().__init__("worldview_rules.yaml", paths)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='世界观统一修复器')
    parser.add_argument('--chapters', type=str, default='1-10',
                        help='章节范围')
    parser.add_argument('--dry-run', action='store_true',
                        help='只输出不保存')
    parser.add_argument('--limit', type=int, default=None,
                        help='限制处理章节数量')

    args = parser.parse_args()

    # 解析章节范围
    chapters = []
    for part in args.chapters.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            chapters.extend(range(start, end + 1))
        else:
            chapters.append(int(part))

    if args.limit:
        chapters = chapters[:args.limit]

    print(f"待处理章节: {len(chapters)} 个")
    print(f"模式: {'干跑(dry-run)' if args.dry_run else '实际修改'}")
    print("-" * 50)

    repairer = WorldviewRepairer()

    if args.dry_run:
        for ch in chapters:
            new_content = repairer.dry_run(ch)
            content = repairer.paths.read_chapter(ch)
            if new_content != content and new_content:
                count = sum(1 for old, new, _ in repairer._get_rules()
                           if old in content and new != old)
                print(f"ch{ch:03d}: [干跑] 预计替换 {count} 处")
            else:
                print(f"ch{ch:03d}: — 无需修改")
    else:
        total_changes = 0
        for ch in chapters:
            result = repairer.repair(ch)
            total_changes += result.changes
            if result.changes > 0:
                print(f"ch{ch:03d}: ✓ 替换 {result.changes} 处")
            else:
                print(f"ch{ch:03d}: — 无需修改")

        print("-" * 50)
        print(f"完成: 总替换 {total_changes} 处")


if __name__ == '__main__':
    main()
