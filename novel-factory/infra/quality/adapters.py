#!/usr/bin/env python3
"""
Adapters for converting existing formats to unified format.

将旧格式转换为统一格式：
- Rule-based Issue from infra/consistency/engine/data_structures.py
- LLM analyzer reports from tools/llm_*.py
"""

import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .interfaces import (
    DomainSpecificReport,
    QualityDimension,
    QualitySource,
    UnifiedIssue,
    UnifiedLocation,
    UnifiedQualityReport,
    UnifiedSeverity,
)

if TYPE_CHECKING:
    from infra.consistency.engine.data_structures import CheckerType, ConsistencyReport, IssueSeverity
    from infra.consistency.engine.data_structures import Issue as RuleBasedIssue
    from tools.llm_emotional_resonance_checker import EmotionalResonanceReport
    from tools.llm_foreshadow_analyzer import ForeshadowAnalysisReport
    from tools.llm_pacing_analyzer import PacingReport


class RuleBasedAdapter:
    """
    Adapter for converting rule-based Issue to UnifiedIssue.

    Handles the mapping between the rule-based Issue system
    and the unified issue system.
    """

    # Mapping from CheckerType to QualityDimension
    CHECKER_TO_DIMENSION: Dict[str, QualityDimension] = {
        "character_checker": QualityDimension.S9_CHARACTER_CONSISTENCY,
        "character_state": QualityDimension.S9_CHARACTER_CONSISTENCY,
        "item_checker": QualityDimension.S2_LOGIC_CONSISTENCY,
        "timeline_checker": QualityDimension.S2_LOGIC_CONSISTENCY,
        "timeline_age": QualityDimension.S2_LOGIC_CONSISTENCY,
        "ability_checker": QualityDimension.S2_LOGIC_CONSISTENCY,
        "personality_checker": QualityDimension.S8_CHARACTER_ARC,
        "foreshadow_checker": QualityDimension.S11_FORESHADOW_RECOVERY,
        "foreshadow_quality": QualityDimension.S11_FORESHADOW_RECOVERY,
        "outline_checker": QualityDimension.S1_PLOT_COMPLETENESS,
        "ai_gloss_checker": QualityDimension.S3_WRITING_STYLE,
        "scene_pattern_repeat": QualityDimension.S5_PACING_CONTROL,
        "pacing_checker": QualityDimension.S5_PACING_CONTROL,
        "scene_transition_checker": QualityDimension.S5_PACING_CONTROL,
        "sentence_diversity": QualityDimension.S3_WRITING_STYLE,
        "repetitive_phrase": QualityDimension.S3_WRITING_STYLE,
        "chapter_redundancy": QualityDimension.S6_READABILITY,
        "narrative_perspective": QualityDimension.S3_WRITING_STYLE,
        "character_agency": QualityDimension.S7_PROTAGONIST_CHARM,
        "battle_visualization": QualityDimension.S5_PACING_CONTROL,
        "cross_chapter_logic": QualityDimension.S2_LOGIC_CONSISTENCY,
        "repair_trace": QualityDimension.S2_LOGIC_CONSISTENCY,
        "gender_consistency": QualityDimension.S9_CHARACTER_CONSISTENCY,
        "causal_chain": QualityDimension.S2_LOGIC_CONSISTENCY,
        "spatial_transition": QualityDimension.S5_PACING_CONTROL,
        "relationship_state": QualityDimension.S8_CHARACTER_ARC,
        "knowledge_tracking": QualityDimension.S2_LOGIC_CONSISTENCY,
        "dialogue_action": QualityDimension.S3_WRITING_STYLE,
        "llm_causal_reasoning": QualityDimension.S2_LOGIC_CONSISTENCY,
    }

    @staticmethod
    def severity_to_unified(severity: "IssueSeverity") -> UnifiedSeverity:
        """Convert rule-based severity to unified severity"""
        mapping = {
            "P0": UnifiedSeverity.P0,
            "P1": UnifiedSeverity.P1,
            "P2": UnifiedSeverity.P2,
            "P3": UnifiedSeverity.P3,
        }
        return mapping.get(severity.value, UnifiedSeverity.P2)

    @classmethod
    def to_unified_issue(cls, issue: "RuleBasedIssue") -> UnifiedIssue:
        """Convert a rule-based Issue to UnifiedIssue"""
        location = UnifiedLocation(
            chapter=issue.location.chapter,
            paragraph=issue.location.paragraph,
            line=issue.location.line,
            start_pos=issue.location.start_pos,
            end_pos=issue.location.end_pos,
        )

        # Determine dimension from checker type
        checker_value = issue.checker_type.value if hasattr(issue.checker_type, 'value') else str(issue.checker_type)
        dimension = cls.CHECKER_TO_DIMENSION.get(checker_value)

        return UnifiedIssue(
            id=issue.id or str(uuid.uuid4()),
            severity=cls.severity_to_unified(issue.severity),
            source=QualitySource.RULE_BASED,
            source_name=checker_value,
            issue_type=issue.issue_type,
            title=issue.title,
            description=issue.description,
            location=location,
            evidence=issue.evidence,
            suggestion=issue.suggestion,
            dimension=dimension,
            confidence=issue.confidence_score,
            metadata={
                "character": issue.character,
                "confidence_level": issue.confidence.value if hasattr(issue.confidence, 'value') else str(issue.confidence),
                "context_used": issue.context_used,
                "needs_llm_review": issue.needs_llm_review,
            }
        )

    @classmethod
    def to_unified_report(cls, report: "ConsistencyReport") -> UnifiedQualityReport:
        """Convert a ConsistencyReport to UnifiedQualityReport"""
        unified_issues = [
            cls.to_unified_issue(issue)
            for issue in report.issues
        ]

        # Convert quality dimension scores
        dim_scores = {
            QualityDimension.S1_PLOT_COMPLETENESS: report.quality.s1_plot_completeness * 20,
            QualityDimension.S2_LOGIC_CONSISTENCY: report.quality.s2_logic_consistency * 20,
            QualityDimension.S3_WRITING_STYLE: report.quality.s3_writing_style * 20,
            QualityDimension.S4_EMOTIONAL_RESONANCE: report.quality.s4_emotional_resonance * 20,
            QualityDimension.S5_PACING_CONTROL: report.quality.s5_pacing_control * 20,
            QualityDimension.S6_READABILITY: report.quality.s6_readability * 20,
            QualityDimension.S7_PROTAGONIST_CHARM: report.quality.s7_protagonist_charm * 20,
            QualityDimension.S8_CHARACTER_ARC: report.quality.s8_character_arc * 20,
        }

        checker_names = []
        for cr in report.checker_results:
            val = cr.checker_type.value if hasattr(cr.checker_type, 'value') else str(cr.checker_type)
            checker_names.append(val)

        return UnifiedQualityReport(
            chapter=report.chapter,
            check_time=report.check_time,
            issues=unified_issues,
            dimension_scores=dim_scores,
            overall_score=report.total_score,
            verdict=report.verdict,
            sources_checked=checker_names,
        )


class LLMForeshadowAdapter:
    """Adapter for ForeshadowAnalysisReport"""

    @classmethod
    def to_unified_issues(
        cls,
        report: "ForeshadowAnalysisReport"
    ) -> List[UnifiedIssue]:
        """Convert foreshadow records to unified issues"""
        issues = []
        for record in report.records:
            if not record.is_released and record.confidence > 0.5:
                location = UnifiedLocation(chapter=record.chapter)

                issue = UnifiedIssue(
                    id=f"fs_{record.chapter}_{uuid.uuid4().hex[:8]}",
                    severity=UnifiedSeverity.P2,
                    source=QualitySource.LLM_ANALYZER,
                    source_name="foreshadow_analyzer",
                    issue_type="unreleased_foreshadow",
                    title=f"未回收伏笔 ({record.category})",
                    description=f"伏笔内容: {record.text[:100]}",
                    location=location,
                    evidence=record.text,
                    suggestion=record.suggestion,
                    dimension=QualityDimension.S11_FORESHADOW_RECOVERY,
                    confidence=record.confidence,
                    metadata={
                        "is_released": record.is_released,
                        "release_chapter": record.release_chapter,
                        "release_quality": record.release_quality,
                        "connection_to_main": record.connection_to_main,
                    }
                )
                issues.append(issue)
        return issues

    @classmethod
    def to_domain_report(
        cls,
        report: "ForeshadowAnalysisReport"
    ) -> DomainSpecificReport:
        """Convert to domain-specific report"""
        return DomainSpecificReport(
            report_type="foreshadow",
            chapter=report.chapter,
            score=report.score,
            raw_data=report.to_dict(),
        )


class LLMEmotionalAdapter:
    """Adapter for EmotionalResonanceReport"""

    @classmethod
    def to_unified_issues(
        cls,
        report: "EmotionalResonanceReport"
    ) -> List[UnifiedIssue]:
        """Convert emotional points to unified issues"""
        issues = []
        for point in report.emotional_points:
            if point.quality in ("formulaic", "fake") and point.authenticity_score < 0.6:
                location = UnifiedLocation(chapter=point.chapter)

                issue = UnifiedIssue(
                    id=f"em_{point.chapter}_{uuid.uuid4().hex[:8]}",
                    severity=UnifiedSeverity.P2,
                    source=QualitySource.LLM_ANALYZER,
                    source_name="emotional_resonance_checker",
                    issue_type=f"low_quality_emotion_{point.quality}",
                    title=f"情感质量({point.quality}): {point.trigger_type}",
                    description=f"情感描写: {point.text[:100]}",
                    location=location,
                    evidence=point.text,
                    suggestion=point.suggestion,
                    dimension=QualityDimension.S4_EMOTIONAL_RESONANCE,
                    confidence=point.authenticity_score,
                    metadata={
                        "emotion_type": point.type,
                        "trigger_type": point.trigger_type,
                        "quality": point.quality,
                    }
                )
                issues.append(issue)
        return issues

    @classmethod
    def to_domain_report(
        cls,
        report: "EmotionalResonanceReport"
    ) -> DomainSpecificReport:
        """Convert to domain-specific report"""
        return DomainSpecificReport(
            report_type="emotional_resonance",
            chapter=report.chapter,
            score=report.score,
            raw_data=report.to_dict(),
        )


class LLMPacingAdapter:
    """Adapter for PacingReport"""

    @classmethod
    def to_unified_issues(
        cls,
        report: "PacingReport"
    ) -> List[UnifiedIssue]:
        """Convert tension points to unified issues"""
        issues = []
        for point in report.tension_points:
            if point.is_predictable or point.urgency_level <= 2:
                location = UnifiedLocation(chapter=point.chapter)

                severity = UnifiedSeverity.P3
                if point.is_predictable and point.urgency_level <= 2:
                    severity = UnifiedSeverity.P2
                elif point.is_predictable:
                    severity = UnifiedSeverity.P2
                elif point.urgency_level <= 2:
                    severity = UnifiedSeverity.P3

                issue = UnifiedIssue(
                    id=f"pc_{point.chapter}_{uuid.uuid4().hex[:8]}",
                    severity=severity,
                    source=QualitySource.LLM_ANALYZER,
                    source_name="pacing_analyzer",
                    issue_type="pacing_issue",
                    title=f"节奏问题({point.tension_type}): {'可预测' if point.is_predictable else '低紧迫感'}",
                    description=f"{point.position}: {point.description}",
                    location=location,
                    evidence=point.description,
                    suggestion=point.suggestion,
                    dimension=QualityDimension.S5_PACING_CONTROL,
                    confidence=point.urgency_level / 5.0,
                    metadata={
                        "tension_type": point.tension_type,
                        "position": point.position,
                        "is_predictable": point.is_predictable,
                        "urgency_level": point.urgency_level,
                    }
                )
                issues.append(issue)
        return issues

    @classmethod
    def to_domain_report(
        cls,
        report: "PacingReport"
    ) -> DomainSpecificReport:
        """Convert to domain-specific report"""
        return DomainSpecificReport(
            report_type="pacing",
            chapter=report.chapter,
            score=report.score,
            raw_data=report.to_dict(),
        )


# Adapter registry for easy lookup
LLM_ADAPTERS = {
    "foreshadow": LLMForeshadowAdapter,
    "emotional_resonance": LLMEmotionalAdapter,
    "pacing": LLMPacingAdapter,
}
