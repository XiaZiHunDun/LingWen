#!/usr/bin/env python3
"""
句式多样性检测器
检测章节句式重复度过高的问题
评分标准：
- 优秀: 句式种类≥10种，且无单一句式超过20%
- 合格: 句式种类≥6种
- 触发重写: 句式种类<6种 或 某句式占比>40%
"""
import re
import math
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

@dataclass
class DiversityIssue:
    chapter: str
    score: float
    severity: str
    description: str

class SentenceDiversityChecker:
    """
    句式多样性检测器
    使用Shannon多样性指数计算句式分布
    """

    # 句式模式定义
    DIVERSE_PATTERNS = [
        (r'「[^」]+」', 'dialog'),           # 对话
        (r'他[^，,。！？]+[，,。！？]', 'narrator_he'),  # 他述句
        (r'她[^，,。！？]+[，,。！？]', 'narrator_she'),  # 她述句
        (r'突然[^，,。！？]+', 'abrupt'),     # 副词开头
        (r'然而[^，,。！？]+', 'however'),     # 转折句
        (r'只见[^，,。！？]+', 'observe'),     # 观察句
        (r'随着[^，,。！？]+', 'temporal'),    # 时间句
        (r'若是[^，,。！？]+', 'conditional'), # 条件句
        (r'因此[^，,。！？]+', 'conclusion'),  # 结论句
        (r'但是[^，,。！？]+', 'but'),         # 转折句2
    ]

    # 评分阈值
    THRESHOLDS = {
        'excellent': 3.5,   # >= 3.5 为优秀
        'pass': 2.5,        # >= 2.5 为合格
        'fail': 2.5         # < 2.5 触发重写
    }

    def __init__(self, chapters_dir: Optional[str] = None):
        if chapters_dir is None:
            project_root = Path(__file__).parent.parent.parent
            chapters_dir = project_root / '03_内容仓库' / '04_正文'
        self.chapters_dir = Path(chapters_dir)

    def score_chapter(self, chapter_num: int) -> tuple[float, dict]:
        """计算单章句式多样性评分，返回(分数, 分布字典)"""
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        if not ch_file.exists():
            return 0.0, {}

        content = ch_file.read_text(encoding='utf-8')

        # 统计各句式出现次数
        distribution = {}
        total_matches = 0

        for pattern, name in self.DIVERSE_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                distribution[name] = len(matches)
                total_matches += len(matches)

        # 统计总句数（以句号、感叹号、问号结尾）
        total_sentences = len(re.findall(r'[。！？]', content))
        if total_sentences == 0:
            return 0.0, distribution

        # 计算Shannon多样性指数
        diversity_index = 0.0
        for count in distribution.values():
            p = count / total_sentences
            if p > 0:
                diversity_index -= p * math.log2(p)

        # 也考虑未被pattern覆盖的句子
        uncovered = total_sentences - total_matches
        if uncovered > 0:
            p_uncovered = uncovered / total_sentences
            diversity_index -= p_uncovered * math.log2(p_uncovered) if p_uncovered > 0 else 0

        return round(diversity_index, 2), distribution

    def check_chapter(self, chapter_num: int) -> Optional[DiversityIssue]:
        """检查单章，如果不合格返回Issue"""
        score, distribution = self.score_chapter(chapter_num)

        if score < self.THRESHOLDS['fail']:
            # 检查是否有某句式占比过高
            ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
            content = ch_file.read_text(encoding='utf-8') if ch_file.exists() else ''
            total_sentences = len(re.findall(r'[。！？]', content))

            dominant_pct = 0
            if total_sentences > 0:
                for name, count in distribution.items():
                    pct = count / total_sentences
                    if pct > dominant_pct:
                        dominant_pct = pct

            severity = 'HIGH' if score < 2.0 else 'MEDIUM'
            description = f"句式多样性评分{score:.2f}，低于阈值{self.THRESHOLDS['fail']}"
            if dominant_pct > 0.4:
                description += f"（某句式占比{dominant_pct*100:.0f}%超过40%）"

            return DiversityIssue(
                chapter=f'ch{chapter_num:03d}',
                score=score,
                severity=severity,
                description=description
            )

        return None

    def check_all(self, limit: Optional[int] = None) -> List[DiversityIssue]:
        """检查所有章节"""
        issues = []
        chapter_files = sorted(self.chapters_dir.glob('ch*.md'))

        if limit:
            chapter_files = chapter_files[:limit]

        for ch_file in chapter_files:
            match = re.match(r'ch(\d+)\.md', ch_file.name)
            if match:
                ch_num = int(match.group(1))
                issue = self.check_chapter(ch_num)
                if issue:
                    issues.append(issue)

        return issues

    def generate_report(self, issues: list[DiversityIssue]) -> str:
        """生成检查报告"""
        if not issues:
            return "✅ 句式多样性检查通过：所有章节评分合格"

        high_issues = [i for i in issues if i.severity == 'HIGH']
        medium_issues = [i for i in issues if i.severity == 'MEDIUM']

        report = ["# 句式多样性检查报告\n"]
        report.append(f"## 汇总\n")
        report.append(f"- HIGH级问题: {len(high_issues)}章节")
        report.append(f"- MEDIUM级问题: {len(medium_issues)}章节\n")

        if high_issues:
            report.append("## 🔴 需重写\n")
            for issue in sorted(high_issues, key=lambda x: x.score):
                report.append(f"- [{issue.chapter}] {issue.description}")

        if medium_issues:
            report.append("\n## ⚠️  建议优化\n")
            for issue in sorted(medium_issues, key=lambda x: x.score)[:10]:
                report.append(f"- [{issue.chapter}] {issue.description}")

        return "\n".join(report)

def main():
    import sys
    import json

    checker = SentenceDiversityChecker()

    # 支持 --limit 参数
    limit = None
    if len(sys.argv) > 1 and sys.argv[1] == '--limit':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    issues = checker.check_all(limit=limit)

    if issues:
        print(checker.generate_report(issues))
        high_count = len([i for i in issues if i.severity == 'HIGH'])
        print(f"\n总计: {len(issues)}章节有问题（{high_count} HIGH）")
        sys.exit(1) if high_count > 0 else sys.exit(0)
    else:
        print("✅ 句式多样性检查通过：所有章节评分合格")
        sys.exit(0)

if __name__ == '__main__':
    main()