#!/usr/bin/env python3
"""
Quality System Unified Interfaces

统一质量系统接口 - 兼容 rule-based checkers 和 LLM analyzers
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Protocol
from datetime import datetime


class QualitySource(Enum):
    """质量issue来源类型"""
    RULE_BASED = "rule_based"
    LLM_ANALYZER = "llm_analyzer"
    MIXED = "mixed"


class UnifiedSeverity(Enum):
    """统一严重程度"""
    P0 = "P0"  # 致命：逻辑硬伤，影响阅读
    P1 = "P1"  # 严重：一致性冲突，需要修改
    P2 = "P2"  # 中等：轻微不一致，建议修改
    P3 = "P3"  # 提示：风格建议，不强制


class QualityDimension(Enum):
    """质量维度枚举"""
    S1_PLOT_COMPLETENESS = "S1"  # 剧情完整性
    S2_LOGIC_CONSISTENCY = "S2"  # 逻辑自洽
    S3_WRITING_STYLE = "S3"      # 文笔风格
    S4_EMOTIONAL_RESONANCE = "S4"  # 情感共鸣
    S5_PACING_CONTROL = "S5"     # 节奏控制
    S6_READABILITY = "S6"        # 可读性
    S7_PROTAGONIST_CHARM = "S7"  # 主角魅力
    S8_CHARACTER_ARC = "S8"      # 人物弧光
    S9_CHARACTER_CONSISTENCY = "S9"  # 角色一致性
    S10_WORLDVIEW_CONSISTENCY = "S10"  # 世界观一致性
    S11_FORESHADOW_RECOVERY = "S11"  # 伏笔回收率


class QualityChecker(Protocol):
    """
    所有检测器实现的统一接口

    用于统一 consistency/ 和 quality/ 两套检测器体系
    """

    @property
    def name(self) -> str:
        """检测器名称"""
        ...

    @property
    def dimension(self) -> QualityDimension:
        """检测维度（S1-S11）"""
        ...

    def check(self, chapter_num: int, content: str) -> List["UnifiedIssue"]:
        """检测章节，返回问题列表"""
        ...


@dataclass
class UnifiedLocation:
    """统一位置信息"""
    chapter: int
    paragraph: Optional[int] = None
    line: Optional[int] = None
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None

    def to_simple_string(self) -> str:
        parts = [f"ch{self.chapter}"]
        if self.paragraph is not None:
            parts.append(f"p{self.paragraph}")
        if self.line is not None:
            parts.append(f"L{self.line}")
        return " ".join(parts)


@dataclass
class UnifiedIssue:
    """
    统一Issue结构 - 兼容所有检测器

    字段尽量精简，只包含所有检测器共同的字段。
    领域特定数据存储在 metadata 中。
    """
    id: str
    severity: UnifiedSeverity
    source: QualitySource
    source_name: str
    issue_type: str
    title: str
    description: str
    location: UnifiedLocation
    evidence: str = ""
    suggestion: str = ""
    dimension: Optional[QualityDimension] = None
    confidence: float = 0.5  # 0.0-1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "severity": self.severity.value,
            "source": self.source.value,
            "source_name": self.source_name,
            "issue_type": self.issue_type,
            "title": self.title,
            "description": self.description,
            "location": {
                "chapter": self.location.chapter,
                "paragraph": self.location.paragraph,
                "line": self.location.line,
            },
            "evidence": self.evidence,
            "suggestion": self.suggestion,
            "dimension": self.dimension.value if self.dimension else None,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class DomainSpecificReport:
    """LLM领域特定数据容器"""
    report_type: str  # e.g., "foreshadow", "emotional_resonance", "pacing"
    chapter: int
    score: float
    raw_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class UnifiedQualityReport:
    """
    统一质量报告 - 整合rule-based和LLM分析结果
    """
    chapter: int
    check_time: datetime = field(default_factory=datetime.now)
    issues: List[UnifiedIssue] = field(default_factory=list)
    domain_reports: List[DomainSpecificReport] = field(default_factory=list)
    dimension_scores: Dict[QualityDimension, float] = field(default_factory=dict)
    overall_score: float = 100.0
    verdict: str = "pending"  # "pass" / "review" / "fail"
    sources_checked: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_issues_by_severity(self, severity: UnifiedSeverity) -> List[UnifiedIssue]:
        return [i for i in self.issues if i.severity == severity]

    def get_issues_by_source(self, source: QualitySource) -> List[UnifiedIssue]:
        return [i for i in self.issues if i.source == source]

    def get_issues_by_dimension(self, dimension: QualityDimension) -> List[UnifiedIssue]:
        return [i for i in self.issues if i.dimension == dimension]

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    @property
    def p0_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == UnifiedSeverity.P0)

    @property
    def p1_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == UnifiedSeverity.P1)

    @property
    def p2_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == UnifiedSeverity.P2)

    @property
    def p3_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == UnifiedSeverity.P3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chapter": self.chapter,
            "check_time": self.check_time.isoformat(),
            "issue_count": self.issue_count,
            "p0_count": self.p0_count,
            "p1_count": self.p1_count,
            "p2_count": self.p2_count,
            "p3_count": self.p3_count,
            "overall_score": self.overall_score,
            "verdict": self.verdict,
            "issues": [i.to_dict() for i in self.issues],
            "domain_reports": [
                {
                    "report_type": r.report_type,
                    "chapter": r.chapter,
                    "score": r.score,
                    "timestamp": r.timestamp,
                }
                for r in self.domain_reports
            ],
            "dimension_scores": {d.value: s for d, s in self.dimension_scores.items()},
            "sources_checked": self.sources_checked,
        }

    def make_verdict(self) -> str:
        """生成判定结果"""
        if self.p0_count > 0:
            self.verdict = "fail"
        elif self.p1_count > 2:
            self.verdict = "fail"
        elif self.overall_score < 75:
            self.verdict = "review"
        elif self.overall_score >= 90:
            self.verdict = "pass"
        else:
            self.verdict = "review"
        return self.verdict
