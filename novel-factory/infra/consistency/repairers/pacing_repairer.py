#!/usr/bin/env python3
"""
节奏修复器 - 修复节奏过快/过慢的问题

检测并修复:
- 节奏过快: 高潮过于密集, 缺少缓冲
- 节奏过慢: 铺垫过长, 信息密度低
- 节奏失衡: 章节内波动过大
"""
import re
import sys
from pathlib import Path
from typing import Any, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.consistency.repairers import BaseConsistencyRepairer, ConsistencyRepairResult


class PacingRepairer(BaseConsistencyRepairer):
    """节奏修复器 - 修复节奏过快/过慢的问题"""

    def __init__(self, project_root: Optional[str] = None):
        super().__init__(project_root)

    def _get_fix_rules(self) -> List[Tuple[str, str, str]]:
        """获取节奏修复规则"""
        return [
            # 节奏过快: 添加缓冲段落
            ("，然后", "，随后进行短暂的休整，", "添加缓冲"),
            ("紧接着", "紧接着，众人稍作休整后", "添加缓冲"),
            # 节奏过慢: 精简铺垫
            ("经过漫长的等待，终于", "不久后", "精简铺垫"),
            ("过了很久很久", "不久后", "精简铺垫"),
        ]

    def _apply_fixes(self, content: str, issues: List[Any] = None) -> Tuple[str, int, List[str]]:
        """
        应用节奏修复

        Returns:
            (new_content, change_count, repaired_issue_descriptions)
        """
        if issues is None:
            issues = []

        count = 0
        repaired = []
        result = content

        # 规则1: 处理突兀的连续动作（节奏过快）
        # 检测连续短句模式（如："他出手。他击中。他倒下。"）
        short_sentence_pattern = re.compile(r'([^。！？]{1,15}[。！？]){3,}')
        matches = short_sentence_pattern.finditer(result)
        for match in matches:
            old_text = match.group()
            if len(old_text) < 50:  # 确实是连续短句
                # 在第二个短句后添加过渡
                new_text = old_text.replace(
                    old_text.split('。')[0] + '。',
                    old_text.split('。')[0] + '。众人心头一紧，',
                    1
                )
                if new_text != old_text:
                    result = result.replace(old_text, new_text, 1)
                    count += 1
                    repaired.append("节奏过快: 添加过渡")

        # 规则2: 处理过长铺垫（节奏过慢）
        long_setup_pattern = re.compile(
            r'(他静静地站在那里|他慢慢地走着|他沉默了很久|时间一分一秒过去)'
        )
        for match in long_setup_pattern.finditer(result):
            old_text = match.group()
            new_text = old_text.replace('静静地', '').replace('慢慢地', '').replace('了很久', '')
            if new_text != old_text:
                result = result.replace(old_text, new_text, 1)
                count += 1
                repaired.append("节奏过慢: 精简铺垫")

        # 规则3: 应用通用修复规则
        rules = self._get_fix_rules()
        for old_term, new_term, desc in rules:
            if old_term in result:
                cnt = result.count(old_term)
                result = result.replace(old_term, new_term)
                count += cnt
                repaired.append(f"{desc}: {cnt}处")

        # 规则4: 检测并修复高潮后突然结束
        re.compile(r'([^。]+。)($|\n\n)', re.MULTILINE)
        # 在高潮句后添加短暂过渡
        fixed, c, r = self._fix_climax_ending(result)
        result = fixed
        count += c
        repaired.extend(r)

        return result, count, repaired

    def _fix_climax_ending(self, content: str) -> Tuple[str, int, List[str]]:
        """修复高潮后突然结束的问题"""
        count = 0
        repaired = []
        lines = content.split('\n')
        result_lines = []

        for i, line in enumerate(lines):
            result_lines.append(line)
            # 检测高潮句（以感叹号结尾且长度适中）
            if line.strip().endswith('！') and 5 < len(line.strip()) < 30:
                if i + 1 < len(lines) and lines[i + 1].strip() and not lines[i + 1].strip().startswith('"'):
                    # 检查下一行是否是新的高潮或普通叙述
                    if not lines[i + 1].strip().endswith('！'):
                        # 在高潮后添加短暂过渡
                        result_lines.append('一阵短暂的寂静笼罩四周。')

        return '\n'.join(result_lines), count, repaired


def main():
    import argparse
    parser = argparse.ArgumentParser(description='节奏修复器 - 修复节奏过快/过慢的问题')
    parser.add_argument('--chapters', type=str, default='1-10', help='章节范围 (如 1-10 或 5,8,12)')
    parser.add_argument('--dry-run', action='store_true', help='只输出不保存')
    args = parser.parse_args()

    # 解析章节范围
    chapter_nums = []
    if '-' in args.chapters:
        start, end = args.chapters.split('-')
        chapter_nums = list(range(int(start), int(end) + 1))
    elif ',' in args.chapters:
        chapter_nums = [int(x) for x in args.chapters.split(',')]
    else:
        chapter_nums = [int(args.chapters)]

    repairer = PacingRepairer()
    total_changes = 0

    for ch in chapter_nums:
        print(f"处理章节 {ch:03d}...", end=" ")
        result = repairer.dry_run(ch) if args.dry_run else repairer.repair(ch)

        if result.success:
            print(f"修复 {result.changes} 处")
            total_changes += result.changes
        else:
            print(f"跳过 ({result.error})")

    print(f"\n总计修复: {total_changes} 处")


if __name__ == '__main__':
    main()
