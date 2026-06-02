#!/usr/bin/env python3
"""
叙事视角检测器
检测视角跳脱问题，严格锁定林夜视角
基于评审2/3/4建议：
- 删除"与此同时，在废土的另一处……"等跳脱
- 莫言内心通过林夜观察呈现，而非直接呈现
- 严格锁定第三人称限知（林夜视角）
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from infra.consistency.engine.data_structures import Issue, IssueLocation, CheckerType, IssueSeverity
from .base_checker import BaseChecker


@dataclass
class PerspectiveIssue:
    """视角问题"""
    chapter: int
    issue_type: str  # 'viewpoint_shift' | 'omniscient' | 'other_char_inner'
    description: str
    line_match: str
    severity: str = "MEDIUM"


class NarrativePerspectiveChecker(BaseChecker):
    """
    叙事视角检测器
    检测破坏林夜限知视角的段落
    """
    _checker_type = CheckerType.NARRATIVE_PERSPECTIVE


    # 视角跳脱模式
    VIEWPOINT_SHIFT_PATTERNS = [
        # === 镜头切换类（评审一致指出）===
        (r'与此同时[，\s][^\n。！？]{0,20}[。！？]?', 'viewpoint_shift', '与此同时',
         '删除或改为：镜头跟随林夜所见'),
        (r'视线转向[^\n。！？]{0,30}[。！？]?', 'viewpoint_shift', '视线转向',
         '删除，改为林夜视角的直接观察'),
        (r'与此同时[，\s][在从]?[^\n。！？]{0,20}(?:另一|别的|其他)[^\n。！？]{0,30}[。！？]?', 'viewpoint_shift', '镜头切换另一处',
         '改为跟随林夜的行动'),
        (r'镜头[拉远切换转到转向]?[^\n。！？]{0,20}[。！？]?', 'viewpoint_shift', '镜头术语',
         '删除电影术语，保持小说视角'),
        (r'视角[切换转回到]?[^\n。！？]{0,20}[。！？]?', 'viewpoint_shift', '视角术语',
         '删除，用叙事手法而非技术术语'),

        # === 其他角色内心直接呈现（评审2/3指出）===
        (r'莫言没有走远[^\n。！？]{0,20}[。！？]?', 'other_char_inner', '莫言位置切换',
         '通过林夜观察莫言行为，而非直接告知'),
        (r'莫言[的]?(?:内心|心理|想法)[^\n。！？]{0,20}[。！？]?', 'other_char_inner', '莫言内心直接呈现',
         '删除莫言内心描写，通过林夜观察推断'),
        (r'苏琳[的]?(?:内心|心理|想法)[^\n。！？]{0,20}[。！？]?', 'other_char_inner', '苏琳内心直接呈现',
         '删除苏琳内心描写，通过林夜观察推断'),
        (r'星月[的]?(?:内心|心理|想法)[^\n。！？]{0,20}[。！？]?', 'other_char_inner', '星月内心直接呈现',
         '删除星月内心描写，通过林夜观察推断'),
        (r'铁蛋[的]?(?:内心|心理|想法)[^\n。！？]{0,20}[。！？]?', 'other_char_inner', '铁蛋内心直接呈现',
         '删除铁蛋内心描写，通过林夜观察推断'),
        (r'小九[的]?(?:内心|心理|想法|记忆)[^\n。！？]{0,20}[。！？]?', 'other_char_inner', '小九内心直接呈现',
         '删除小九内心描写，通过林夜观察推断'),

        # === 全知叙事打断沉浸感（评审2/3指出）===
        (r'而[此时此刻][\s，][^\n。！？]{0,30}[。！？]?', 'omniscient', '而此刻全知',
         '改为限知叙事：林夜看到/听到/注意到'),
        (r'就在同一时刻[^\n。！？]{0,30}[。！？]?', 'omniscient', '同一时刻',
         '删除并发视角，避免全知视角'),
        (r'读者[^\n。！？]{0,20}[。！？]?', 'omniscient', '读者称呼',
         '删除"读者"，用"林夜注意到"替代'),
        (r'众所周知[^\n。！？]{0,20}[。！？]?', 'omniscient', '众所周知',
         '删除全知陈述，改为林夜知道的信息'),
        (r'没有人知道[^\n。！？]{0,20}[。！？]?', 'omniscient', '没有人知道',
         '删除全知视角，改为具体角色感知'),

        # === 时间线跳脱 ===
        (r'三年后[^\n。！？]{0,20}[。！？]?', 'viewpoint_shift', '三年后',
         '避免宏观时间跳跃，用场景过渡'),
        (r'五年后[^\n。！？]{0,20}[。！？]?', 'viewpoint_shift', '五年后',
         '避免宏观时间跳跃，用场景过渡'),
        (r'多年后[^\n。！？]{0,20}[。！？]?', 'viewpoint_shift', '多年后',
         '避免宏观时间跳跃，用场景过渡'),
        (r'那之后[^\n。！？]{0,20}[。！？]?', 'viewpoint_shift', '那之后',
         '避免模糊时间跳跃，改为具体场景'),

        # === 突然的场景切换标记 ===
        (r'画面[切换到]?[^\n。！？]{0,20}[。！？]?', 'viewpoint_shift', '画面切换',
         '删除，用叙事过渡'),
        (r'场景[切换到转到回到]?[^\n。！？]{0,20}[。！？]?', 'viewpoint_shift', '场景切换',
         '删除，用自然叙事过渡'),
        (r'镜头回到[^\n。！？]{0,20}[。！？]?', 'viewpoint_shift', '镜头回到',
         '删除，改为林夜视角'),
    ]

    # 角色名列表（用于检测非林夜视角）
    OTHER_CHARACTERS = ['莫言', '苏琳', '星月', '铁蛋', '小九', '赵勇', '陈风', '周雪', '林夜父亲', '林夜母亲', '暗皇']

    def __init__(self, chapters_dir: Optional[str] = None):
        super().__init__(self._checker_type)
        if chapters_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            chapters_dir = project_root / '03_内容仓库' / '04_正文'
        self.chapters_dir = Path(chapters_dir)

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        执行叙事视角检查

        直接检查传入的章节内容
        """
        issues = self.check_content(chapter_content, chapter_num)
        return self.generate_issues_for_chapter(chapter_num, issues)

    def check_chapter(self, chapter_num: int) -> List[PerspectiveIssue]:
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        if not ch_file.exists():
            return []
        content = ch_file.read_text(encoding='utf-8')
        return self.check_content(content, chapter_num)

    def check_content(self, content: str, chapter_num: int = 0) -> List[PerspectiveIssue]:
        issues = []
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            for pattern, issue_type, phrase, suggestion in self.VIEWPOINT_SHIFT_PATTERNS:
                matches = re.finditer(pattern, line)
                for match in matches:
                    matched_text = match.group(0)
                    if len(matched_text) > 5:  # 过滤太短的匹配
                        severity = 'HIGH' if issue_type in ('other_char_inner', 'omniscient') else 'MEDIUM'
                        issues.append(PerspectiveIssue(
                            chapter=chapter_num,
                            issue_type=issue_type,
                            description=f"'{phrase}'导致视角跳脱",
                            line_match=matched_text[:60],
                            severity=severity
                        ))

        return issues

    def check_all(self, limit: Optional[int] = None) -> List[PerspectiveIssue]:
        issues = []
        chapter_files = sorted(self.chapters_dir.glob('ch*.md'))
        if limit:
            chapter_files = chapter_files[:limit]

        for ch_file in chapter_files:
            match = re.match(r'ch(\d+)\.md', ch_file.name)
            if match:
                ch_num = int(match.group(1))
                ch_issues = self.check_chapter(ch_num)
                issues.extend(ch_issues)

        return issues

    def generate_issues_for_chapter(self, chapter_num: int) -> List[Issue]:
        """生成符合一致性引擎格式的Issue列表"""
        issues = self.check_chapter(chapter_num)
        result = []

        for issue in issues:
            if issue.severity in ('HIGH', 'MEDIUM'):
                suggestions_map = {
                    'viewpoint_shift': '删除视角跳脱段落，改为林夜所见所闻',
                    'other_char_inner': '删除其他角色内心描写，通过林夜观察呈现',
                    'omniscient': '删除全知陈述，改为限知视角',
                }

                result.append(Issue(
                    id=f"NP_{chapter_num:03d}_{issue.issue_type}",
                    severity=IssueSeverity.P1 if issue.severity == 'HIGH' else IssueSeverity.P2,
                    checker_type=CheckerType.NARRATIVE_PERSPECTIVE,
                    issue_type="narrative_perspective",
                    title=f"叙事视角问题: {issue.issue_type}",
                    description=issue.description,
                    location=IssueLocation(chapter=chapter_num),
                    evidence=issue.line_match,
                    suggestion=suggestions_map.get(issue.issue_type, '改为林夜限知视角')
                ))

        return result

    def generate_report(self, issues: List[PerspectiveIssue]) -> str:
        if not issues:
            return "✅ 叙事视角检查通过：未检测到视角跳脱问题"

        high_issues = [i for i in issues if i.severity == 'HIGH']
        medium_issues = [i for i in issues if i.severity == 'MEDIUM']

        report = ["# 叙事视角检查报告\n"]
        report.append(f"## 汇总\n")
        report.append(f"- HIGH级问题: {len(high_issues)}处\n")
        report.append(f"- MEDIUM级问题: {len(medium_issues)}处\n")

        # 按类型统计
        type_stats = {}
        for issue in issues:
            if issue.issue_type not in type_stats:
                type_stats[issue.issue_type] = {'count': 0, 'chapters': []}
            type_stats[issue.issue_type]['count'] += 1
            type_stats[issue.issue_type]['chapters'].append(issue.chapter)

        if type_stats:
            report.append("\n## 问题类型统计\n")
            for itype, stats in sorted(type_stats.items(), key=lambda x: x[1]['count'], reverse=True):
                ch_list = ', '.join([f"ch{c:03d}" for c in set(stats['chapters'])][:5])
                type_name = {
                    'viewpoint_shift': '视角跳脱',
                    'other_char_inner': '其他角色内心',
                    'omniscient': '全知叙事'
                }.get(itype, itype)
                report.append(f"- **{type_name}**({itype}): {stats['count']}处 (ch{ch_list})")

        # HIGH问题详情
        if high_issues:
            report.append("\n## HIGH 需重写\n")
            by_chapter = {}
            for issue in high_issues:
                if issue.chapter not in by_chapter:
                    by_chapter[issue.chapter] = []
                by_chapter[issue.chapter].append(issue)

            for ch in sorted(by_chapter.keys())[:10]:
                report.append(f"### ch{ch:03d}")
                for issue in by_chapter[ch]:
                    report.append(f"- [{issue.issue_type}] {issue.description}")
                    report.append(f"  例: {issue.line_match}")
                report.append("")

        return "\n".join(report)


if __name__ == '__main__':
    import sys
    checker = NarrativePerspectiveChecker()

    limit = None
    if len(sys.argv) > 1 and sys.argv[1] == '--limit':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    issues = checker.check_all(limit=limit)
    if issues:
        print(checker.generate_report(issues))
    else:
        print("✅ 叙事视角检查通过")