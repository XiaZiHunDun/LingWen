#!/usr/bin/env python3
"""
Quality Coordinator

Orchestrates both rule-based and LLM quality checks, deduplicates results,
and produces a single UnifiedQualityReport.
"""

import logging
from typing import List, Dict, Any, Optional, Type
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .interfaces import (
    UnifiedIssue, UnifiedQualityReport, UnifiedSeverity,
    QualitySource, DomainSpecificReport
)
from .adapters import RuleBasedAdapter

logger = logging.getLogger(__name__)


class QualityCoordinator:
    """
    Coordinates quality checking from both rule-based and LLM sources.

    Usage:
        coordinator = QualityCoordinator()

        # Run all checks
        report = coordinator.check_chapter(chapter_num, content)

        # Run only rule-based
        report = coordinator.check_chapter(chapter_num, content, sources=["rule_based"])

        # Run only specific LLM analyzers
        report = coordinator.check_chapter(
            chapter_num, content,
            sources=["llm"],
            llm_analyzers=["foreshadow", "emotional_resonance"]
        )
    """

    def __init__(
        self,
        consistency_engine=None,
        llm_analyzers: Optional[List[str]] = None,
        deduplicate: bool = True,
        parallel: bool = True,
        max_workers: int = 4
    ):
        """
        Initialize the QualityCoordinator.

        Args:
            consistency_engine: Existing ConsistencyEngine instance (lazy-loaded if None)
            llm_analyzers: List of LLM analyzer names to use (["all"] if None)
            deduplicate: Whether to deduplicate issues from different sources
            parallel: Whether to run checks in parallel
            max_workers: Max parallel workers
        """
        self._consistency_engine = consistency_engine
        self.llm_analyzers = llm_analyzers or ["all"]
        self.deduplicate = deduplicate
        self.parallel = parallel
        self.max_workers = max_workers

    @property
    def consistency_engine(self):
        """Lazy-load consistency engine"""
        if self._consistency_engine is None:
            from infra.consistency.engine.consistency_engine import ConsistencyEngine
            self._consistency_engine = ConsistencyEngine()
        return self._consistency_engine

    def check_chapter(
        self,
        chapter_num: int,
        chapter_content: str,
        context: Optional[Dict[str, Any]] = None,
        sources: Optional[List[str]] = None,
        llm_analyzers: Optional[List[str]] = None
    ) -> UnifiedQualityReport:
        """
        Check a chapter using both rule-based and LLM analyzers.

        Args:
            chapter_num: Chapter number
            chapter_content: Chapter content
            context: Optional context dict
            sources: List of sources to use ["rule_based", "llm"] (all if None)
            llm_analyzers: Specific LLM analyzers to run (all if None)

        Returns:
            UnifiedQualityReport
        """
        sources = sources or ["rule_based", "llm"]
        llm_analyzers = llm_analyzers or ["all"]
        context = context or {}

        report = UnifiedQualityReport(chapter=chapter_num)

        if self.parallel and len(sources) > 1:
            report = self._check_parallel(
                chapter_num, chapter_content, context, sources, llm_analyzers
            )
        else:
            report = self._check_sequential(
                chapter_num, chapter_content, context, sources, llm_analyzers
            )

        # Deduplicate if enabled
        if self.deduplicate and len(sources) > 1:
            report.issues = self._deduplicate_issues(report.issues)

        # Calculate overall score
        report.overall_score = self._calculate_overall_score(report)

        # Make verdict
        report.make_verdict()

        return report

    def _check_parallel(
        self,
        chapter_num: int,
        chapter_content: str,
        context: Dict[str, Any],
        sources: List[str],
        llm_analyzers: List[str]
    ) -> UnifiedQualityReport:
        """Run checks in parallel"""
        report = UnifiedQualityReport(chapter=chapter_num)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}

            if "rule_based" in sources:
                future = executor.submit(
                    self._check_rule_based, chapter_num, chapter_content, context
                )
                futures[future] = ("rule_based", None)

            if "llm" in sources:
                for analyzer_name in self._resolve_llm_analyzers(llm_analyzers):
                    future = executor.submit(
                        self._check_llm_analyzer,
                        analyzer_name, chapter_num, chapter_content
                    )
                    futures[future] = ("llm", analyzer_name)

            for future in as_completed(futures):
                source_type, analyzer_name = futures[future]
                try:
                    result = future.result()
                    if source_type == "rule_based":
                        report.issues.extend(result)
                        report.sources_checked.append("rule_based")
                    else:
                        issues, domain_report = result
                        report.issues.extend(issues)
                        if domain_report:
                            report.domain_reports.append(domain_report)
                        report.sources_checked.append(f"llm_{analyzer_name}")
                except Exception as e:
                    logger.error(f"Check failed for {source_type}: {e}")

        return report

    def _check_sequential(
        self,
        chapter_num: int,
        chapter_content: str,
        context: Dict[str, Any],
        sources: List[str],
        llm_analyzers: List[str]
    ) -> UnifiedQualityReport:
        """Run checks sequentially"""
        report = UnifiedQualityReport(chapter=chapter_num)

        for source in sources:
            if source == "rule_based":
                issues = self._check_rule_based(chapter_num, chapter_content, context)
                report.issues.extend(issues)
                report.sources_checked.append("rule_based")
            elif source == "llm":
                for analyzer_name in self._resolve_llm_analyzers(llm_analyzers):
                    try:
                        issues, domain_report = self._check_llm_analyzer(
                            analyzer_name, chapter_num, chapter_content
                        )
                        report.issues.extend(issues)
                        if domain_report:
                            report.domain_reports.append(domain_report)
                        report.sources_checked.append(f"llm_{analyzer_name}")
                    except Exception as e:
                        logger.error(f"LLM analyzer {analyzer_name} failed: {e}")

        return report

    def _check_rule_based(
        self,
        chapter_num: int,
        chapter_content: str,
        context: Dict[str, Any]
    ) -> List[UnifiedIssue]:
        """Run rule-based consistency checks"""
        try:
            consistency_report = self.consistency_engine.check_chapter(
                chapter_num=chapter_num,
                chapter_content=chapter_content,
                context=context
            )
            unified = RuleBasedAdapter.to_unified_report(consistency_report)
            return unified.issues
        except Exception as e:
            logger.error(f"Rule-based check failed: {e}")
            return []

    def _check_llm_analyzer(
        self,
        analyzer_name: str,
        chapter_num: int,
        chapter_content: str
    ) -> tuple[List[UnifiedIssue], Optional[DomainSpecificReport]]:
        """Run a specific LLM analyzer"""
        if analyzer_name == "foreshadow":
            return self._check_foreshadow(chapter_num, chapter_content)
        elif analyzer_name == "emotional_resonance":
            return self._check_emotional(chapter_num, chapter_content)
        elif analyzer_name == "pacing":
            return self._check_pacing(chapter_num, chapter_content)
        elif analyzer_name == "character_arc":
            return self._check_character_arc(chapter_num, chapter_content)
        elif analyzer_name == "protagonist":
            return self._check_protagonist(chapter_num, chapter_content)
        elif analyzer_name == "readability":
            return self._check_readability(chapter_num, chapter_content)
        else:
            logger.warning(f"Unknown LLM analyzer: {analyzer_name}")
            return [], None

    def _check_foreshadow(self, chapter_num, content):
        """Run foreshadow analyzer"""
        try:
            from tools.llm_foreshadow_analyzer import ForeshadowAnalyzer
            from .adapters import LLMForeshadowAdapter

            analyzer = ForeshadowAnalyzer()
            report = analyzer.analyze_chapter_foreshadows(chapter_num, content)

            issues = LLMForeshadowAdapter.to_unified_issues(report)
            domain_report = LLMForeshadowAdapter.to_domain_report(report)
            return issues, domain_report
        except Exception as e:
            logger.error(f"Foreshadow analyzer failed: {e}")
            return [], None

    def _check_emotional(self, chapter_num, content):
        """Run emotional resonance checker"""
        try:
            from tools.llm_emotional_resonance_checker import EmotionalResonanceChecker
            from .adapters import LLMEmotionalAdapter

            checker = EmotionalResonanceChecker()
            report = checker.check_emotional_resonance(chapter_num, content)

            issues = LLMEmotionalAdapter.to_unified_issues(report)
            domain_report = LLMEmotionalAdapter.to_domain_report(report)
            return issues, domain_report
        except Exception as e:
            logger.error(f"Emotional resonance checker failed: {e}")
            return [], None

    def _check_pacing(self, chapter_num, content):
        """Run pacing analyzer"""
        try:
            from tools.llm_pacing_analyzer import PacingAnalyzer
            from .adapters import LLMPacingAdapter

            analyzer = PacingAnalyzer()
            report = analyzer.analyze_pacing(chapter_num, content)

            issues = LLMPacingAdapter.to_unified_issues(report)
            domain_report = LLMPacingAdapter.to_domain_report(report)
            return issues, domain_report
        except Exception as e:
            logger.error(f"Pacing analyzer failed: {e}")
            return [], None

    def _check_character_arc(self, chapter_num, content):
        """Run character arc analyzer (placeholder - full implementation needed)"""
        # Placeholder - would need to implement CharacterArcAnalyzer adapter
        return [], None

    def _check_protagonist(self, chapter_num, content):
        """Run protagonist charm analyzer (placeholder - full implementation needed)"""
        # Placeholder - would need to implement ProtagonistCharmAnalyzer adapter
        return [], None

    def _check_readability(self, chapter_num, content):
        """Run readability analyzer (placeholder - full implementation needed)"""
        # Placeholder - would need to implement ReadabilityAnalyzer adapter
        return [], None

    def _resolve_llm_analyzers(self, requested: List[str]) -> List[str]:
        """Resolve which LLM analyzers to run"""
        all_analyzers = [
            "foreshadow", "emotional_resonance", "pacing",
            "character_arc", "protagonist", "readability"
        ]

        if "all" in requested:
            return all_analyzers

        return [a for a in requested if a in all_analyzers]

    def _deduplicate_issues(self, issues: List[UnifiedIssue]) -> List[UnifiedIssue]:
        """
        Deduplicate issues based on location and issue_type.

        Issues are considered duplicates if they have:
        1. Same location (chapter + paragraph + line)
        2. Same issue_type
        3. Same source_name

        Keeps the issue with higher confidence.
        """
        seen = {}

        for issue in issues:
            # Create dedup key
            key = (
                issue.location.chapter,
                issue.location.paragraph,
                issue.location.line,
                issue.issue_type,
                issue.source_name
            )

            if key not in seen:
                seen[key] = issue
            elif issue.confidence > seen[key].confidence:
                seen[key] = issue

        return list(seen.values())

    def _calculate_overall_score(self, report: UnifiedQualityReport) -> float:
        """Calculate overall quality score"""
        base_score = 100.0

        # Deduct for issues by severity
        p0_penalty = report.p0_count * 30
        p1_penalty = report.p1_count * 15
        p2_penalty = report.p2_count * 3
        p3_penalty = report.p3_count * 1

        total_deduction = p0_penalty + p1_penalty + p2_penalty + p3_penalty

        # Boost for LLM domain reports
        if report.domain_reports:
            avg_llm_score = sum(r.score for r in report.domain_reports) / len(report.domain_reports)
            # Weighted combination: 70% issue-based, 30% LLM score
            issue_score = max(0, base_score - total_deduction)
            return issue_score * 0.7 + avg_llm_score * 100 * 0.3

        return max(0, base_score - total_deduction)