#!/usr/bin/env python3
"""
LLM质检决策器
在PHASE_5_LLM_QUALITY中，对关键判断节点使用MiniMax进行深度分析
用于：
1. 判断问题严重性（P0/P1/P2）
2. 决定是否需要修改
3. 生成修复建议
"""

import logging
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.config.api_config_loader import get_api_config
from infra.llm_service import LLMService, LLMTask, TaskType
from infra.quality import Issue

logger = logging.getLogger(__name__)


class SeverityDecision(Enum):
    """严重性决策"""
    P0 = "P0"      # 致命问题，必须修复
    P1 = "P1"      # 重要问题，建议修复
    P2 = "P2"      # 轻微问题，可选修复


class RepairDecision(Enum):
    """修复决策"""
    REQUIRED = "required"      # 必须修复
    RECOMMENDED = "recommended"  # 建议修复
    OPTIONAL = "optional"      # 可选修复
    SKIP = "skip"              # 跳过


# RepairDecision 字符串值 → Enum 映射（解析 LLM JSON 响应时使用）
REPAIR_DECISION_MAP: Dict[str, RepairDecision] = {e.value: e for e in RepairDecision}
DEFAULT_REPAIR_DECISION = RepairDecision.OPTIONAL

# SeverityDecision 名称 → Enum 映射（解析 LLM JSON 响应时使用）
SEVERITY_DECISION_MAP: Dict[str, SeverityDecision] = {e.name: e for e in SeverityDecision}
DEFAULT_SEVERITY_DECISION = SeverityDecision.P2


@dataclass
class AnalysisResult:
    """分析结果"""
    severity: SeverityDecision
    repair_decision: RepairDecision
    reasoning: str
    repair_suggestion: str
    confidence: float  # 0.0-1.0


@dataclass
class SeverityJudgment:
    """严重性判断"""
    issue_type: str
    original_severity: str  # 原始严重性
    refined_severity: SeverityDecision
    reasoning: str


class LLMQualityAnalyzer:
    """
    LLM质检决策器

    对检测到的问题进行深度分析：
    1. 判断问题严重性是否准确
    2. 决定是否需要修复
    3. 生成具体的修复建议
    """

    SYSTEM_PROMPT = """你是一个专业的小说质量审核官。你的任务是对检测到的问题进行严重性判断和修复建议。

严重性定义：
- P0: 致命问题，会严重影响阅读体验，必须修复
  * 角色行为逻辑矛盾
  * 前后剧情矛盾
  * 世界观设定冲突
- P1: 重要问题，建议修复
  * 情感描写不够深入
  * 节奏把控不佳
  * 伏笔回收不够明显
- P2: 轻微问题，可选修复
  * 句式重复
  * AI痕迹
  * 轻微的逻辑不够严密

修复决策定义：
- required: 必须修复（P0问题）
- recommended: 建议修复（P1问题）
- optional: 可选修复（P2问题）
- skip: 跳过（误报或无意义的问题）

输出格式：
直接输出JSON对象，包含：
- severity: P0/P1/P2
- repair_decision: required/recommended/optional/skip
- reasoning: 判断理由
- repair_suggestion: 修复建议
- confidence: 判断置信度(0.0-1.0)
"""

    def __init__(self, llm_service=None):
        self._llm = llm_service or LLMService()
        self._config = get_api_config()

    def analyze_issue(
        self,
        issue: Issue,
        chapter_num: int,
        context: Optional[str] = None
    ) -> AnalysisResult:
        """
        分析单个问题

        Args:
            issue: Issue对象
            chapter_num: 章节号
            context: 上下文（可选）

        Returns:
            AnalysisResult分析结果
        """
        prompt = self._build_issue_prompt(issue, chapter_num, context)

        try:
            response = self._llm.execute(LLMTask(
                task_type=TaskType.QUALITY_ANALYSIS,
                prompt=prompt,
                system=self.SYSTEM_PROMPT,
                max_tokens=1000,
                temperature=0.3,
            ))
            return self._parse_response(response, issue)
        except Exception as e:
            logger.error(f"analyze_issue failed: {e}")
            return AnalysisResult(
                severity=SeverityDecision.P2,
                repair_decision=RepairDecision.OPTIONAL,
                reasoning=f"分析失败: {e}",
                repair_suggestion="",
                confidence=0.0,
            )

    def analyze_batch(
        self,
        issues: List[Issue],
        chapter_num: int,
        context: Optional[str] = None
    ) -> List[AnalysisResult]:
        """
        批量分析问题

        Args:
            issues: Issue列表
            chapter_num: 章节号
            context: 上下文（可选）

        Returns:
            AnalysisResult列表
        """
        results = []
        for issue in issues:
            result = self.analyze_issue(issue, chapter_num, context)
            results.append(result)
        return results

    def should_repair(self, results: List[AnalysisResult]) -> bool:
        """
        根据分析结果判断是否需要修复

        Args:
            results: AnalysisResult列表

        Returns:
            是否需要修复
        """
        for result in results:
            if result.repair_decision == RepairDecision.REQUIRED:
                return True
        return False

    def filter_issues(
        self,
        issues: List[Issue],
        chapter_num: int,
        context: Optional[str] = None
    ) -> List[Issue]:
        """
        根据分析结果过滤问题

        只返回需要修复的问题

        Args:
            issues: 原始Issue列表
            chapter_num: 章节号
            context: 上下文

        Returns:
            过滤后的Issue列表
        """
        results = self.analyze_batch(issues, chapter_num, context)

        filtered = []
        for issue, result in zip(issues, results):
            if result.repair_decision != RepairDecision.SKIP:
                filtered.append(issue)

        return filtered

    def _build_issue_prompt(
        self,
        issue: Issue,
        chapter_num: int,
        context: Optional[str]
    ) -> str:
        """构建问题分析提示词"""
        context_str = f"\n\n上下文（章节前后内容）：\n{context}" if context else ""

        return f"""分析以下章节第{chapter_num}章检测到的问题：

问题类型：{issue.checker}
问题描述：{issue.description}
位置：{issue.position}
严重性：{issue.severity}{context_str}

请判断：
1. 这个问题的严重性是否准确？
2. 是否需要修复？
3. 如何修复？

直接输出JSON对象。
"""

    def _parse_response(
        self,
        response: str,
        original_issue: Issue
    ) -> AnalysisResult:
        """解析LLM响应"""
        import json
        import re

        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)

            severity_str = data.get("severity", DEFAULT_SEVERITY_DECISION.name)
            severity = SEVERITY_DECISION_MAP.get(severity_str, DEFAULT_SEVERITY_DECISION)

            repair_str = data.get("repair_decision", DEFAULT_REPAIR_DECISION.value)
            repair = REPAIR_DECISION_MAP.get(repair_str.lower(), DEFAULT_REPAIR_DECISION)

            return AnalysisResult(
                severity=severity,
                repair_decision=repair,
                reasoning=data.get("reasoning", ""),
                repair_suggestion=data.get("repair_suggestion", ""),
                confidence=data.get("confidence", 0.5),
            )
        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            return AnalysisResult(
                severity=DEFAULT_SEVERITY_DECISION,
                repair_decision=DEFAULT_REPAIR_DECISION,
                reasoning=f"解析失败: {e}",
                repair_suggestion="",
                confidence=0.0,
            )


def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(description='LLM质检决策器')
    parser.add_argument("--chapter", type=int, required=True, help="章节号")
    parser.add_argument("--issue-file", type=str, help="问题JSON文件路径")

    args = parser.parse_args()

    analyzer = LLMQualityAnalyzer()

    if args.issue_file:
        with open(args.issue_file, "r", encoding="utf-8") as f:
            issues_data = json.load(f)
        issues = [Issue(**i) for i in issues_data]
    else:
        issues = []

    if issues:
        results = analyzer.analyze_batch(issues, args.chapter)
        for issue, result in zip(issues, results):
            print(f"\n问题: {issue.description}")
            print(f"  严重性: {result.severity.value}")
            print(f"  决策: {result.repair_decision.value}")
            print(f"  理由: {result.reasoning}")
            print(f"  建议: {result.repair_suggestion}")
            print(f"  置信度: {result.confidence:.2f}")
    else:
        print("无可分析的问题")


if __name__ == '__main__':
    main()
