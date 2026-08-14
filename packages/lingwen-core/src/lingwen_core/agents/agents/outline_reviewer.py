#!/usr/bin/env python3
"""
大纲审稿 Agent — 检查大纲是否与故事契约一致

Usage:
    from lingwen_core.agents.agents.outline_reviewer import OutlineReviewer

    agent = OutlineReviewer(router=router)
    findings = agent.run({"outline": outline, "story_contract": contract})
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .base import AgentBase

if TYPE_CHECKING:
    from .....ai_service.router import AIRouter

logger = logging.getLogger(__name__)


@dataclass
class OutlineFinding:
    """大纲审稿发现项

    Attributes:
        issue: 问题描述
        severity: 严重程度（"critical", "major", "minor"）
        contract_section: 相关的故事契约章节
        suggestion: 修改建议
    """
    issue: str
    severity: str = "minor"
    contract_section: str = ""
    suggestion: str = ""


class OutlineReviewer(AgentBase):
    """大纲审稿 Agent

    检查创作大纲是否与故事契约一致，包括：
    - 情节主线是否与契约一致
    - 角色弧光是否按契约发展
    - 章节分布是否符合契约规划

    Attributes:
        router: AI Router 实例
    """

    SYSTEM_PROMPT = (
        "你是一位大纲审稿专家。你的职责是检查创作大纲是否与故事契约一致。"
        "请严格对照故事契约，找出大纲中的偏差和遗漏。"
    )

    def __init__(self, router: Optional['AIRouter'] = None):
        """初始化大纲审稿 Agent

        Args:
            router: AI Router 实例
        """
        super().__init__(router)

    def run(self, context: Dict[str, Any]) -> List[OutlineFinding]:
        """执行大纲审稿

        Args:
            context: 上下文数据，必须包含:
                - outline: 大纲内容
                - story_contract: 故事契约

        Returns:
            发现项列表
        """
        outline = context.get("outline", "")
        story_contract = context.get("story_contract", {})

        if not outline:
            logger.warning("OutlineReviewer: no outline provided")
            return []

        if self._fallback_mode:
            logger.info("OutlineReviewer: fallback mode, returning empty findings")
            return []

        import json

        prompt = (
            f"请审阅以下大纲，对照故事契约检查一致性。\n\n"
            f"=== 故事契约 ===\n"
            f"{json.dumps(story_contract, ensure_ascii=False, indent=2)}\n\n"
            f"=== 大纲 ===\n"
            f"{outline}\n\n"
            f"请以 JSON 格式输出发现项:\n"
            f'{{"findings": [{{"issue": "问题", "severity": "critical|major|minor", '
            f'"contract_section": "相关契约章节", "suggestion": "建议"}}]}}'
        )

        try:
            response = self.chat(prompt, system=self.SYSTEM_PROMPT, temperature=0.3)
            data = self._parse_json_response(response)
            raw_findings = data.get("findings", [])
        except Exception as e:
            logger.error("OutlineReviewer: LLM call failed: %s", e)
            return []

        return [
            OutlineFinding(
                issue=f.get("issue", ""),
                severity=f.get("severity", "minor"),
                contract_section=f.get("contract_section", ""),
                suggestion=f.get("suggestion", ""),
            )
            for f in raw_findings
        ]

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析 JSON 响应"""
        import json
        import re

        json_match = re.search(
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL
        )
        if json_match:
            return json.loads(json_match.group(0))
        return {}