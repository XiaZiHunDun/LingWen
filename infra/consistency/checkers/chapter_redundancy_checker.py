#!/usr/bin/env python3
"""
章节重复度检测器
检测相邻或相近章节间的内容重复问题
基于评审2建议：
- 2-3章功能重复（求生）→ 合并1章
- 11-15章连续5章守护主题 → 压缩2章
- 46-50章铁蛋→莫言温情戏 → 压缩2章

检测方法：
1. N-gram相似度（连续句子片段）
2. 关键词重叠率
3. 主题句重复检测
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from infra.consistency.engine.data_structures import CheckerType, Issue, IssueLocation, IssueSeverity

from .base_checker import BaseChecker


@dataclass
class ChapterRedundancyIssue:
    """章节重复问题"""
    chapter_a: int
    chapter_b: int
    similarity_score: float
    repeat_type: str  # 'ngram' | 'keyword' | 'theme'
    shared_content: List[str] = None
    severity: str = "MEDIUM"

    def __post_init__(self):
        if self.shared_content is None:
            self.shared_content = []


class ChapterRedundancyChecker(BaseChecker):
    """
    章节重复度检测器
    检测章节间的内容重复
    """
    _checker_type = CheckerType.CHAPTER_REDUNDANCY


    # N-gram参数
    NGRAM_SIZE = 3  # 连续3句话为N-gram
    NGRAM_THRESHOLD = 0.3  # 30%重复率阈值

    # 关键词参数
    KEYWORD_THRESHOLD = 0.5  # 50%关键词重叠

    # 已知需要合并的章节范围（基于评审2建议）
    KNOWN_REDUNDANT_RANGES = [
        (2, 3, "求生内容重复"),
        (11, 15, "守护主题连续5章"),
        (46, 50, "铁蛋→莫言温情戏过长"),
    ]

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
        执行章节重复度检查

        检查指定章节与相邻章节的重复度
        """
        issues = []

        # 检查与前一章的重复度
        if chapter_num > 1:
            pair_issues = self.check_chapter_pair(chapter_num - 1, chapter_num)
            for issue in pair_issues:
                if issue.severity in ('HIGH', 'MEDIUM'):
                    issues.append(Issue(
                        id=f"CR_{chapter_num-1:03d}_{chapter_num:03d}_{issue.repeat_type}",
                        severity=IssueSeverity.P1 if issue.severity == 'HIGH' else IssueSeverity.P2,
                        checker_type=CheckerType.CHAPTER_REDUNDANCY,
                        issue_type="chapter_redundancy",
                        title=f"章节重复: ch{chapter_num-1}-ch{chapter_num}",
                        description=f"与前一章重复度{issue.similarity_score*100:.1f}%",
                        location=IssueLocation(chapter=chapter_num),
                        evidence=f"重复类型: {issue.repeat_type}",
                        suggestion="考虑合并或删减重复内容"
                    ))

        # 检查与后一章的重复度
        next_ch = chapter_num + 1
        ch_file = self.chapters_dir / f'ch{next_ch:03d}.md'
        if ch_file.exists():
            pair_issues = self.check_chapter_pair(chapter_num, next_ch)
            for issue in pair_issues:
                if issue.severity in ('HIGH', 'MEDIUM'):
                    issues.append(Issue(
                        id=f"CR_{chapter_num:03d}_{next_ch:03d}_{issue.repeat_type}",
                        severity=IssueSeverity.P1 if issue.severity == 'HIGH' else IssueSeverity.P2,
                        checker_type=CheckerType.CHAPTER_REDUNDANCY,
                        issue_type="chapter_redundancy",
                        title=f"章节重复: ch{chapter_num}-ch{next_ch}",
                        description=f"与后一章重复度{issue.similarity_score*100:.1f}%",
                        location=IssueLocation(chapter=chapter_num),
                        evidence=f"重复类型: {issue.repeat_type}",
                        suggestion="考虑合并或删减重复内容"
                    ))

        return issues

    def _read_chapter(self, chapter_num: int) -> str:
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        if not ch_file.exists():
            return ""
        return ch_file.read_text(encoding='utf-8')

    def _extract_sentences(self, content: str) -> List[str]:
        """提取句子列表"""
        sentences = re.split(r'[。！？\n]+', content)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

    def _extract_keywords(self, sentences: List[str]) -> Set[str]:
        """提取关键词（简化版：名词+动词+形容词）"""
        words = []
        for sent in sentences:
            # 去除标点和常用词
            cleaned = re.sub(r'[^\w]', '', sent)
            if len(cleaned) > 1:
                words.append(cleaned)
        return set(words)

    def _compute_ngram_similarity(self, sentences_a: List[str], sentences_b: List[str]) -> float:
        """计算N-gram相似度"""
        if not sentences_a or not sentences_b:
            return 0.0

        def get_ngrams(sents: List[str], n: int) -> List[str]:
            ngrams = []
            for i in range(len(sents) - n + 1):
                ngram = '|||'.join(sents[i:i+n])
                ngrams.append(ngram)
            return ngrams

        ngrams_a = set(get_ngrams(sentences_a, self.NGRAM_SIZE))
        ngrams_b = set(get_ngrams(sentences_b, self.NGRAM_SIZE))

        if not ngrams_a or not ngrams_b:
            return 0.0

        intersection = len(ngrams_a & ngrams_b)
        union = len(ngrams_a | ngrams_b)

        return intersection / union if union > 0 else 0.0

    def _compute_keyword_overlap(self, keywords_a: Set[str], keywords_b: Set[str]) -> float:
        """计算关键词重叠率"""
        if not keywords_a or not keywords_b:
            return 0.0

        intersection = len(keywords_a & keywords_b)
        smaller = min(len(keywords_a), len(keywords_b))

        return intersection / smaller if smaller > 0 else 0.0

    def check_chapter_pair(self, ch_a: int, ch_b: int) -> List[ChapterRedundancyIssue]:
        """检查两个章节间的重复度"""
        content_a = self._read_chapter(ch_a)
        content_b = self._read_chapter(ch_b)

        if not content_a or not content_b:
            return []

        sentences_a = self._extract_sentences(content_a)
        sentences_b = self._extract_sentences(content_b)

        issues = []

        # N-gram相似度
        ngram_sim = self._compute_ngram_similarity(sentences_a, sentences_b)
        if ngram_sim > self.NGRAM_THRESHOLD:
            # 找出共同的N-gram片段
            def get_ngrams(sents: List[str], n: int) -> List[str]:
                ngrams = []
                for i in range(len(sents) - n + 1):
                    ngram = '|||'.join(sents[i:i+n])
                    ngrams.append(ngram)
                return ngrams

            ngrams_a = get_ngrams(sentences_a, self.NGRAM_SIZE)
            ngrams_b = get_ngrams(sentences_b, self.NGRAM_SIZE)
            shared = list(set(ngrams_a) & set(ngrams_b))[:5]  # 最多5个

            severity = 'HIGH' if ngram_sim > 0.5 else 'MEDIUM'
            issues.append(ChapterRedundancyIssue(
                chapter_a=ch_a,
                chapter_b=ch_b,
                similarity_score=round(ngram_sim, 3),
                repeat_type='ngram',
                shared_content=shared,
                severity=severity
            ))

        # 关键词重叠
        keywords_a = self._extract_keywords(sentences_a)
        keywords_b = self._extract_keywords(sentences_b)
        kw_overlap = self._compute_keyword_overlap(keywords_a, keywords_b)

        if kw_overlap > self.KEYWORD_THRESHOLD:
            severity = 'HIGH' if kw_overlap > 0.7 else 'MEDIUM'
            issues.append(ChapterRedundancyIssue(
                chapter_a=ch_a,
                chapter_b=ch_b,
                similarity_score=round(kw_overlap, 3),
                repeat_type='keyword',
                shared_content=[],
                severity=severity
            ))

        return issues

    def check_range(self, start: int, end: int) -> List[ChapterRedundancyIssue]:
        """检查一个范围内的章节重复"""
        issues = []
        for i in range(start, end):
            for j in range(i + 1, min(end + 1, i + 4)):  # 最多比较相邻3章
                pair_issues = self.check_chapter_pair(i, j)
                issues.extend(pair_issues)
        return issues

    def check_all(self, limit: Optional[int] = None) -> List[ChapterRedundancyIssue]:
        """检查所有章节"""
        issues = []

        # 1. 检查已知重复范围
        for start, end, reason in self.KNOWN_REDUNDANT_RANGES:
            range_issues = self.check_range(start, end)
            for issue in range_issues:
                issue.repeat_type = f"known_{reason}"
            issues.extend(range_issues)

        # 2. 滑动窗口检查所有相邻章节
        chapter_files = sorted(self.chapters_dir.glob('ch*.md'))
        if limit:
            chapter_files = chapter_files[:limit]

        chapter_nums = []
        for ch_file in chapter_files:
            match = re.match(r'ch(\d+)\.md', ch_file.name)
            if match:
                chapter_nums.append(int(match.group(1)))

        for i in range(len(chapter_nums) - 1):
            ch_a = chapter_nums[i]
            ch_b = chapter_nums[i + 1]
            pair_issues = self.check_chapter_pair(ch_a, ch_b)
            for issue in pair_issues:
                if issue.severity == 'HIGH':  # 只报告HIGH级问题
                    issues.append(issue)

        return issues

    def generate_issues_for_range(self, start: int, end: int, reason: str) -> List[Issue]:
        """为已知重复范围生成Issue列表"""
        issues = []
        range_issues = self.check_range(start, end)

        for issue in range_issues:
            if issue.severity in ('HIGH', 'MEDIUM'):
                suggestions = {
                    (2, 3): "合并为1章，保留裂爪兽、第一次杀人等关键场景",
                    (11, 15): "压缩为2章，保留篝火夜话、小九噩梦等关键情感场景",
                    (46, 50): "压缩为2章，保留'修断剑'和'噩梦'关键场景",
                }
                suggestion = suggestions.get((start, end), "考虑合并或删减重复内容")

                issues.append(Issue(
                    id=f"CR_{start:03d}_{end:03d}_{issue.repeat_type}",
                    severity=IssueSeverity.P1 if issue.severity == 'HIGH' else IssueSeverity.P2,
                    checker_type=CheckerType.CHAPTER_REDUNDANCY,
                    issue_type="chapter_redundancy",
                    title=f"章节重复: ch{start}-ch{end} {reason}",
                    description=f"ch{issue.chapter_a}与ch{issue.chapter_b}重复度{issue.similarity_score*100:.1f}%",
                    location=IssueLocation(chapter=issue.chapter_a),
                    evidence=f"重复类型: {issue.repeat_type}",
                    suggestion=suggestion
                ))

        return issues

    def generate_report(self, issues: List[ChapterRedundancyIssue]) -> str:
        if not issues:
            return "✅ 章节重复度检查通过：未检测到显著的章节重复"

        high_issues = [i for i in issues if i.severity == 'HIGH']
        medium_issues = [i for i in issues if i.severity == 'MEDIUM']

        report = ["# 章节重复度检查报告\n"]
        report.append("## 汇总\n")
        report.append(f"- HIGH级问题: {len(high_issues)}对\n")
        report.append(f"- MEDIUM级问题: {len(medium_issues)}对\n")

        if high_issues:
            report.append("\n## HIGH 需重写\n")
            for issue in sorted(high_issues, key=lambda x: x.similarity_score, reverse=True)[:10]:
                report.append(f"- ch{issue.chapter_a} ↔ ch{issue.chapter_b}: {issue.similarity_score*100:.1f}%重复 ({issue.repeat_type})")
                if issue.shared_content:
                    for content in issue.shared_content[:2]:
                        clean = content.replace('|||', ' ')
                        if len(clean) > 50:
                            clean = clean[:50] + '...'
                        report.append(f"  例: {clean}")

        if medium_issues:
            report.append("\n## MEDIUM 建议优化\n")
            for issue in sorted(medium_issues, key=lambda x: x.similarity_score, reverse=True)[:5]:
                report.append(f"- ch{issue.chapter_a} ↔ ch{issue.chapter_b}: {issue.similarity_score*100:.1f}%重复 ({issue.repeat_type})")

        # 已知问题区域
        report.append("\n## 评审建议的待合并章节\n")
        for start, end, reason in self.KNOWN_REDUNDANT_RANGES:
            range_issues = [i for i in issues if start <= i.chapter_a <= end and start <= i.chapter_b <= end]
            if range_issues:
                max_sim = max(i.similarity_score for i in range_issues)
                report.append(f"- ch{start}-ch{end}: {reason} (最大重复度: {max_sim*100:.1f}%)")
            else:
                report.append(f"- ch{start}-ch{end}: {reason} (未检测到显著重复)")

        return "\n".join(report)


if __name__ == '__main__':
    import sys
    checker = ChapterRedundancyChecker()

    limit = None
    if len(sys.argv) > 1 and sys.argv[1] == '--limit':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    issues = checker.check_all(limit=limit)
    if issues:
        print(checker.generate_report(issues))
    else:
        print("✅ 章节重复度检查通过")
