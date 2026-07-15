#!/usr/bin/env python3
"""
世界观一致性检测器
检测科幻术语是否已替换为修真术语
"""

import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.quality import Inspector, Issue

# 科幻术语列表（用于检测未替换的术语）
SCIFI_TERMS = [
    "核废土", "辐射区", "辐射污染", "放射性污染", "核辐射",
    "核武器", "核弹", "核爆", "核爆炸", "核打击",
    "基因变异", "基因突变", "变异生物", "变异兽",
    "能量护盾", "激光武器", "激光", "等离子", "导弹",
    "飞船", "战舰", "航空母舰", "飞机",
    "人工智能", "量子", "纳米", "电子设备",
    "全息投影", "全息", "通讯信号",
    "基因治疗", "纳米医疗", "医疗舱",
    "防护服", "太空服", "作战服",
    "雷达扫描", "生命探测仪", "热成像",
    "核动力", "能量核心", "电池",
]


class WorldviewChecker(Inspector):
    """
    世界观一致性检测器

    检测章节中是否包含未替换的科幻术语
    """

    dimension = "世界观一致性"
    issue_type = "科幻术语残留"

    def check(self, chapter_num: int) -> List[Issue]:
        """
        检测单个章节的世界观一致性

        Args:
            chapter_num: 章节编号

        Returns:
            发现的问题列表
        """
        content = self.read_chapter(chapter_num)
        if not content:
            return []

        issues = []
        for term in SCIFI_TERMS:
            if term in content:
                count = content.count(term)
                issues.append(Issue(
                    chapter=chapter_num,
                    dimension=self.dimension,
                    issue_type=self.issue_type,
                    severity="P1",
                    description=f"发现{count}处未替换的科幻术语: {term}",
                    location=f"全文约{count}处",
                    evidence=f"术语 '{term}' 应替换为修真术语",
                    suggestion="使用 worldview_repairer.py 进行替换"
                ))

        return issues


def main():
    import argparse
    parser = argparse.ArgumentParser(description='世界观一致性检测')
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

    checker = WorldviewChecker()
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
