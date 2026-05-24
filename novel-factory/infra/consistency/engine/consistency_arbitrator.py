#!/usr/bin/env python3
"""
混合仲裁器 - Layer 6 实现
多检查器交叉验证，模糊问题提交LLM复核
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .data_structures import Issue, IssueSeverity, ConfidenceLevel


@dataclass
class ArbitrationResult:
    """仲裁结果"""
    original_issues: List[Issue]
    resolved_issues: List[Issue]  # 经仲裁确认的问题
    ambiguous_issues: List[Issue]  # 模糊问题，需LLM复核
    false_positive_issues: List[Issue]  # 误报问题
    arbitration_summary: str
    needs_llm_review: bool = False


@dataclass
class IssueGroup:
    """问题组（相同位置的问题）"""
    location_key: str  # "chXXX_pYY" 格式
    issues: List[Issue] = field(default_factory=list)
    checker_types: List[str] = field(default_factory=list)
    severities: List[IssueSeverity] = field(default_factory=list)
    avg_confidence: float = 0.0


class ConsistencyArbitrator:
    """
    混合仲裁器

    仲裁规则：
    1. 位置分组：相同章节/段落的问题分组
    2. 多检查器确认：≥2个检查器报告相同位置的问题 → 高置信度
    3. 置信度投票：HIGH置信度issue权重高
    4. 模糊问题：置信度差异大或多个检查器冲突 → LLM复核
    """

    def __init__(self):
        self.arbitration_log = []

    def _group_issues_by_location(self, issues: List[Issue]) -> List[IssueGroup]:
        """将问题按位置分组"""
        groups: Dict[str, IssueGroup] = {}

        for issue in issues:
            # 生成位置键
            loc = issue.location
            key = f"ch{loc.chapter}"
            if loc.paragraph is not None:
                key += f"_p{loc.paragraph}"

            if key not in groups:
                groups[key] = IssueGroup(location_key=key)
            groups[key].issues.append(issue)
            groups[key].checker_types.append(issue.checker_type.value)
            groups[key].severities.append(issue.severity)

            # 计算平均置信度
            conf_map = {"HIGH": 1.0, "MEDIUM": 0.7, "LOW": 0.4}
            conf_val = conf_map.get(issue.confidence.value, 0.5)
            avg = groups[key].avg_confidence
            n = len(groups[key].issues)
            groups[key].avg_confidence = (avg * (n - 1) + conf_val) / n

        return list(groups.values())

    def _is_same_issue(self, issue1: Issue, issue2: Issue) -> bool:
        """判断两个问题是否实质相同"""
        # 相同检查器类型
        if issue1.checker_type == issue2.checker_type:
            return True
        # 不同检查器但相同角色和相似类型
        if issue1.character and issue2.character:
            if issue1.character == issue2.character:
                return True
        return False

    def _get_severity_priority(self, severity: IssueSeverity) -> int:
        """获取严重性优先级（数字越大越严重）"""
        priority_map = {
            IssueSeverity.P0: 4,
            IssueSeverity.P1: 3,
            IssueSeverity.P2: 2,
            IssueSeverity.P3: 1,
        }
        return priority_map.get(severity, 0)

    def _arbitrate_group(self, group: IssueGroup) -> Tuple[List[Issue], List[Issue], List[Issue]]:
        """仲裁一个问题组"""
        resolved = []
        ambiguous = []
        false_positives = []

        # 规则1：多检查器确认（相同位置≥2个检查器报告）→ 高置信度
        unique_checkers = set(group.checker_types)
        if len(unique_checkers) >= 2:
            # 多个检查器确认，这是个真实问题
            # 取最高严重性
            max_priority = max(self._get_severity_priority(s) for s in group.severities)
            max_severity = None
            for s in group.severities:
                if self._get_severity_priority(s) == max_priority:
                    for issue in group.issues:
                        if issue.severity == s and issue not in resolved:
                            resolved.append(issue)
                            max_severity = s
                            break
                    break
            return resolved, ambiguous, false_positives

        # 规则2：单检查器，查看置信度
        issue = group.issues[0]
        if issue.confidence == ConfidenceLevel.HIGH:
            resolved.append(issue)
        elif issue.confidence == ConfidenceLevel.LOW:
            # 低置信度 → 标记为模糊，需要LLM复核
            issue.needs_llm_review = True
            ambiguous.append(issue)
        else:
            # MEDIUM置信度
            if issue.confidence_score >= 0.75:
                resolved.append(issue)
            elif issue.confidence_score <= 0.4:
                issue.needs_llm_review = True
                ambiguous.append(issue)
            else:
                ambiguous.append(issue)

        return resolved, ambiguous, false_positives

    def arbitrate(self, issues: List[Issue]) -> ArbitrationResult:
        """
        仲裁一组问题

        Args:
            issues: 从多个检查器收集的问题列表

        Returns:
            ArbitrationResult: 包含已解决、模糊和误报问题
        """
        if not issues:
            return ArbitrationResult(
                original_issues=[],
                resolved_issues=[],
                ambiguous_issues=[],
                false_positive_issues=[],
                arbitration_summary="无问题可仲裁"
            )

        # 按位置分组
        groups = self._group_issues_by_location(issues)

        all_resolved = []
        all_ambiguous = []
        all_false_positives = []

        for group in groups:
            resolved, ambiguous, false_pos = self._arbitrate_group(group)
            all_resolved.extend(resolved)
            all_ambiguous.extend(ambiguous)
            all_false_positives.extend(false_pos)

        # 生成摘要
        summary = f"仲裁完成：{len(all_resolved)}个已确认，{len(all_ambiguous)}个需LLM复核，{len(all_false_positives)}个误报"

        result = ArbitrationResult(
            original_issues=issues,
            resolved_issues=all_resolved,
            ambiguous_issues=all_ambiguous,
            false_positive_issues=all_false_positives,
            arbitration_summary=summary,
            needs_llm_review=len(all_ambiguous) > 0
        )

        # 记录日志
        self.arbitration_log.append({
            "timestamp": datetime.now().isoformat(),
            "original_count": len(issues),
            "resolved_count": len(all_resolved),
            "ambiguous_count": len(all_ambiguous),
            "false_positive_count": len(all_false_positives)
        })

        return result

    def get_arbitration_log(self) -> List[Dict[str, Any]]:
        """获取仲裁日志"""
        return self.arbitration_log