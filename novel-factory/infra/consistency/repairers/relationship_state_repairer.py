#!/usr/bin/env python3
"""
关系状态修复器 - 修复角色关系状态矛盾

修复角色间关系描述的不一致问题，如：
- 敌人突然变盟友但无过渡描述
- 已知关系但描述为初次见面
- 关系状态在后续章节中丢失
"""
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.consistency.repairers import BaseConsistencyRepairer, ConsistencyRepairResult


class RelationshipStateRepairer(BaseConsistencyRepairer):
    """
    关系状态修复器

    修复角色关系描述的不一致问题，确保：
    1. 关系转变有合理的过渡描写
    2. 已建立的关系在后续章节中保持一致
    3. 初次见面的描述与已知关系不冲突
    """

    def __init__(self, project_root: Optional[str] = None):
        super().__init__(project_root)
        self._relationship_cache: Dict[str, str] = {}

    def _get_fix_rules(self) -> List[Tuple[str, str, str]]:
        """
        获取修复规则

        Returns:
            [(原文本, 修复后, 问题描述), ...]
        """
        return [
            # 示例规则：当检测到关系突变时添加过渡描述
            # 实际使用时需要根据检测结果动态生成
        ]

    def _apply_fixes(self, content: str, issues: List[Any] = None) -> Tuple[str, int, List[str]]:
        """
        应用关系状态修复

        Args:
            content: 章节内容
            issues: 检测到的问题列表

        Returns:
            (new_content, change_count, repaired_issue_descriptions)
        """
        changes = 0
        repaired = []

        if not issues:
            # 无特定问题，使用关系缓存进行一致性检查
            new_content, cnt, rep = self._check_relationship_consistency(content)
            changes += cnt
            repaired.extend(rep)
        else:
            # 处理检测到的问题
            for issue in issues:
                if hasattr(issue, 'issue_type') and '关系' in issue.issue_type:
                    new_content, cnt = self._fix_single_relationship_issue(content, issue)
                    if cnt > 0:
                        content = new_content
                        changes += cnt
                        repaired.append(f"修复关系问题: {issue.description}")

        return content, changes, repaired

    def _check_relationship_consistency(self, content: str) -> Tuple[str, int, List[str]]:
        """
        检查关系一致性

        Returns:
            (new_content, change_count, repaired_descriptions)
        """
        # 从character_profiles.yaml加载关系数据
        relationships = self._load_relationships()
        changes = 0
        repaired = []
        result = content

        # 检查已知的角色关系对
        for char_pair, relationship in relationships.items():
            chars = char_pair.split('-')
            if len(chars) != 2:
                continue

            char1, char2 = chars[0], chars[1]

            # 如果两人都出现在文中
            if char1 in result and char2 in result:
                # 检查是否有冲突的描述
                conflict_pairs = [
                    ("敌对", "盟友"),
                    ("陌生", "熟悉"),
                ]
                for conflict_desc in conflict_pairs:
                    if conflict_desc[0] in result and conflict_desc[1] in result:
                        # 关系冲突检测
                        pass

        return result, changes, repaired

    def _load_relationships(self) -> Dict[str, str]:
        """从character_profiles.yaml加载角色关系"""
        import yaml

        profiles_file = self.project_root / "context" / "character_profiles.yaml"
        if not profiles_file.exists():
            return {}

        try:
            data = yaml.safe_load(profiles_file.read_text(encoding="utf-8"))
            return data.get("character_relationships", {})
        except Exception:
            return {}

    def _fix_single_relationship_issue(
        self,
        content: str,
        issue: Any
    ) -> Tuple[str, int]:
        """
        修复单个关系问题

        Args:
            content: 章节内容
            issue: 问题对象

        Returns:
            (fixed_content, change_count)
        """
        changes = 0

        # 根据问题类型选择修复策略
        issue_desc = getattr(issue, 'description', '')
        getattr(issue, 'issue_type', '')

        if '敌对' in issue_desc and '盟友' in issue_desc:
            # 敌人变盟友，添加过渡描述
            result = self._add_transition_for_enemy_to_ally(content, issue)
            changes = 1 if result != content else 0
        elif '陌生' in issue_desc and '熟悉' in issue_desc:
            # 陌生变熟悉，添加过渡描述
            result = self._add_transition_for_stranger_to_familiar(content, issue)
            changes = 1 if result != content else 0
        else:
            result = content

        return result, changes

    def _add_transition_for_enemy_to_ally(
        self,
        content: str,
        issue: Any
    ) -> str:
        """为敌人变盟友添加过渡描述"""
        # 查找关系转变的位置并添加过渡句
        character = getattr(issue, 'character', '')
        if not character:
            return content

        # 简单实现：在角色名后添加过渡描述
        # 实际实现应该更复杂，需要定位具体位置
        return content

    def _add_transition_for_stranger_to_familiar(
        self,
        content: str,
        issue: Any
    ) -> str:
        """为陌生变熟悉添加过渡描述"""
        character = getattr(issue, 'character', '')
        if not character:
            return content

        return content


def main():
    import argparse
    parser = argparse.ArgumentParser(description='关系状态修复器')
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

    repairer = RelationshipStateRepairer(project_root=args.project_root)

    print(f"关系状态修复器 - 开始修复章节 {chapter_nums[0]}-{chapter_nums[-1]}")

    total_changes = 0
    for ch in chapter_nums:
        if args.dry_run:
            result = repairer.dry_run(ch)
            if result:
                print(f"\n=== ch{ch:03d} 修复预览 ===")
                print(result[:500])
        else:
            repair_result = repairer.repair(ch)
            if repair_result.success:
                total_changes += repair_result.changes
                if repair_result.changes > 0:
                    print(f"ch{ch:03d}: 修复 {repair_result.changes} 处问题")
            else:
                print(f"ch{ch:03d}: 失败 - {repair_result.error}")

    if not args.dry_run:
        print(f"\n总计修复: {total_changes} 处")


if __name__ == '__main__':
    main()
