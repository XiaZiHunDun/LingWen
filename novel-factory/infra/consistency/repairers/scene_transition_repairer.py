#!/usr/bin/env python3
"""
场景转换修复器 - 修复突兀的场景跳跃

检测并修复:
- 时间跳跃: 瞬间切换时间点缺少过渡
- 空间跳跃: 突然切换地点缺少说明
- 视角跳跃: 视角切换过于突兀
"""
import sys
import re
from pathlib import Path
from typing import List, Tuple, Any

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.consistency.repairers import BaseConsistencyRepairer, ConsistencyRepairResult


class SceneTransitionRepairer(BaseConsistencyRepairer):
    """场景转换修复器 - 修复突兀的场景跳跃"""

    # 时间词模式
    TIME_TRANSITIONS = [
        '几分钟后', '片刻之后', '一段时间后', '转眼间',
        '突然', '就在这时', '下一秒', '紧接着',
        '几天后', '数日后', '一周后', '一个月后',
    ]

    # 空间词模式
    SPACE_TRANSITIONS = [
        '与此同时', '另一边', '在同一时刻',
        '画面一转', '场景切换', '镜头一转',
        '与此同时，', '与此同时的',
    ]

    def __init__(self, project_root=None):
        super().__init__(project_root)

    def _get_fix_rules(self) -> List[Tuple[str, str, str]]:
        """获取场景转换修复规则"""
        return [
            # 突兀的时间跳跃
            ("瞬间", "片刻之后", "时间过渡"),
            ("下一刻", "片刻之后", "时间过渡"),
            ("下一秒", "紧接着", "时间过渡"),
            # 突兀的空间跳跃
            ("他消失在原地", "他身影一闪，消失在原地", "空间过渡"),
            ("出现在", "众人只见他身影一闪，出现在", "空间过渡"),
        ]

    def _apply_fixes(self, content: str, issues: List[Any] = None) -> Tuple[str, int, List[str]]:
        """
        应用场景转换修复

        Returns:
            (new_content, change_count, repaired_issue_descriptions)
        """
        if issues is None:
            issues = []

        count = 0
        repaired = []
        result = content

        # 规则1: 检测并修复突兀的时间跳跃
        fixed, c, r = self._fix_abrupt_time_jump(result)
        result = fixed
        count += c
        repaired.extend(r)

        # 规则2: 检测并修复突兀的空间跳跃
        fixed, c, r = self._fix_abrupt_space_jump(result)
        result = fixed
        count += c
        repaired.extend(r)

        # 规则3: 检测并修复视角突然切换
        fixed, c, r = self._fix_abrupt_pov_switch(result)
        result = fixed
        count += c
        repaired.extend(r)

        # 规则4: 应用通用修复规则
        rules = self._get_fix_rules()
        for old_term, new_term, desc in rules:
            if old_term in result:
                cnt = result.count(old_term)
                result = result.replace(old_term, new_term)
                count += cnt
                repaired.append(f"{desc}: {cnt}处")

        return result, count, repaired

    def _fix_abrupt_time_jump(self, content: str) -> Tuple[str, int, List[str]]:
        """修复突兀的时间跳跃"""
        count = 0
        repaired = []
        lines = content.split('\n')
        result_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]
            result_lines.append(line)

            # 检测突兀的时间跳跃（单独一行时间词，前面没有过渡）
            stripped = line.strip()
            is_time_transition = any(stripped.startswith(t) for t in self.TIME_TRANSITIONS)

            if is_time_transition and i > 0:
                prev_line = lines[i - 1].strip()
                # 检查前一行是否也是时间词或动作句
                if prev_line and not any(prev_line.startswith(t) for t in self.TIME_TRANSITIONS):
                    if not prev_line.endswith('。') and not prev_line.endswith('：'):
                        # 在时间词前添加过渡词
                        result_lines[-1] = f"片刻后，{line}"
                        count += 1
                        repaired.append("突兀时间跳跃: 添加过渡")

            i += 1

        return '\n'.join(result_lines), count, repaired

    def _fix_abrupt_space_jump(self, content: str) -> Tuple[str, int, List[str]]:
        """修复突兀的空间跳跃"""
        count = 0
        repaired = []
        lines = content.split('\n')
        result_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]
            result_lines.append(line)

            stripped = line.strip()
            is_space_transition = any(stripped.startswith(t) for t in self.SPACE_TRANSITIONS)

            if is_space_transition and i > 0:
                prev_line = lines[i - 1].strip()
                # 检查前一行是否是动作句（可能表示场景切换）
                if prev_line and (prev_line.endswith('。') or prev_line.endswith('！')):
                    # 检测是否在同一段落内且有对话
                    if i >= 2 and '"' in lines[i - 1]:
                        # 添加场景说明
                        result_lines[-1] = f"与此同时，\n{line}"
                        count += 1
                        repaired.append("突兀空间跳跃: 添加过渡")

            i += 1

        return '\n'.join(result_lines), count, repaired

    def _fix_abrupt_pov_switch(self, content: str) -> Tuple[str, int, List[str]]:
        """修复视角突然切换"""
        count = 0
        repaired = []
        result = content

        # 检测连续两段无过渡的视角切换
        # 例如: 第一段描写A, 第二段突然描写B, 中间没有过渡
        paragraphs = result.split('\n\n')

        if len(paragraphs) >= 2:
            fixed_paragraphs = []
            i = 0
            while i < len(paragraphs):
                p = paragraphs[i].strip()
                fixed_paragraphs.append(p)

                if i > 0 and p:
                    prev_p = paragraphs[i - 1].strip()
                    # 检测两人称切换（他→你或我）
                    if self._has_pov_switch(prev_p, p):
                        # 在段落间添加过渡句
                        fixed_paragraphs.append('视角切换过渡句占位')
                        count += 1
                        repaired.append("视角跳跃: 添加过渡")

                i += 1

            # 移除占位符，替换为实际的过渡
            final_result = '\n\n'.join(fixed_paragraphs)

            # 简化: 用自然的过渡句替换
            transition_marker = '视角切换过渡句占位'
            while transition_marker in final_result:
                final_result = final_result.replace(
                    transition_marker,
                    '与此同时，场上的局势发生了微妙的变化。',
                    1
                )

            return final_result, count, repaired

        return result, 0, []

    def _has_pov_switch(self, paragraph1: str, paragraph2: str) -> bool:
        """检测两个段落间是否有视角切换"""
        # 检测第一人称到第三人称的切换
        first_person = ['我', '我的', '我们', '我们的']
        third_person = ['他', '他的', '她', '她的', '他们', '她们的']

        p1_has_first = any(f in paragraph1 for f in first_person)
        p1_has_third = any(f in paragraph1 for f in third_person)
        p2_has_first = any(f in paragraph2 for f in first_person)
        p2_has_third = any(f in paragraph2 for f in third_person)

        # 从第一人称切换到第三人称
        if p1_has_first and p2_has_third and not p1_has_third:
            return True
        # 从第三人称切换到第一人称
        if p1_has_third and p2_has_first and not p2_has_third:
            return True

        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description='场景转换修复器 - 修复突兀的场景跳跃')
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

    repairer = SceneTransitionRepairer()
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