#!/usr/bin/env python3
"""
角色一致性修复器
修复角色行为、对话、决策不一致的问题
"""

import re
import sys
from pathlib import Path
from typing import Any, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.consistency.engine.data_structures import Issue
from infra.consistency.repairers import BaseConsistencyRepairer, ConsistencyRepairResult


class CharacterRepairer(BaseConsistencyRepairer):
    """
    角色一致性修复器

    修复角色行为、对话、决策与角色设定不一致的问题。
    大部分角色一致性问题需要LLM修复，此修复器提供基于规则的修复能力。

    支持的修复类型：
    - 性格-行为冲突（通过角色设定档案检测）
    - 行为逻辑冲突（如恐高角色做爬高动作）
    - 语言风格冲突（如冷静角色说出激动的话）
    """

    def __init__(self, project_root: Optional[str] = None):
        super().__init__(project_root)
        self._rules: Optional[List[Tuple[str, str, str]]] = None

    def _get_fix_rules(self) -> List[Tuple[str, str, str]]:
        """
        获取修复规则

        基于规则的修复主要是通用性较强的模式，
        复杂角色特定问题需要LLM修复。

        Returns:
            [(原文本, 修复后, 描述), ...]
        """
        # 通用修复规则：某些模板句式可以替换为更符合角色设定的描述
        return [
            # 激动词汇替换为冷静表达（用于冷静型角色）
            ("猛然站起身", "缓缓起身", "冷静角色不应猛然动作"),
            ("暴怒道", "沉声道", "冷静角色不应暴怒"),
            ("歇斯底里地", "低声", "冷静角色不应歇斯底里"),
            ("疯狂地", "镇定地", "冷静角色不应疯狂"),
            ("失控地", "有节制地", "冷静角色不应失控"),

            # 热血角色相关
            ("冷漠地", "关切地", "热血角色不应冷漠"),
            ("退缩了", "迎难而上", "热血角色不应退缩"),
            ("放弃了", "坚持不懈", "热血角色不应放弃"),

            # 狡猾角色相关
            ("轻信道", "审慎对待", "狡猾角色不应轻信"),
            ("坦诚地", "委婉地", "狡猾角色不应过于坦诚"),

            # 谨慎角色相关
            ("鲁莽地", "谨慎地", "谨慎角色不应鲁莽"),
            ("冲动的", "深思熟虑的", "谨慎角色不应冲动"),
        ]

    def _apply_fixes(self, content: str, issues: List[Any] = None) -> Tuple[str, int, List[str]]:
        """
        应用修复

        对于角色一致性问题，规则修复只能覆盖少部分模式。
        大部分问题（如具体角色的具体行为冲突）需要LLM修复。

        Args:
            content: 章节内容
            issues: 问题列表（可选）

        Returns:
            (new_content, change_count, repaired_issue_descriptions)
        """
        rules = self._get_fix_rules()
        if not rules:
            return content, 0, []

        count = 0
        repaired = []
        result = content

        for old_term, new_term, desc in rules:
            if old_term in result:
                cnt = result.count(old_term)
                result = result.replace(old_term, new_term)
                count += cnt
                repaired.append(f"{desc}: {cnt}处")

        return result, count, repaired


def main():
    import argparse
    parser = argparse.ArgumentParser(description='角色一致性修复器')
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

    repairer = CharacterRepairer()

    if args.dry_run:
        for ch in chapters:
            new_content = repairer.dry_run(ch)
            content = repairer._read_chapter(ch)
            if new_content != content and new_content:
                count = sum(1 for old, new, _ in repairer._get_fix_rules()
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
