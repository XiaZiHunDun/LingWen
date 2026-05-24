#!/usr/bin/env python3
"""
AI痕迹检测器
检测小说中的AI模板句式
"""

import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.quality import Inspector, Issue


# AI痕迹模式列表
AI_TRACE_PATTERNS = [
    "首先", "其次", "最后",
    "那一刻", "突然", "霎时", "刹那",
    "可以看出", "值得注意的是", "实际上", "显然", "明显地", "显而易见",
    "因此", "所以", "由于",
    "于是乎", "紧接着",
    "不断地", "持续地",
    "他感到一阵", "她感到一阵",
]


class AITraceChecker(Inspector):
    """
    AI痕迹检测器

    检测章节中的AI模板句式
    """

    dimension = "文笔风格"
    issue_type = "AI模板句式"

    def check(self, chapter_num: int) -> List[Issue]:
        """
        检测单个章节的AI痕迹

        Args:
            chapter_num: 章节编号

        Returns:
            发现的问题列表
        """
        content = self.read_chapter(chapter_num)
        if not content:
            return []

        issues = []
        for pattern in AI_TRACE_PATTERNS:
            if pattern in content:
                count = content.count(pattern)
                issues.append(Issue(
                    chapter=chapter_num,
                    dimension=self.dimension,
                    issue_type=self.issue_type,
                    severity="P2",
                    description=f"发现{count}处AI模板句式: {pattern}",
                    location=f"全文约{count}处",
                    evidence=f"句式 '{pattern}' 为AI常用模板",
                    suggestion=f"使用 ai_trace_repairer.py 进行替换或删除"
                ))

        return issues


def main():
    import argparse
    parser = argparse.ArgumentParser(description='AI痕迹检测')
    parser.add_argument('--chapters', type=str, default='1-10',
                        help='章节范围')
    parser.add_argument('--limit', type=int, default=None,
                        help='限制检测章节数量')

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

    checker = AITraceChecker()
    all_issues = checker.check_batch(chapters)

    print(f"检测章节: {len(chapters)} 个")
    print(f"发现问题: {len(all_issues)} 个")
    print("-" * 50)

    # 按章节分组显示
    current_ch = 0
    for issue in all_issues:
        if issue.chapter != current_ch:
            print(f"\nch{issue.chapter:03d}:")
            current_ch = issue.chapter
        print(f"  [{issue.severity}] {issue.description}")


if __name__ == '__main__':
    main()