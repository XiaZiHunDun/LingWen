#!/usr/bin/env python3
"""
对话真实性修复器 - 修复AI感对话

功能：
- 识别并修复过于规范化、模板化的对话
- 增强对话的自然感和人物特色
- 去除AI生成的"完美对话"痕迹
"""
import sys
import re
from pathlib import Path
from typing import Tuple, List, Any

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.consistency.repairers import BaseConsistencyRepairer, ConsistencyRepairResult


class DialogueAuthenticityRepairer(BaseConsistencyRepairer):
    """对话真实性修复器 - 消除AI感对话"""

    def __init__(self, project_root=None):
        super().__init__(project_root)

    def _get_fix_rules(self):
        """获取对话修复规则"""
        return [
            # AI模板句式 - 过于规整的开场白
            ('"是的，"', '"嗯"', '规整确认句式'),
            ('"当然，"', '"那倒是"', '规整同意句式'),
            ('"我明白了，"', '"哦懂了"', '规整理解句式'),
            ('"确实，"', '"可不是嘛"', '规整肯定句式'),
            ('"没错，"', '"对，是这样"', '规整肯定句式'),

            # 过于完美的回应
            ('"你说得对，"', '"嗯"', '完美认同句式'),
            ('"你说得有道理，"', '"好吧"', '完美接受句式'),
            ('"我完全同意，"', '"行吧"', '完美同意句式'),
            ('"正如你所说，"', '"是呗"', '完美附和句式'),

            # 过渡句式 - 过于规范
            ('"说到这里，"', '"对了"', '规范过渡句'),
            ('"顺便说一下，"', '"哎说起来"', '规范插入句'),
            ('"更重要的是，"', '"而且"', '规范强调句'),
            ('"事实上，"', '"其实"', '规范陈述句'),
            ('"总的来说，"', '"反正"', '规范总结句'),

            # 解释句式 - 过于学术
            ('"换句话说，"', '"就是说"', '学术解释句'),
            ('"也就是说，"', '"这么来讲"', '学术解释句'),
            ('"从某种意义上说，"', '"说白了"', '学术限定句'),
            ('"严格来说，"', '"讲真"', '学术限定句'),

            # 情感表达 - 过于工整
            ('"我感到非常', '我挺', '过度情感句'),
            ('"我深深地', '我', '过度情感句'),
            ('"我不禁', '我', '过度情感句'),
            ('"不由自主地', '', '过度副词'),

            # 问句 - 过于规范
            ('"请问', '"', '规范问句前缀'),
            ('"能否告诉我', '"说真的', '规范请求句'),
            ('"你是否可以', '"你能', '规范请求句'),
            ('"我是否可以', '"我', '规范请求句'),

            # 引号中的规整表达
            ('"没错，"', '"对"', '规整肯定'),
            ('"确实如此，"', '"是这么回事"', '规整确认'),
        ]

    def _apply_fixes(self, content: str, issues: List[Any] = None) -> Tuple[str, int, List[str]]:
        """
        应用对话真实性修复

        策略：
        1. 替换AI模板句式为更口语化的表达
        2. 修复过于规整的对话标签
        3. 添加自然的口语化表达
        4. 消除"完美对话"痕迹
        """
        rules = self._get_fix_rules()
        count = 0
        repaired = []
        result = content

        # 应用规则修复
        for old_term, new_term, desc in rules:
            if old_term in result:
                cnt = result.count(old_term)
                result = result.replace(old_term, new_term)
                count += cnt
                repaired.append(f"{desc}: {cnt}处")

        # 额外修复：去除多余的解释性语句
        result = self._fix_excessive_explanations(result)

        # 额外修复：修复问句中的AI感
        result = self._fix_ai_question_patterns(result)

        return result, count, repaired

    def _fix_excessive_explanations(self, content):
        """修复过于冗长的解释性对话"""
        patterns = [
            # 过长解释 + 引用组合
            (r'(\s)"我来解释一下，[^"]+"\s*', r'\1'),
            (r'(\s)"让我说明一下，[^"]+"\s*', r'\1'),
            (r'(\s)"简单来说，[^"]+"\s*', r'\1'),
            (r'(\s)"实际上，[^"]+"\s*', r'\1'),
        ]

        result = content
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result)

        return result

    def _fix_ai_question_patterns(self, content):
        """修复AI风格的问句"""
        patterns = [
            # 连续小问题（AI喜欢拆解问题）
            (r'\?"\s*\?"', '?"'),
            # 过度礼貌的问句
            (r'"请问您能', '"你能'),
            (r'"您能否', '"你能不能'),
            (r'"我想请教一下', '"问个事'),
        ]

        result = content
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result)

        return result


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
    parser = argparse.ArgumentParser(description='对话真实性修复器 - 修复AI感对话')
    parser.add_argument('--chapters', type=str, default='1-10', help='章节范围 (如: 1-10,15,20-25)')
    parser.add_argument('--dry-run', action='store_true', help='只输出不保存')
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    args = parser.parse_args()

    repairer = DialogueAuthenticityRepairer()

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