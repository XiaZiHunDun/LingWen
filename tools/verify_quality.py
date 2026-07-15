#!/usr/bin/env python3
"""
质量验证工具 - v9.1
基于Inspector框架的质量验证

使用方式:
    python verify_quality.py --chapters 1-30
    python verify_quality.py --chapters 1-360 --output report.json
"""

import json
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.paths import ProjectPaths
from infra.quality import AITraceChecker, WorldviewChecker


class QualityVerifier:
    """质量验证器"""

    def __init__(self, paths: ProjectPaths = None):
        self.paths = paths or ProjectPaths.get()
        self.worldview_checker = WorldviewChecker(self.paths)
        self.ai_trace_checker = AITraceChecker(self.paths)

    def verify_chapters(self, chapter_nums: List[int]) -> Dict[str, Any]:
        """
        验证指定章节的质量

        Returns:
            验证结果字典
        """
        worldview_issues = []
        ai_trace_issues = []

        for ch in chapter_nums:
            worldview_issues.extend(self.worldview_checker.check(ch))
            ai_trace_issues.extend(self.ai_trace_checker.check(ch))

        return {
            "chapters_checked": len(chapter_nums),
            "worldview": {
                "total_issues": len(worldview_issues),
                "issues": [{"ch": i.chapter, "desc": i.description} for i in worldview_issues]
            },
            "ai_trace": {
                "total_issues": len(ai_trace_issues),
                "issues": [{"ch": i.chapter, "desc": i.description} for i in ai_trace_issues]
            }
        }

    def verify_sample(self, sample_size: int = 30, seed: int = 42) -> Dict[str, Any]:
        """
        随机抽样验证

        Args:
            sample_size: 抽样数量
            seed: 随机种子

        Returns:
            验证结果字典
        """
        random.seed(seed)
        all_chapters = list(range(1, 361))
        sample_chapters = sorted(random.sample(all_chapters, sample_size))

        return self.verify_chapters(sample_chapters)

    def generate_report(self, result: Dict[str, Any]) -> str:
        """生成文本报告"""
        lines = [
            "=" * 60,
            "质量验证报告",
            f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            f"检测章节数: {result['chapters_checked']}",
            "",
            "【世界观一致性】",
            f"  违规总数: {result['worldview']['total_issues']}",
            f"  涉及章节: {len(set(i['ch'] for i in result['worldview']['issues']))}",
            "",
            "【AI痕迹】",
            f"  AI痕迹总数: {result['ai_trace']['total_issues']}",
            f"  涉及章节: {len(set(i['ch'] for i in result['ai_trace']['issues']))}",
        ]

        # 显示前10个问题
        if result['worldview']['issues']:
            lines.append("")
            lines.append("【世界观问题示例】")
            for i in result['worldview']['issues'][:10]:
                lines.append(f"  ch{i['ch']:03d}: {i['desc']}")

        if result['ai_trace']['issues']:
            lines.append("")
            lines.append("【AI痕迹问题示例】")
            for i in result['ai_trace']['issues'][:10]:
                lines.append(f"  ch{i['ch']:03d}: {i['desc']}")

        return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='质量验证工具')
    parser.add_argument('--chapters', type=str, default='1-30',
                        help='章节范围，如 "1-30" 或 "1,5,10"')
    parser.add_argument('--sample', action='store_true',
                        help='随机抽样模式')
    parser.add_argument('--sample-size', type=int, default=30,
                        help='抽样数量')
    parser.add_argument('--output', type=str, default=None,
                        help='输出JSON文件路径')
    parser.add_argument('--limit', type=int, default=None,
                        help='限制处理章节数量')

    args = parser.parse_args()

    # 解析章节范围
    if args.sample:
        verifier = QualityVerifier()
        result = verifier.verify_sample(sample_size=args.sample_size)
        print(verifier.generate_report(result))
    else:
        chapters = []
        for part in args.chapters.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                chapters.extend(range(start, end + 1))
            else:
                chapters.append(int(part))

        if args.limit:
            chapters = chapters[:args.limit]

        verifier = QualityVerifier()
        result = verifier.verify_chapters(chapters)

        print(verifier.generate_report(result))

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n结果已保存: {output_path}")


if __name__ == '__main__':
    main()
