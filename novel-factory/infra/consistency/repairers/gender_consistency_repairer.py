#!/usr/bin/env python3
"""
性别一致性修复器 - 修复性别引用错误

功能：
- 识别并修复文本中的性别引用错误
- 确保角色性别描述的一致性
- 修复代词和称谓的混用问题
"""
import sys
import re
from pathlib import Path
from typing import Tuple, List, Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.consistency.repairers import BaseConsistencyRepairer, ConsistencyRepairResult


class GenderConsistencyRepairer(BaseConsistencyRepairer):
    """性别一致性修复器 - 消除性别引用错误"""

    def __init__(self, project_root: Optional[str] = None):
        super().__init__(project_root)

    def _get_fix_rules(self):
        """获取性别一致性修复规则"""
        return [
            # 常见性别混淆 - 他/她
            ('她他', '他', '他她混淆'),
            ('他她', '她', '他她混淆'),
            # 动作性别不匹配
            ('她（', '她'),
            ('他（', '他'),
        ]

    def _apply_fixes(self, content: str, issues: List[Any] = None) -> Tuple[str, int, List[str]]:
        """
        应用性别一致性修复

        策略：
        1. 基于角色档案检测性别错误
        2. 修复代词混用问题
        3. 修复动作与性别不匹配
        """
        rules = self._get_fix_rules()
        count = 0
        repaired = []
        result = content

        # 应用基础规则修复
        for old_term, new_term, desc in rules:
            if old_term in result:
                cnt = result.count(old_term)
                result = result.replace(old_term, new_term)
                count += cnt
                repaired.append(f"{desc}: {cnt}处")

        # 加载角色档案进行高级修复
        result, additional_count, additional_repaired = self._fix_with_character_profiles(result)
        count += additional_count
        repaired.extend(additional_repaired)

        return result, count, repaired

    def _fix_with_character_profiles(self, content):
        """基于角色档案修复性别错误"""
        profiles_path = self.project_root / 'novel-factory' / 'context' / 'character_profiles.yaml'

        if not profiles_path.exists():
            return content, 0, []

        try:
            import yaml
            with open(profiles_path, 'r', encoding='utf-8') as f:
                profiles = yaml.safe_load(f)

            count = 0
            repaired = []
            result = content

            # 遍历角色档案，检测性别引用错误
            for char_name, char_data in profiles.items():
                gender = char_data.get('gender', '')
                if not gender:
                    continue

                # 检测该角色名在文本中的性别引用
                # 这是一个简化版本，完整实现需要更复杂的NLP
                name_patterns = [
                    f"她{char_name}",
                    f"他{char_name}",
                    f"{char_name}她",
                    f"{char_name}他",
                ]

                for pattern in name_patterns:
                    if pattern in result:
                        cnt = result.count(pattern)
                        # 修复性别混淆
                        if gender == 'male' and '她' in pattern:
                            result = result.replace(pattern, pattern.replace('她', '他'))
                            count += cnt
                        elif gender == 'female' and '他' in pattern:
                            result = result.replace(pattern, pattern.replace('他', '她'))
                            count += cnt

                if count > 0:
                    repaired.append(f"{char_name}性别修正: {count}处")

        except Exception:
            # 如果角色档案加载失败，静默返回
            return content, 0, []

        return result, count, repaired

    def _detect_gender_issues(self, content, character_profiles=None):
        """
        检测潜在的性别问题

        Returns:
            List of (position, issue_type, suggestion) tuples
        """
        issues = []

        # 检测他/她混淆
        confusion_patterns = [
            r'她他',
            r'他她',
        ]

        for pattern in confusion_patterns:
            for match in re.finditer(pattern, content):
                issues.append((
                    match.start(),
                    'gender_confusion',
                    f"发现 '{match.group()}' - 可能存在性别混淆"
                ))

        # 检测动作与性别不匹配
        # 这是一个简化实现
        return issues


def parse_chapters(chapters_str):
    """解析章节范围字符串"""
    chapters = []
    for part in chapters_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            chapters.extend(range(int(start), int(end) + 1))
        else:
            chapters.append(int(part))
    return chapters


def main():
    import argparse
    parser = argparse.ArgumentParser(description='性别一致性修复器 - 修复性别引用错误')
    parser.add_argument('--chapters', type=str, default='1-10', help='章节范围 (如: 1-10,15,20-25)')
    parser.add_argument('--dry-run', action='store_true', help='只输出不保存')
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    parser.add_argument('--check-only', action='store_true', help='仅检测问题，不修复')
    args = parser.parse_args()

    repairer = GenderConsistencyRepairer()

    if args.check_only:
        # 仅检测模式
        chapters = parse_chapters(args.chapters)
        for ch in chapters:
            content = repairer._read_chapter(ch)
            if not content:
                print(f"章节 {ch:03d}: 文件不存在")
                continue

            issues = repairer._detect_gender_issues(content)
            if issues:
                print(f"章节 {ch:03d}: 发现 {len(issues)} 个潜在问题")
                for pos, issue_type, suggestion in issues:
                    print(f"  - {issue_type}: {suggestion}")
            else:
                print(f"章节 {ch:03d}: 无明显问题")
        return

    chapters = parse_chapters(args.chapters)
    total_changes = 0

    for ch in chapters:
        result = repairer.repair(ch)

        if args.verbose:
            status = "✓" if result.success else "✗"
            print(f"章节 {ch:03d} [{status}] - 修复 {result.changes} 处")

        if result.success:
            total_changes += result.changes

            if args.dry_run:
                print(f"\n=== 章节 {ch:03d} 修复预览 ===")
                print(result.new_content[:500] + "..." if len(result.new_content) > 500 else result.new_content)

    print(f"\n总计: {total_changes} 处修复")
    if args.dry_run:
        print("(dry-run 模式，未保存)")


if __name__ == '__main__':
    main()