#!/usr/bin/env python3
"""
质量审稿 Agent — 对章节内容进行全面的质量检查

Usage:
    from lingwen_core.agents.agents.quality_reviewer import QualityReviewer

    agent = QualityReviewer(router=router)
    findings = agent.run({"chapter_content": content, "story_contract": contract})
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
class QualityFinding:
    """质量审稿发现项

    Attributes:
        category: 类别（如 "plot", "character", "style", "grammar", "pacing"）
        severity: 严重程度
        description: 描述
        location: 位置
        suggestion: 建议
    """
    category: str
    severity: str
    description: str
    location: str = ""
    suggestion: str = ""


class QualityReviewer(AgentBase):
    """质量审稿 Agent

    对章节内容进行全面的质量检查，包括：
    - 情节逻辑: 检查情节发展和逻辑一致性
    - 角色表现: 检查角色行为是否合理
    - 文笔风格: 检查语言表达质量
    - 节奏把控: 检查叙事节奏
    - 结构完整性: 检查章节结构

    Attributes:
        router: AI Router 实例
    """

    SYSTEM_PROMPT = (
        "你是一位专业的文学质量审稿编辑。请对章节内容进行全面质量检查，"
        "包括情节逻辑、角色表现、文笔风格、节奏把控和结构完整性。"
        "请以结构化 JSON 格式输出审稿结果。"
    )

    # 质量检查维度
    DIMENSIONS = [
        "plot",       # 情节逻辑
        "character",  # 角色表现
        "style",      # 文笔风格
        "pacing",     # 节奏把控
        "structure",  # 结构完整性
        "grammar",    # 语法错误
    ]

    def __init__(self, router: Optional['AIRouter'] = None):
        """初始化质量审稿 Agent

        Args:
            router: AI Router 实例
        """
        super().__init__(router)

    def run(self, context: Dict[str, Any]) -> List[QualityFinding]:
        """执行全面质量检查

        Args:
            context: 上下文数据，必须包含:
                - chapter_content: 章节内容
                - story_contract: 故事契约（可选）
                - world_model: 世界模型（可选）

        Returns:
            发现项列表
        """
        chapter_content = context.get("chapter_content", "")
        story_contract = context.get("story_contract", {})
        world_model = context.get("world_model", {})

        if not chapter_content:
            logger.warning("QualityReviewer: no chapter content provided")
            return []

        if self._fallback_mode:
            logger.info("QualityReviewer: fallback mode, returning empty findings")
            return []


        all_findings: List[QualityFinding] = []

        # 按维度逐一检查，每个维度独立调用 LLM
        for dimension in self.DIMENSIONS:
            logger.info("QualityReviewer: checking dimension '%s'", dimension)

            dimension_prompt = self._build_dimension_prompt(
                dimension, chapter_content, story_contract, world_model
            )

            try:
                response = self.chat(
                    dimension_prompt,
                    system=self.SYSTEM_PROMPT,
                    temperature=0.3,
                )
                data = self._parse_json_response(response)
                raw_findings = data.get("findings", [])
            except Exception as e:
                logger.error(
                    "QualityReviewer: dimension '%s' check failed: %s", dimension, e
                )
                continue

            for f in raw_findings:
                all_findings.append(QualityFinding(
                    category=f.get("category", dimension),
                    severity=f.get("severity", "minor"),
                    description=f.get("description", ""),
                    location=f.get("location", ""),
                    suggestion=f.get("suggestion", ""),
                ))

        logger.info(
            "QualityReviewer: completed, %d findings across %d dimensions",
            len(all_findings), len(self.DIMENSIONS),
        )

        return all_findings

    def _build_dimension_prompt(
        self,
        dimension: str,
        chapter_content: str,
        story_contract: Dict[str, Any],
        world_model: Dict[str, Any],
    ) -> str:
        """构建特定维度的审稿提示

        Args:
            dimension: 质量维度
            chapter_content: 章节内容
            story_contract: 故事契约
            world_model: 世界模型

        Returns:
            格式化的提示文本
        """
        import json

        dimension_descriptions = {
            "plot": "检查情节发展是否逻辑自洽，是否有情节漏洞，转折是否合理",
            "character": "检查角色行为是否符合其性格设定，对话是否在角色",
            "style": "检查文笔风格是否统一，语言表达是否优美、准确",
            "pacing": "检查叙事节奏是否得当，是否有拖沓或过快的问题",
            "structure": "检查章节结构是否完整，开头、发展、高潮、结尾是否清晰",
            "grammar": "检查语法错误、错别字、标点符号使用",
        }

        prompt = (
            f"请对以下章节内容进行 **{dimension}** 维度的质量检查。\n"
            f"检查要点: {dimension_descriptions.get(dimension, '全面检查')}\n\n"
        )

        if story_contract:
            prompt += (
                f"=== 故事契约 ===\n"
                f"{json.dumps(story_contract, ensure_ascii=False, indent=2)}\n\n"
            )

        if world_model:
            prompt += (
                f"=== 世界模型 ===\n"
                f"{json.dumps(world_model, ensure_ascii=False, indent=2)}\n\n"
            )

        prompt += (
            f"=== 章节内容 ===\n"
            f"{chapter_content}\n\n"
            f"请以 JSON 格式输出发现项:\n"
            f'{{"findings": [{{"category": "{dimension}", "severity": "critical|major|minor|info", '
            f'"description": "描述", "location": "位置", "suggestion": "建议"}}]}}'
        )

        return prompt

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
