#!/usr/bin/env python3
"""
写审分离流程 — 独立审稿会话模块

提供 ReviewerSession 类，管理独立的审稿 AI 会话，与作者写作会话完全隔离。
审稿人无权访问作者的 CLAIM 上下文，仅基于故事契约和世界模型进行独立审稿。

核心设计原则:
- 审稿会话与作者会话完全隔离，使用独立的 AI Router 实例
- 最多 3 轮审稿循环，每轮都有 STOP 条件
- 返回结构化的 ReviewResult，包含发现项和建议修复

Usage:
    from infra.agent_system.reviewer import ReviewerSession, review_chapter

    reviewer = ReviewerSession(router=review_router)
    result = reviewer.review(chapter_content, story_contract, world_model)
    # 或使用便捷函数
    result = review_chapter(chapter_content, story_contract, world_model, router=review_router)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ...ai_service.router import AIRouter

logger = logging.getLogger(__name__)

# 审稿循环上限
MAX_REVIEW_CYCLES = 3

# STOP 条件：当发现项数量低于此阈值时，停止审稿
STOP_THRESHOLD = 0


@dataclass
class ReviewFinding:
    """单条审稿发现项

    Attributes:
        category: 发现项类别（如 "plot_hole", "character_inconsistency", "style_issue"）
        severity: 严重程度（"critical", "major", "minor", "info"）
        description: 发现项描述
        location: 问题所在位置描述（如 "第3段"）
        suggested_fix: 建议修复方案
    """
    category: str
    severity: str
    description: str
    location: str = ""
    suggested_fix: str = ""

    def to_dict(self) -> Dict[str, str]:
        """转换为字典"""
        return {
            "category": self.category,
            "severity": self.severity,
            "description": self.description,
            "location": self.location,
            "suggested_fix": self.suggested_fix,
        }


@dataclass
class ReviewResult:
    """审稿结果

    Attributes:
        passed: 是否通过审稿（无 critical 发现项）
        findings: 发现项列表
        cycles_used: 使用的审稿轮数
        summary: 审稿总结
        suggested_fixes: 建议修复列表
    """
    passed: bool = True
    findings: List[ReviewFinding] = field(default_factory=list)
    cycles_used: int = 0
    summary: str = ""
    suggested_fixes: List[str] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        """critical 级别发现项数量"""
        return sum(1 for f in self.findings if f.severity == "critical")

    @property
    def total_findings(self) -> int:
        """总发现项数量"""
        return len(self.findings)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "passed": self.passed,
            "findings": [f.to_dict() for f in self.findings],
            "cycles_used": self.cycles_used,
            "summary": self.summary,
            "suggested_fixes": self.suggested_fixes,
            "critical_count": self.critical_count,
            "total_findings": self.total_findings,
        }


class ReviewerSession:
    """独立审稿会话

    管理一个与作者写作会话完全隔离的审稿 AI 会话。
    审稿人无权访问作者的 CLAIM 上下文，仅基于故事契约和世界模型进行独立审稿。

    Attributes:
        router: AI Router 实例（审稿专用，不应与作者共用）
        max_cycles: 最大审稿循环数（默认 3）
        stop_threshold: 发现项数量低于此值时停止（默认 0）
    """

    REVIEW_SYSTEM_PROMPT = (
        "你是一位严格的文学审稿编辑。你的职责是独立审阅章节内容，找出逻辑漏洞、"
        "角色不一致、风格问题和其他写作缺陷。\n\n"
        "审稿标准:\n"
        "1. 情节一致性: 检查是否与故事契约一致\n"
        "2. 角色一致性: 检查角色行为、性格、关系是否前后一致\n"
        "3. 世界观一致性: 检查是否违反已建立的世界规则\n"
        "4. 文笔质量: 检查语言表达、节奏、结构\n\n"
        "输出格式: 只输出 JSON 格式的审稿结果，不要包含任何其他文字。"
    )

    def __init__(
        self,
        router: Optional['AIRouter'] = None,
        max_cycles: int = MAX_REVIEW_CYCLES,
        stop_threshold: int = STOP_THRESHOLD,
    ):
        """初始化审稿会话

        Args:
            router: AI Router 实例。如果为 None，则处于 fallback 模式。
            max_cycles: 最大审稿循环数
            stop_threshold: 发现项数量低于此值时停止审稿循环
        """
        self._router = router
        self._fallback_mode = router is None
        self.max_cycles = max_cycles
        self.stop_threshold = stop_threshold
        self._cycle_count = 0

    @property
    def is_available(self) -> bool:
        """检查审稿会话是否可用"""
        return not self._fallback_mode and self._router is not None

    @property
    def cycles_used(self) -> int:
        """已使用的审稿轮数"""
        return self._cycle_count

    def review(
        self,
        chapter_content: str,
        story_contract: Dict[str, Any],
        world_model: Dict[str, Any],
    ) -> ReviewResult:
        """对章节内容进行独立审稿

        Args:
            chapter_content: 章节内容文本
            story_contract: 故事契约（包含情节大纲、角色设定等）
            world_model: 世界模型（包含世界观规则、设定等）

        Returns:
            ReviewResult: 审稿结果，包含发现项和建议修复
        """
        self._cycle_count = 0
        all_findings: List[ReviewFinding] = []
        summary = ""

        if self._fallback_mode:
            logger.warning("ReviewerSession: fallback mode, returning empty review result")
            return ReviewResult(
                passed=True,
                findings=[],
                cycles_used=0,
                summary="[FALLBACK] Reviewer not initialized. No review performed.",
                suggested_fixes=[],
            )

        # 审稿循环：最多 max_cycles 轮
        for cycle in range(1, self.max_cycles + 1):
            self._cycle_count = cycle
            logger.info("Review cycle %d/%d", cycle, self.max_cycles)

            # 构建本轮审稿提示
            prompt = self._build_review_prompt(
                chapter_content, story_contract, world_model, cycle, all_findings
            )

            try:
                response = self._router.generate(
                    prompt=prompt,
                    system=self.REVIEW_SYSTEM_PROMPT,
                    temperature=0.3,
                    max_tokens=2048,
                )
            except Exception as e:
                logger.error("Review cycle %d failed: %s", cycle, e)
                # 如果审稿调用失败，保留已收集的发现项并返回
                break

            # 解析审稿响应
            cycle_findings, cycle_summary = self._parse_review_response(response)
            all_findings.extend(cycle_findings)

            if cycle_summary:
                summary = cycle_summary

            # STOP 条件：如果本轮没有发现新的 critical/major 问题，停止
            if len(cycle_findings) <= self.stop_threshold:
                logger.info(
                    "Review stopped at cycle %d: no new findings (threshold=%d)",
                    cycle, self.stop_threshold,
                )
                break

            # STOP 条件：如果连续两轮发现项相同，说明审稿已收敛
            if cycle >= 2:
                # 简单检查：本轮发现的类别是否与上一轮完全一致
                prev_categories = {f.category for f in all_findings[:-len(cycle_findings)]}
                curr_categories = {f.category for f in cycle_findings}
                if curr_categories.issubset(prev_categories):
                    logger.info(
                        "Review stopped at cycle %d: findings converged", cycle
                    )
                    break

        # 判定是否通过：无 critical 发现项即为通过
        has_critical = any(f.severity == "critical" for f in all_findings)
        passed = not has_critical

        if not passed:
            logger.warning(
                "Review NOT passed: %d critical finding(s) out of %d total",
                sum(1 for f in all_findings if f.severity == "critical"),
                len(all_findings),
            )

        suggested_fixes = [
            f.suggested_fix for f in all_findings if f.suggested_fix
        ]

        return ReviewResult(
            passed=passed,
            findings=all_findings,
            cycles_used=self._cycle_count,
            summary=summary,
            suggested_fixes=suggested_fixes,
        )

    def _build_review_prompt(
        self,
        chapter_content: str,
        story_contract: Dict[str, Any],
        world_model: Dict[str, Any],
        cycle: int,
        previous_findings: List[ReviewFinding],
    ) -> str:
        """构建审稿提示

        Args:
            chapter_content: 章节内容
            story_contract: 故事契约
            world_model: 世界模型
            cycle: 当前审稿轮次
            previous_findings: 前几轮发现项

        Returns:
            格式化的审稿提示
        """
        import json

        prompt_parts = [
            "请审阅以下章节内容，对照故事契约和世界模型，找出所有问题。",
            "",
            "=== 故事契约 ===",
            json.dumps(story_contract, ensure_ascii=False, indent=2),
            "",
            "=== 世界模型 ===",
            json.dumps(world_model, ensure_ascii=False, indent=2),
            "",
            "=== 章节内容 ===",
            chapter_content,
        ]

        if cycle > 1 and previous_findings:
            prompt_parts.extend([
                "",
                f"=== 第 {cycle} 轮审稿（前几轮已发现 {len(previous_findings)} 个问题）===",
                "请在前几轮基础上，深入检查是否还有遗漏的问题。",
                "已发现问题类别: " + ", ".join(
                    sorted(set(f.category for f in previous_findings))
                ),
            ])

        prompt_parts.extend([
            "",
            "请以 JSON 格式输出审稿结果:",
            '{',
            '  "findings": [',
            '    {"category": "类别", "severity": "critical|major|minor|info", "description": "描述", "location": "位置", "suggested_fix": "建议修复"}',
            '  ],',
            '  "summary": "审稿总结"',
            '}',
        ])

        return "\n".join(prompt_parts)

    def _parse_review_response(
        self, response: str
    ) -> tuple[List[ReviewFinding], str]:
        """解析审稿响应

        Args:
            response: AI 返回的审稿响应文本

        Returns:
            (发现项列表, 总结文本) 元组
        """
        import json
        import re

        findings: List[ReviewFinding] = []
        summary = ""

        # 尝试提取 JSON 块
        json_match = re.search(
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL
        )

        if not json_match:
            logger.warning("Failed to extract JSON from review response: %s", response[:200])
            return findings, summary

        try:
            data = json.loads(json_match.group(0))
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse review JSON: %s", e)
            return findings, summary

        raw_findings = data.get("findings", [])
        summary = data.get("summary", "")

        for f in raw_findings:
            finding = ReviewFinding(
                category=f.get("category", "unknown"),
                severity=f.get("severity", "minor"),
                description=f.get("description", ""),
                location=f.get("location", ""),
                suggested_fix=f.get("suggested_fix", ""),
            )
            findings.append(finding)

        return findings, summary

    def reset(self) -> None:
        """重置审稿会话状态"""
        self._cycle_count = 0


def review_chapter(
    chapter_content: str,
    story_contract: Dict[str, Any],
    world_model: Dict[str, Any],
    router: Optional['AIRouter'] = None,
) -> ReviewResult:
    """便捷函数：独立审阅一个章节

    使用独立的 ReviewerSession 进行审稿，与作者写作会话完全隔离。

    Args:
        chapter_content: 章节内容文本
        story_contract: 故事契约
        world_model: 世界模型
        router: AI Router 实例（可选）

    Returns:
        ReviewResult: 审稿结果
    """
    session = ReviewerSession(router=router)
    return session.review(chapter_content, story_contract, world_model)
