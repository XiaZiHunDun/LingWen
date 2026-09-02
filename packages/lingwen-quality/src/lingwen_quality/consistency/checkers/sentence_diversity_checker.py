#!/usr/bin/env python3
"""
句式多样性检测器
检测章节句式重复度过高的问题
评分标准（S3文笔风格）：
- 优秀: Shannon指数≥3.5，句式种类≥10种，且无单一句式超过20%
- 合格: Shannon指数≥2.5，句式种类≥6种
- 触发重写: Shannon指数<2.0 或 句式种类<6种 或 某句式占比>40%

当前阈值(excellent=3.0/pass=1.5)已校准，因模式覆盖受限。
随着模式增加，阈值将逐步调整至标准值(Shannon≥3.5/2.5)。
"""

import logging
import math
import re
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from infra.patterns import PatternRegistry

from ..engine.data_structures import CheckerType, Issue, IssueLocation, IssueSeverity
from .base_checker import BaseChecker
from .sentence_diversity_patterns import _load_patterns_from_yaml
from .sentence_diversity_types import (
    DiversityIssue,
    PatternRatio,
    TemplateSentence,
)

logger = logging.getLogger(__name__)


class SentenceDiversityChecker(BaseChecker):
    """
    句式多样性检测器
    使用Shannon多样性指数计算句式分布
    """

    _checker_type = CheckerType.SENTENCE_DIVERSITY

    # 句式模式定义（从YAML加载，带有默认回退机制）
    DIVERSE_PATTERNS, TEMPLATE_PATTERNS = _load_patterns_from_yaml()

    # 评分阈值（S3标准，校准后适配新增陈述句兜底）
    # Shannon指数受句式种类数影响，6种以上可达标
    THRESHOLDS = {
        "excellent": 3.0,
        "pass": 1.5,
        "fail": 1.5,
        "template_ratio": 30.0,
    }

    # 模块级缓存 - 预编译所有正则表达式
    _COMPILED_PATTERNS = None
    _TEMPLATE_COMPILED = None
    _compile_lock = threading.Lock()

    def __init__(self, chapters_dir: Optional[str] = None):
        super().__init__(self._checker_type)
        if chapters_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            chapters_dir = project_root / "03_内容仓库" / "04_正文"
        self.chapters_dir = Path(chapters_dir)

    @classmethod
    def _get_compiled_patterns(cls):
        """获取预编译的模式列表（懒加载，只编译一次）
        优先使用PatternRegistry中的预编译模式，回退到本地编译
        """
        if cls._COMPILED_PATTERNS is not None:
            return cls._COMPILED_PATTERNS, cls._TEMPLATE_COMPILED

        with cls._compile_lock:
            if cls._COMPILED_PATTERNS is not None:
                return cls._COMPILED_PATTERNS, cls._TEMPLATE_COMPILED

            registry = PatternRegistry.get_instance()

            # 优先从PatternRegistry获取已编译的模式
            cls._COMPILED_PATTERNS = []
            for pattern, name, label in cls.DIVERSE_PATTERNS:
                # 尝试从Registry获取同名模式
                reg_pattern = registry.get(name)
                if reg_pattern:
                    cls._COMPILED_PATTERNS.append((reg_pattern, name, label))
                else:
                    # 回退：本地编译
                    try:
                        cls._COMPILED_PATTERNS.append((re.compile(pattern), name, label))
                    except re.error as e:
                        logger.warning(f"正则表达式编译失败 ({name}): {e}")

            # 模板模式处理（Registry中可能没有完整定义）
            cls._TEMPLATE_COMPILED = []
            for pattern, name, suggestions in cls.TEMPLATE_PATTERNS:
                try:
                    cls._TEMPLATE_COMPILED.append((re.compile(pattern), name, suggestions))
                except re.error as e:
                    logger.warning(f"模板正则表达式编译失败 ({name}): {e}")

        return cls._COMPILED_PATTERNS, cls._TEMPLATE_COMPILED

    # 注意：__init__ 在上方Lines 319-324已定义，此处不重复

    def _count_sentences(self, content: str) -> int:
        return len(re.findall(r"[。！？]", content))

    def _calculate_shannon_index(self, distribution: Dict[str, int], total: int) -> float:
        if total == 0:
            return 0.0
        diversity_index = 0.0
        for count in distribution.values():
            p = count / total
            if p > 0:
                diversity_index -= p * math.log2(p)
        return diversity_index

    def score_chapter(self, chapter_num: int) -> Tuple[float, Dict[str, int]]:
        ch_file = self.chapters_dir / f"ch{chapter_num:03d}.md"
        if not ch_file.exists():
            return 0.0, {}
        content = ch_file.read_text(encoding="utf-8")
        return self.score_content(content)

    def score_content(self, content: str) -> Tuple[float, Dict[str, int]]:
        total_sentences = self._count_sentences(content)
        if total_sentences == 0:
            return 0.0, {}

        distribution = {}
        compiled_patterns, _ = self._get_compiled_patterns()
        for compiled_pattern, name, _ in compiled_patterns:
            matches = compiled_pattern.findall(content)
            if matches:
                distribution[name] = len(matches)

        diversity_index = self._calculate_shannon_index(distribution, total_sentences)

        covered = sum(distribution.values())
        uncovered = total_sentences - covered
        if uncovered > 0:
            all_dist = distribution.copy()
            all_dist["_other"] = uncovered
            diversity_index = self._calculate_shannon_index(all_dist, total_sentences)

        return round(diversity_index, 2), distribution

    def get_pattern_ratios(self, chapter_num: int) -> List[PatternRatio]:
        ch_file = self.chapters_dir / f"ch{chapter_num:03d}.md"
        if not ch_file.exists():
            return []
        content = ch_file.read_text(encoding="utf-8")
        return self.get_pattern_ratios_from_content(content)

    def get_pattern_ratios_from_content(self, content: str) -> List[PatternRatio]:
        total_sentences = self._count_sentences(content)
        if total_sentences == 0:
            return []

        distribution = {}
        compiled_patterns, _ = self._get_compiled_patterns()
        for compiled_pattern, name, _ in compiled_patterns:
            matches = compiled_pattern.findall(content)
            if matches:
                distribution[name] = len(matches)

        ratios = []
        for name, count in distribution.items():
            pct = (count / total_sentences) * 100
            ratios.append(
                PatternRatio(
                    pattern_name=name,
                    count=count,
                    percentage=round(pct, 2),
                    is_template=pct > self.THRESHOLDS["template_ratio"],
                )
            )
        ratios.sort(key=lambda x: x.percentage, reverse=True)
        return ratios

    def detect_template_sentences(self, chapter_num: int) -> List[TemplateSentence]:
        ch_file = self.chapters_dir / f"ch{chapter_num:03d}.md"
        if not ch_file.exists():
            return []
        content = ch_file.read_text(encoding="utf-8")
        return self.detect_template_sentences_from_content(content)

    def detect_template_sentences_from_content(self, content: str) -> List[TemplateSentence]:
        total_sentences = self._count_sentences(content)
        if total_sentences == 0:
            return []

        template_sentences = []
        _, compiled_templates = self._get_compiled_patterns()
        for compiled_pattern, template_name, suggestions in compiled_templates:
            matches = compiled_pattern.findall(content)
            if matches:
                count = len(matches)
                pct = (count / total_sentences) * 100
                if pct > self.THRESHOLDS["template_ratio"]:
                    example = matches[0] if matches else ""
                    if len(example) > 30:
                        example = example[:30] + "..."
                    template_sentences.append(
                        TemplateSentence(
                            pattern_name=template_name,
                            template_example=example,
                            count=count,
                            percentage=round(pct, 2),
                            replacement_suggestions=suggestions,
                        )
                    )
        template_sentences.sort(key=lambda x: x.percentage, reverse=True)
        return template_sentences

    def check(
        self, chapter_content: str, chapter_num: int, context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """执行检查，返回标准Issue列表"""
        diversity_issue = self.check_chapter(chapter_num)
        if not diversity_issue:
            return []

        # 转换严重度
        severity_map = {"HIGH": IssueSeverity.P1, "MEDIUM": IssueSeverity.P2, "LOW": IssueSeverity.P3}
        severity = severity_map.get(diversity_issue.severity, IssueSeverity.P2)

        return [
            Issue(
                id=f"diversity-{chapter_num}-{diversity_issue.score}",
                severity=severity,
                checker_type=CheckerType.SENTENCE_DIVERSITY,
                issue_type="sentence_diversity_low",
                title="句式多样性不足",
                description=diversity_issue.description,
                location=IssueLocation(chapter=chapter_num),
                evidence=f"Shannon指数={diversity_issue.score}",
                suggestion="增加句式变化，避免重复使用相同句式结构",
            )
        ]

    def check_chapter(self, chapter_num: int) -> Optional[DiversityIssue]:
        score, distribution = self.score_chapter(chapter_num)
        templates = self.detect_template_sentences(chapter_num)
        template_warnings = [t for t in templates if t.percentage > self.THRESHOLDS["template_ratio"]]

        ch_file = self.chapters_dir / f"ch{chapter_num:03d}.md"
        content = ch_file.read_text(encoding="utf-8") if ch_file.exists() else ""
        total_sentences = self._count_sentences(content)
        pattern_variety = len(distribution)

        dominant_pct = 0
        if total_sentences > 0:
            for name, count in distribution.items():
                pct = (count / total_sentences) * 100
                if pct > dominant_pct:
                    dominant_pct = pct

        issues_desc = []
        if score < self.THRESHOLDS["fail"]:
            issues_desc.append(f"Shannon指数{score:.2f}低于阈值{self.THRESHOLDS['fail']}")
        if pattern_variety < 6:
            issues_desc.append(f"句式种类仅{pattern_variety}种，少于6种")
        if dominant_pct > 40:
            issues_desc.append(f"单一句式占比{dominant_pct:.0f}%超过40%")
        if template_warnings:
            template_names = ", ".join([t.pattern_name for t in template_warnings[:3]])
            issues_desc.append(f"模板句问题：{template_names}")

        if not issues_desc:
            return None

        if score < 2.0 or dominant_pct > 50 or len(template_warnings) >= 2:
            severity = "HIGH"
        elif score < 2.5 or dominant_pct > 40 or template_warnings:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        return DiversityIssue(
            chapter=f"ch{chapter_num:03d}", score=score, severity=severity, description="; ".join(issues_desc)
        )

    def check_all(self, limit: Optional[int] = None) -> List[DiversityIssue]:
        issues = []
        chapter_files = sorted(self.chapters_dir.glob("ch*.md"))
        if limit:
            chapter_files = chapter_files[:limit]

        for ch_file in chapter_files:
            match = re.match(r"ch(\d+)\.md", ch_file.name)
            if match:
                ch_num = int(match.group(1))
                issue = self.check_chapter(ch_num)
                if issue:
                    issues.append(issue)
        return issues

    def generate_report(self, issues: List[DiversityIssue]) -> str:
        if not issues:
            return "✅ 句式多样性检查通过：所有章节评分合格"

        high_issues = [i for i in issues if i.severity == "HIGH"]
        medium_issues = [i for i in issues if i.severity == "MEDIUM"]

        report = ["# 句式多样性检查报告\n"]
        report.append("## 汇总\n")
        report.append(f"- HIGH级问题: {len(high_issues)}章节\n")
        report.append(f"- MEDIUM级问题: {len(medium_issues)}章节\n")

        if high_issues:
            report.append("## HIGH 需重写\n")
            for issue in sorted(high_issues, key=lambda x: x.score):
                report.append(f"- [{issue.chapter}] {issue.description}")

        if medium_issues:
            report.append("\n## MEDIUM 建议优化\n")
            for issue in sorted(medium_issues, key=lambda x: x.score)[:10]:
                report.append(f"- [{issue.chapter}] {issue.description}")

        return "\n".join(report)

    def generate_template_report(self, chapter_num: int) -> str:
        templates = self.detect_template_sentences(chapter_num)
        if not templates:
            return f"ch{chapter_num:03d}: 未检测到模板句问题"

        lines = [f"# 模板句检测报告 - ch{chapter_num:03d}\n"]
        lines.append("## 检测到的模板句问题\n")

        for t in templates:
            lines.append(f"### {t.pattern_name}")
            lines.append(f"- 出现次数: {t.count}")
            lines.append(f"- 占比: {t.percentage}%")
            lines.append(f"- 示例: {t.template_example}")
            lines.append("- 替换建议:")
            for suggestion in t.replacement_suggestions:
                lines.append(f"  - {suggestion}")
            lines.append("")
        return "\n".join(lines)


if __name__ == "__main__":
    import sys

    checker = SentenceDiversityChecker()

    limit = None
    if len(sys.argv) > 1 and sys.argv[1] == "--limit":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    template_mode = "--template" in sys.argv

    if template_mode:
        chapter_files = sorted(checker.chapters_dir.glob("ch*.md"))[: limit or 9999]
        for ch_file in chapter_files:
            match = re.match(r"ch(\d+)\.md", ch_file.name)
            if match:
                ch_num = int(match.group(1))
                templates = checker.detect_template_sentences(ch_num)
                if templates:
                    print(checker.generate_template_report(ch_num))
                    print("---")
    else:
        issues = checker.check_all(limit=limit)
        if issues:
            print(checker.generate_report(issues))
            high_count = len([i for i in issues if i.severity == "HIGH"])
            print(f"\n总计: {len(issues)}章节有问题（{high_count} HIGH）")
            sys.exit(1) if high_count > 0 else sys.exit(0)
        else:
            print("✅ 句式多样性检查通过：所有章节评分合格")
            sys.exit(0)
