#!/usr/bin/env python3
"""
一致性检查数据结构和Issue定义

定义一致性检查系统中使用的数据结构：
- Issue: 单个一致性问题
- ConsistencyReport: 一致性检查报告
- CheckScope: 检查范围枚举
- IssueSeverity: 问题严重程度枚举
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class IssueSeverity(Enum):
    """问题严重程度"""
    P0 = "P0"  # 致命：逻辑硬伤，影响阅读
    P1 = "P1"  # 严重：一致性冲突，需要修改
    P2 = "P2"  # 中等：轻微不一致，建议修改
    P3 = "P3"  # 提示：风格建议，不强制


class ConfidenceLevel(Enum):
    """检测置信度"""
    HIGH = "HIGH"   # 置信度>85%，可直接处理
    MEDIUM = "MED"  # 置信度60-85%，需LLM复核
    LOW = "LOW"     # 置信度<60%，人工审核


class CheckerType(Enum):
    """检查器类型"""
    CHARACTER = "character_checker"
    ITEM = "item_checker"
    TIMELINE = "timeline_checker"
    ABILITY = "ability_checker"
    PERSONALITY = "personality_checker"
    FORESHADOW = "foreshadow_checker"
    OUTLINE = "outline_checker"
    AI_GLOSS = "ai_gloss_checker"
    CHARACTER_STATE = "character_state_checker"
    SENTENCE_DIVERSITY = "sentence_diversity_checker"
    REPETITIVE_PHRASE = "repetitive_phrase_checker"
    CHAPTER_REDUNDANCY = "chapter_redundancy_checker"
    NARRATIVE_PERSPECTIVE = "narrative_perspective_checker"
    SCENE_PATTERN = "scene_pattern_repeat_checker"
    PACING = "pacing_checker"
    SCENE_TRANSITION = "scene_transition_checker"
    FORESHADOW_QUALITY = "foreshadow_quality_checker"
    CHARACTER_AGENCY = "character_agency_checker"
    TIMELINE_AGE = "timeline_age_checker"
    BATTLE_VISUALIZATION = "battle_visualization_checker"
    CROSS_CHAPTER_LOGIC = "cross_chapter_logic_checker"
    REPAIR_TRACE = "repair_trace_checker"
    GENDER_CONSISTENCY = "gender_consistency_checker"
    CAUSAL_CHAIN = "causal_chain_checker"
    SPATIAL_TRANSITION = "spatial_transition_checker"
    RELATIONSHIP_STATE = "relationship_state_checker"
    KNOWLEDGE_TRACKING = "knowledge_tracking_checker"
    DIALOGUE_ACTION = "dialogue_action_checker"
    LLM_CAUSAL_REASONING = "llm_causal_reasoning_checker"
    
    ITEM_CORE = "core_props_checker"  # CorePropsChecker - 核心物品/道具追踪
    AI_GLOSS_DIALOGUE = "dialogue_authenticity_checker"  # DialogueAuthenticityChecker - 对话AI化专项


class CheckScope(Enum):
    """检查范围"""
    ALL = "all"           # 全部8个检查器
    CRITICAL = "critical" # 仅critical级别
    IMPORTANT = "important"  # critical + important
    STANDARD = "standard"  # 标准检查


@dataclass
class IssueLocation:
    """问题位置"""
    chapter: int
    paragraph: Optional[int] = None
    line: Optional[int] = None
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None

    def __str__(self) -> str:
        parts = [f"ch{self.chapter}"]
        if self.paragraph is not None:
            parts.append(f"第{self.paragraph}段")
        if self.line is not None:
            parts.append(f"第{self.line}行")
        return "，".join(parts)


@dataclass
class Issue:
    """
    单个一致性问题

    Attributes:
        id: 问题唯一标识
        severity: 严重程度 (P0-P3)
        checker_type: 检查器类型
        issue_type: 问题类型
        title: 问题标题
        description: 问题描述
        location: 问题位置
        character: 涉及的角色的名称
        evidence: 问题依据（前文内容）
        suggestion: 修改建议
        created_at: 创建时间
    """
    id: str
    severity: IssueSeverity
    checker_type: CheckerType
    issue_type: str
    title: str
    description: str
    location: IssueLocation
    evidence: str = ""
    suggestion: str = ""
    character: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: float = 0.5  # 0.0-1.0 详细分数
    context_used: List[str] = field(default_factory=list)  # 使用的上下文
    needs_llm_review: bool = False  # 是否需LLM复核

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "severity": self.severity.value,
            "checker_type": self.checker_type.value,
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
            "character": self.character,
            "created_at": self.created_at.isoformat(),
            "confidence": self.confidence.value,
            "confidence_score": self.confidence_score,
            "context_used": self.context_used,
            "needs_llm_review": self.needs_llm_review,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Issue":
        """从字典创建"""
        location_data = data.get("location", {})
        location = IssueLocation(
            chapter=location_data.get("chapter", 0),
            paragraph=location_data.get("paragraph"),
            line=location_data.get("line"),
        )
        return cls(
            id=data["id"],
            severity=IssueSeverity(data["severity"]),
            checker_type=CheckerType(data["checker_type"]),
            issue_type=data["issue_type"],
            title=data["title"],
            description=data["description"],
            location=location,
            evidence=data.get("evidence", ""),
            suggestion=data.get("suggestion", ""),
            character=data.get("character"),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            confidence=ConfidenceLevel(data.get("confidence", "MED")),
            confidence_score=data.get("confidence_score", 0.5),
            context_used=data.get("context_used", []),
            needs_llm_review=data.get("needs_llm_review", False),
        )


@dataclass
class CheckerPerformance:
    """检查器性能统计"""
    checker_type: str
    total_detections: int = 0
    false_positive_count: int = 0
    true_positive_count: int = 0
    false_positive_rate: float = 0.0
    avg_confidence_score: float = 0.5
    last_updated: datetime = field(default_factory=datetime.now)
    is_over_threshold: bool = False  # 是否超过误报阈值

    def update(self, is_false_positive: bool, confidence_score: float = 0.5):
        """更新性能统计"""
        self.total_detections += 1
        if is_false_positive:
            self.false_positive_count += 1
        else:
            self.true_positive_count += 1
        self.false_positive_rate = self.false_positive_count / max(self.total_detections, 1)
        # 更新平均置信度分数
        self.avg_confidence_score = (
            (self.avg_confidence_score * (self.total_detections - 1) + confidence_score)
            / self.total_detections
        )
        self.last_updated = datetime.now()


@dataclass
class IssueFeedback:
    """问题反馈（用于自检）"""
    issue_id: str
    checker_type: str
    chapter_num: int
    is_false_positive: bool
    user_confirmed: bool = False
    llm_reviewed: bool = False
    llm_verdict: Optional[str] = None  # "confirmed", "false_positive", "ambiguous"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ForeshadowAlert:
    """
    伏笔预警提示

    Attributes:
        alert_type: 预警类型 (overdue, approaching, unresolved)
        thread_id: 伏笔线索ID
        content: 伏笔内容
        introduced_chapter: 引入章节
        expected_resolve_chapter: 预期解决章节
        current_chapter: 当前章节
        delay_chapters: 延迟章节数 (未到期则为0)
        severity: 严重程度
        message: 人类可读的预警消息
        created_at: 创建时间
    """
    alert_type: str
    thread_id: str
    content: str
    introduced_chapter: int
    expected_resolve_chapter: int
    current_chapter: int
    delay_chapters: int = 0
    severity: IssueSeverity = IssueSeverity.P2
    message: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "alert_type": self.alert_type,
            "thread_id": self.thread_id,
            "content": self.content,
            "introduced_chapter": self.introduced_chapter,
            "expected_resolve_chapter": self.expected_resolve_chapter,
            "current_chapter": self.current_chapter,
            "delay_chapters": self.delay_chapters,
            "severity": self.severity.value,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class CheckerResult:
    """单个检查器的检查结果"""
    checker_type: CheckerType
    issues: List[Issue] = field(default_factory=list)
    foreshadow_alerts: List[ForeshadowAlert] = field(default_factory=list)
    score: float = 100.0
    check_duration_ms: float = 0.0

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    @property
    def p0_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.P0)

    @property
    def p1_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.P1)

    @property
    def p2_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.P2)

    @property
    def p3_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.P3)


@dataclass
class QualityDimension:
    """质量维度评分"""
    s1_plot_completeness: float = 5.0   # S1 剧情完整性
    s2_logic_consistency: float = 5.0  # S2 逻辑自洽
    s3_writing_style: float = 5.0       # S3 文笔风格
    s4_emotional_resonance: float = 5.0 # S4 情感共鸣
    s5_pacing_control: float = 5.0      # S5 节奏控制
    s6_readability: float = 5.0         # S6 可读性
    s7_protagonist_charm: float = 5.0  # S7 主角魅力
    s8_character_arc: float = 5.0      # S8 人物弧光

    def to_dict(self) -> Dict[str, Any]:
        return {
            "S1": self.s1_plot_completeness,
            "S2": self.s2_logic_consistency,
            "S3": self.s3_writing_style,
            "S4": self.s4_emotional_resonance,
            "S5": self.s5_pacing_control,
            "S6": self.s6_readability,
            "S7": self.s7_protagonist_charm,
            "S8": self.s8_character_arc,
        }

    def overall_score(self) -> float:
        """计算综合评分"""
        weights = {
            "S1": 0.20, "S2": 0.20, "S3": 0.15, "S4": 0.10,
            "S5": 0.10, "S6": 0.10, "S7": 0.08, "S8": 0.07
        }
        scores = self.to_dict()
        return sum(scores[k] * weights[k] for k in weights) * 20  # 转换为100分制

    def get_dimension(self, name: str) -> float:
        """获取指定维度评分"""
        dim_map = {
            "S1": self.s1_plot_completeness,
            "S2": self.s2_logic_consistency,
            "S3": self.s3_writing_style,
            "S4": self.s4_emotional_resonance,
            "S5": self.s5_pacing_control,
            "S6": self.s6_readability,
            "S7": self.s7_protagonist_charm,
            "S8": self.s8_character_arc,
        }
        return dim_map.get(name.upper(), 5.0)


@dataclass
class ConsistencyReport:
    """
    一致性检查报告

    Attributes:
        chapter: 章节号
        check_time: 检查时间
        check_scope: 检查范围
        issues: 问题列表
        checker_results: 各检查器结果
        quality: 质量维度评分
        total_score: 综合评分
        suggestions: 修改建议
        verdict: 通过判定
        metadata: 元数据
    """
    chapter: int
    check_time: datetime = field(default_factory=datetime.now)
    check_scope: CheckScope = CheckScope.ALL
    issues: List[Issue] = field(default_factory=list)
    checker_results: List[CheckerResult] = field(default_factory=list)
    quality: QualityDimension = field(default_factory=QualityDimension)
    total_score: float = 100.0
    suggestions: List[str] = field(default_factory=list)
    verdict: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    @property
    def p0_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.P0)

    @property
    def p1_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.P1)

    @property
    def p2_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.P2)

    @property
    def p3_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.P3)

    def add_issue(self, issue: Issue):
        """添加问题"""
        self.issues.append(issue)

    def get_issues_by_severity(self, severity: IssueSeverity) -> List[Issue]:
        """按严重程度获取问题"""
        return [i for i in self.issues if i.severity == severity]

    def get_issues_by_checker(self, checker_type: CheckerType) -> List[Issue]:
        """按检查器获取问题"""
        return [i for i in self.issues if i.checker_type == checker_type]

    def make_verdict(self) -> str:
        """生成通过判定"""
        if self.p0_count > 0:
            self.verdict = "fail"
        elif self.p1_count > 2:
            self.verdict = "fail"
        elif self.total_score < 75:
            self.verdict = "review"
        elif self.total_score >= 90:
            self.verdict = "pass"
        else:
            self.verdict = "review"
        return self.verdict

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "chapter": self.chapter,
            "check_time": self.check_time.isoformat(),
            "check_scope": self.check_scope.value,
            "issue_count": self.issue_count,
            "p0_count": self.p0_count,
            "p1_count": self.p1_count,
            "p2_count": self.p2_count,
            "p3_count": self.p3_count,
            "total_score": self.total_score,
            "verdict": self.verdict,
            "issues": [i.to_dict() for i in self.issues],
            "quality": self.quality.to_dict(),
            "suggestions": self.suggestions,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConsistencyReport":
        """从字典创建"""
        report = cls(
            chapter=data["chapter"],
            check_time=datetime.fromisoformat(data["check_time"]),
            check_scope=CheckScope(data.get("check_scope", "all")),
            total_score=data.get("total_score", 100.0),
            verdict=data.get("verdict", "pending"),
            suggestions=data.get("suggestions", []),
            metadata=data.get("metadata", {}),
        )
        report.issues = [Issue.from_dict(i) for i in data.get("issues", [])]
        return report


@dataclass
class RealtimeIssue:
    """
    实时检查问题（轻量级）

    用于写作过程中的即时预警
    """
    severity: IssueSeverity
    checker_type: CheckerType
    message: str
    location: str
    quick_fix: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity.value,
            "checker_type": self.checker_type.value,
            "message": self.message,
            "location": self.location,
            "quick_fix": self.quick_fix,
        }
