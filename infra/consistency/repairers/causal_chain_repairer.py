#!/usr/bin/env python3
"""
因果链修复器
修复原因结果不连贯的问题
"""

import re
import sys
from pathlib import Path
from typing import Any, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.consistency.engine.data_structures import Issue
from infra.consistency.repairers import BaseConsistencyRepairer, ConsistencyRepairResult


class CausalChainRepairer(BaseConsistencyRepairer):
    """
    因果链修复器

    修复原因结果不连贯的问题。
    因果链问题通常需要LLM理解上下文来修复，
    此修复器提供基于规则的修复能力。

    支持的修复类型：
    - 因果断裂（做了X但Y没发生相应改变）
    - 缺少必要结果（动作完成后缺少预期后果）
    - 状态矛盾（前文状态与当前描述矛盾）
    """

    def __init__(self, project_root: Optional[str] = None):
        super().__init__(project_root)
        self._rules: Optional[List[Tuple[str, str, str]]] = None

    def _get_fix_rules(self) -> List[Tuple[str, str, str]]:
        """
        获取修复规则

        因果链问题需要理解上下文，规则修复主要用于常见的模板问题。
        复杂的因果断裂需要LLM修复。

        Returns:
            [(原文本, 修复后, 描述), ...]
        """
        # 常见因果链修复模式
        return [
            # 添加必要的结果描述
            ("剑尖刺入", "剑尖刺入，剑身颤抖", "动作后应描述受力状态"),
            ("击中对手", "击中对手，对手后退数步", "攻击后应描述结果"),
            ("挡下攻击", "挡下攻击，火花四溅", "防御后应描述效果"),

            # 修复状态不连贯
            ("毫发无伤", "略有疲态", "战斗后不应毫发无伤"),
            ("若无其事地", "略微喘息地", "剧烈战斗后不应若无其事"),

            # 补充因果连接词
            ("因此", "因此（因果连接）", "使用因果连接词"),
            ("于是", "于是（因果连接）", "使用因果连接词"),
            ("导致", "导致（因果连接）", "使用因果连接词"),
        ]

    def _apply_fixes(self, content: str, issues: List[Any] = None) -> Tuple[str, int, List[str]]:
        """
        应用修复

        因果链问题大多数需要LLM理解上下文后修复。
        规则修复主要用于补充缺失的因果描述。

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
    parser = argparse.ArgumentParser(description='因果链修复器')
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

    repairer = CausalChainRepairer()

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
