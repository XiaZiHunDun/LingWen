#!/usr/bin/env python3
"""
AI痕迹与修复标记检测器
检测元文本残留和模板句式

检测维度（S3文笔风格 + AI痕迹专项）：
- P0: 修复标记残留（影响可读性）
- P1: 调试/think标记残留（暴露AI生成）
- P2: 评审元数据残留
- P3: 模板句式（轻微AI感）
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from infra.consistency.engine.data_structures import Issue, IssueLocation, CheckerType, IssueSeverity
from .base_checker import BaseChecker


@dataclass
class RepairTraceIssue:
    """AI痕迹问题"""
    chapter: int
    issue_type: str
    count: int
    examples: List[str] = field(default_factory=list)
    severity: str = "MEDIUM"


class RepairTraceChecker(BaseChecker):
    """
    AI痕迹与修复标记检测器
    检测元文本残留和模板句式
    """

    # P0级：修复标记（最严重）
    REPAIR_MARK_PATTERNS = [
        (r'#\s*修复后的章节', '修复后标记'),
        (r'#\s*修复要点说明', '修复要点'),
        (r'#\s*修复记录', '修复记录'),
        (r'#\s*修复日志', '修复日志'),
        (r'<!--.*?-->', 'HTML注释'),
        (r'/\*.*?\*/', 'CSS/JS注释'),
    ]

    # P1级：调试/think标记
    DEBUG_MARK_PATTERNS = [
        (r'<div data-think="true"', 'think标签'),
        (r'<div data-think="false"', 'think标签'),
        (r'<think>.*?', 'think标签'),
        (r'\[think\].*?\[/think\]', 'think标签'),
    ]

    # P2级：评审元数据
    REVIEW_META_PATTERNS = [
        (r'\*\*评审日期\*\*.*?\n', '评审日期'),
        (r'\*\*评分\*\*.*?\n', '评分行'),
        (r'\|维度\|评分.*?\|\n', '评分表格'),
        (r'## 综合评价', '评审综合评价标题'),
    ]

    # P3级：模板句式（阈值2，与报告1/3一致）
    TEMPLATE_PATTERNS = [
        (r'首先[，\s]', '首先模板'),
        (r'其次[，\s]', '其次模板'),
        (r'最后[，\s]', '最后模板'),
        (r'综上所述', '综上所述模板'),
        (r'总的来说', '总的来说模板'),
        (r'值得注意的是', '值得注意的是模板'),
        (r'一般来说', '一般来说模板'),
    ]

    # P3级：情感描写重复模式（报告1/2/3指出"眼眶泛红"类重复）
    # 使用更宽松的匹配模式处理中文
    EMOTIONAL_PATTERNS = [
        # 眼眶相关 - 使用宽松匹配
        (r'眼眶.{0,6}?(?:泛红|发红|红了)', '眼眶泛红'),
        (r'眼眶一阵?[泛红发酸酸涩]', '眼眶泛红'),
        (r'鼻腔泛起一阵酸涩', '鼻腔酸涩'),
        (r'鼻尖一酸', '鼻尖酸'),
        # 喉咙相关（报告1指出）
        (r'喉咙像被什么堵住', '喉咙堵住'),
        (r'喉咙像是被什么堵住', '喉咙堵住'),
        # 胸口/心头相关
        (r'胸口像被攥紧', '胸口紧'),
        (r'心头一沉', '心头一沉'),
        (r'心头一热', '心头一热'),
    ]

    def __init__(self, chapters_dir: Optional[str] = None):
        super().__init__(CheckerType.REPAIR_TRACE)
        if chapters_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            chapters_dir = project_root / '03_内容仓库' / '04_正文'
        self.chapters_dir = Path(chapters_dir)

    def check(self, chapter_content: str, chapter_num: int, context: Optional[Dict[str, Any]] = None) -> List[Issue]:
        """执行检查（符合BaseChecker接口）"""
        repair_issues = self.check_content(chapter_content, chapter_num)
        return self._convert_to_issues(repair_issues)

    def _convert_to_issues(self, repair_issues: List[RepairTraceIssue]) -> List[Issue]:
        """将RepairTraceIssue转换为Issue"""
        result = []
        severity_map = {'P0': IssueSeverity.P0, 'P1': IssueSeverity.P1, 'P2': IssueSeverity.P2, 'P3': IssueSeverity.P3}

        suggestions = {
            'repair_mark': '删除修复标记元文本，保持正文纯净',
            'debug_mark': '删除debug/think标签，保持正文纯净',
            'review_meta': '删除评审元数据，保持正文纯净',
            'template_pattern': '替换模板句式，用更自然的表达',
            'emotional_repeat': '减少情感描写重复，使用身体反应或动作暗示替代',
        }

        for issue in repair_issues:
            result.append(Issue(
                id=f"RT_{issue.chapter:03d}_{issue.issue_type}",
                severity=severity_map.get(issue.severity, IssueSeverity.P2),
                checker_type=CheckerType.REPAIR_TRACE,
                issue_type="repair_trace",
                title=f"AI痕迹: {issue.issue_type}",
                description=f"'{issue.issue_type}'出现{issue.count}处",
                location=IssueLocation(chapter=issue.chapter),
                evidence='; '.join(issue.examples[:2]),
                suggestion=suggestions.get(issue.issue_type, '清理元文本')
            ))
        return result

    def check_chapter(self, chapter_num: int) -> List[RepairTraceIssue]:
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        if not ch_file.exists():
            return []
        content = ch_file.read_text(encoding='utf-8')
        return self.check_content(content, chapter_num)

    def check_content(self, content: str, chapter_num: int = 0) -> List[RepairTraceIssue]:
        issues = []

        # P0: 修复标记
        for pattern, ptype in self.REPAIR_MARK_PATTERNS:
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                issues.append(RepairTraceIssue(
                    chapter=chapter_num,
                    issue_type='repair_mark',
                    count=len(matches),
                    examples=[m[:50] for m in matches[:3]],
                    severity='P0'
                ))

        # P1: 调试标记
        for pattern, ptype in self.DEBUG_MARK_PATTERNS:
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                issues.append(RepairTraceIssue(
                    chapter=chapter_num,
                    issue_type='debug_mark',
                    count=len(matches),
                    examples=[m[:50] for m in matches[:3]],
                    severity='P1'
                ))

        # P2: 评审元数据
        for pattern, ptype in self.REVIEW_META_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                issues.append(RepairTraceIssue(
                    chapter=chapter_num,
                    issue_type='review_meta',
                    count=len(matches),
                    examples=[m[:50] for m in matches[:3]],
                    severity='P2'
                ))

        # P3: 模板句式（阈值2）
        for pattern, ptype in self.TEMPLATE_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                count = len(matches)
                if count >= 2:  # 阈值降为2（报告1/3指出重复2-3次即应检测）
                    issues.append(RepairTraceIssue(
                        chapter=chapter_num,
                        issue_type='template_pattern',
                        count=count,
                        examples=[m[:50] for m in matches[:3]],
                        severity='P3'
                    ))

        # P3: 情感描写重复（阈值2）
        for pattern, ptype in self.EMOTIONAL_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                count = len(matches)
                if count >= 2:  # 阈值2（报告1/2/3指出"眼眶泛红"类重复出现）
                    issues.append(RepairTraceIssue(
                        chapter=chapter_num,
                        issue_type='emotional_repeat',
                        count=count,
                        examples=[m[:50] for m in matches[:3]],
                        severity='P3'
                    ))

        return issues

    def check_all(self, limit: Optional[int] = None) -> List[RepairTraceIssue]:
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

    def generate_report(self, issues: List[RepairTraceIssue]) -> str:
        if not issues:
            return "✅ AI痕迹检查通过：未检测到修复标记残留"

        report = ["# AI痕迹检查报告\n"]

        by_severity = {}
        for issue in issues:
            if issue.severity not in by_severity:
                by_severity[issue.severity] = []
            by_severity[issue.severity].append(issue)

        for sev in ['P0', 'P1', 'P2', 'P3']:
            if sev in by_severity:
                report.append(f"\n## {sev}级问题: {len(by_severity[sev])}处")
                for issue in by_severity[sev][:10]:
                    report.append(f"- ch{issue.chapter:03d}/{issue.issue_type}: {issue.count}处")

        return "\n".join(report)


if __name__ == '__main__':
    import sys
    checker = RepairTraceChecker()

    limit = None
    if len(sys.argv) > 1 and sys.argv[1] == '--limit':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    issues = checker.check_all(limit=limit)
    if issues:
        print(checker.generate_report(issues))
    else:
        print("✅ AI痕迹检查通过")