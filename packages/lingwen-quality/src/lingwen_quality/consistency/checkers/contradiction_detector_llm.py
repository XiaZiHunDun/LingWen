"""LLMCausalReasoner — LLM 因果推理检测器（拆分自 contradiction_detector.py）。

通过 LLM 检测复杂的、需要推理的因果/时间/属性/关系矛盾。

下游消费者统一从 ``lingwen_quality.consistency.checkers.contradiction_detector``
导入（re-export），保持兼容性。
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from .attribute_comparer import Contradiction

logger = logging.getLogger(__name__)


class LLMCausalReasoner:
    """LLM因果推理检测器

    使用LLM检测复杂的、需推理的因果矛盾
    """

    def __init__(self, llm_service=None, config: Optional[Dict[str, Any]] = None):
        self.llm_service = llm_service
        self.config = config or {}

    async def detect(
        self,
        chapter_num: int,
        chapter_content: str,
        context: Dict[str, Any],
    ) -> List[Contradiction]:
        """使用LLM检测矛盾"""
        if not self.llm_service:
            logger.warning("LLM服务未配置，跳过LLM检测")
            return []

        # 准备prompt
        prompt = self._build_prompt(chapter_num, chapter_content, context)

        try:
            # 调用LLM
            response = await self.llm_service.generate(prompt)
            return self._parse_response(response, chapter_num)
        except Exception as e:
            logger.error(f"LLM检测失败: {e}")
            return []

    def _build_prompt(
        self,
        chapter_num: int,
        chapter_content: str,
        context: Dict[str, Any],
    ) -> str:
        """构建检测prompt"""
        # 获取相关段落
        related_chunks = context.get("related_chunks", [])
        chunks_text = "\n\n".join(
            [f"章节{ch.get('chapter', 0)}: {ch.get('content', '')[:500]}" for ch in related_chunks[:5]]
        )

        prompt = f"""请检查以下小说片段是否存在矛盾。

重点检查：
1. 时间矛盾：时间线是否前后一致？
2. 属性矛盾：角色外貌/性格/能力描述是否一致？
3. 因果矛盾：事件是否有合理的前因后果？
4. 关系矛盾：角色关系描述是否前后一致？

相关章节片段：
{chunks_text}

当前章节（第{chapter_num}章）：
{chapter_content[:2000]}

如果发现矛盾，请用以下JSON格式返回：
{{
    "contradictions": [
        {{
            "type": "time|attribute|causal|relationship",
            "severity": "P0|P1|P2",
            "description": "矛盾描述",
            "evidence": ["证据1", "证据2"],
            "suggestion": "修复建议"
        }}
    ]
}}

如果没有发现矛盾，返回空数组：{{"contradictions": []}}
"""
        return prompt

    def _parse_response(self, response: str, chapter_num: int) -> List[Contradiction]:
        """解析LLM响应"""
        contradictions = []

        try:
            # 尝试提取JSON
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                data = json.loads(json_match.group(0))
                for item in data.get("contradictions", []):
                    contradictions.append(
                        Contradiction(
                            entity_name="LLM_DETECTED",
                            attribute_name=item.get("type", "unknown"),
                            values=[],
                            severity=item.get("severity", "P2"),
                            contradiction_type=item.get("type", "unknown"),
                            description=item.get("description", ""),
                            suggestion=item.get("suggestion", ""),
                        )
                    )
        except Exception as e:
            logger.error(f"解析LLM响应失败: {e}")

        return contradictions


__all__ = ["LLMCausalReasoner"]
