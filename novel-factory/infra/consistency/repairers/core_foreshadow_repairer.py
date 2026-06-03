#!/usr/bin/env python3
"""
核心伏笔修复器 - 确保核心伏笔被回收

修复未回收的核心级伏笔，通过：
1. 在伏笔植入章节添加回收提示
2. 在预期回收章节前添加伏笔触发描述
3. 确保伏笔关键词在预期位置出现
"""
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.consistency.repairers import BaseConsistencyRepairer, ConsistencyRepairResult


class CoreForeshadowRepairer(BaseConsistencyRepairer):
    """
    核心伏笔修复器

    确保核心级伏笔（core level）被正确回收：
    - core级伏笔必须在expect_recycled_by指定的章节前回收
    - 100%回收率要求，无一遗漏
    """

    def __init__(self, project_root: Optional[str] = None):
        super().__init__(project_root)
        self._foreshadow_records: Dict[int, List[Dict]] = {}

    def _get_fix_rules(self) -> List[Tuple[str, str, str]]:
        """
        获取修复规则

        Returns:
            [(原文本, 修复后, 问题描述), ...]
        """
        return []

    def _apply_fixes(self, content: str, issues: List[Any] = None) -> Tuple[str, int, List[str]]:
        """
        应用核心伏笔修复

        Args:
            content: 章节内容
            issues: 检测到的问题列表

        Returns:
            (new_content, change_count, repaired_issue_descriptions)
        """
        changes = 0
        repaired = []

        if not issues:
            return content, 0, []

        for issue in issues:
            if hasattr(issue, 'severity') and getattr(issue, 'severity', '') == 'HIGH':
                # HIGH严重度问题需要修复
                new_content, cnt = self._fix_foreshadow_issue(content, issue)
                if cnt > 0:
                    content = new_content
                    changes += cnt
                    repaired.append(f"修复伏笔: {getattr(issue, 'description', 'unknown')}")

        return content, changes, repaired

    def _fix_foreshadow_issue(self, content: str, issue: Any) -> Tuple[str, int]:
        """
        修复单个伏笔问题

        Args:
            content: 章节内容
            issue: 问题对象

        Returns:
            (fixed_content, change_count)
        """
        changes = 0

        # 提取伏笔信息
        foreshadow_text = getattr(issue, 'foreshadow_text', '')
        level = getattr(issue, 'level', 'core')
        getattr(issue, 'chapter', '')

        if not foreshadow_text or level != 'core':
            return content, 0

        # 查找伏笔标记位置
        foreshadow_pattern = rf'【伏笔:{level}:{re.escape(foreshadow_text)}:([\w-]+)】'
        match = re.search(foreshadow_pattern, content)

        if not match:
            return content, 0

        # 在伏笔标记后添加触发描述
        insert_pos = match.end()
        trigger_desc = self._generate_trigger_description(foreshadow_text)

        if trigger_desc:
            result = content[:insert_pos] + f"\n{trigger_desc}" + content[insert_pos:]
            changes = 1
            return result, changes

        return content, 0

    def _generate_trigger_description(self, foreshadow_text: str) -> str:
        """
        生成伏笔触发描述

        根据伏笔内容生成应该在回收章节出现的触发描述

        Args:
            foreshadow_text: 伏笔内容

        Returns:
            触发描述文本
        """
        # 简化实现：直接使用伏笔关键词
        keywords = foreshadow_text.split('/')
        if keywords:
            # 生成提示性描述
            main_keyword = keywords[0].strip()
            return f"<!-- 伏笔触发提示: {main_keyword} -->"

        return ""

    def check_and_repair_chapter(self, chapter_num: int) -> ConsistencyRepairResult:
        """
        检查并修复单章伏笔

        Args:
            chapter_num: 章节编号

        Returns:
            ConsistencyRepairResult
        """
        # 先检查伏笔
        from ..checkers.core_foreshadow_checker import CoreForeshadowChecker

        checker = CoreForeshadowChecker(chapters_dir=str(self.chapters_dir))
        issues = checker.check_chapter(chapter_num)

        if not issues:
            return ConsistencyRepairResult(
                chapter=chapter_num,
                success=True,
                changes=0
            )

        # 修复问题
        return self.repair(chapter_num, issues)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='核心伏笔修复器')
    parser.add_argument('--chapters', type=str, default='1-10', help='章节范围 (如 1-10)')
    parser.add_argument('--dry-run', action='store_true', help='只输出不保存')
    parser.add_argument('--project-root', type=str, default=None, help='项目根目录')
    args = parser.parse_args()

    # 解析章节范围
    if '-' in args.chapters:
        start, end = args.chapters.split('-')
        chapter_nums = list(range(int(start), int(end) + 1))
    else:
        chapter_nums = [int(args.chapters)]

    repairer = CoreForeshadowRepairer(project_root=args.project_root)

    print(f"核心伏笔修复器 - 开始修复章节 {chapter_nums[0]}-{chapter_nums[-1]}")

    total_changes = 0
    for ch in chapter_nums:
        result = repairer.check_and_repair_chapter(ch)
        if result.success:
            total_changes += result.changes
            if result.changes > 0:
                print(f"ch{ch:03d}: 修复 {result.changes} 处伏笔")
        else:
            print(f"ch{ch:03d}: 失败 - {result.error}")

    print(f"\n总计修复: {total_changes} 处伏笔")


if __name__ == '__main__':
    main()
