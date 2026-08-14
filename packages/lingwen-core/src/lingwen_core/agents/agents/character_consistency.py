#!/usr/bin/env python3
"""
角色一致性 Agent — 检查新建角色是否与已有角色设定冲突

Usage:
    from lingwen_core.agents.agents.character_consistency import CharacterConsistencyAgent

    agent = CharacterConsistencyAgent(router=router)
    findings = agent.run({"new_character": new_char, "existing_characters": existing})
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
class CharacterConsistencyFinding:
    """角色一致性发现项

    Attributes:
        character_name: 相关角色名称
        conflict_type: 冲突类型（如 "name_conflict", "personality_overlap", "role_duplicate"）
        description: 冲突描述
        severity: 严重程度
        suggestion: 修改建议
    """
    character_name: str
    conflict_type: str
    description: str
    severity: str = "minor"
    suggestion: str = ""


class CharacterConsistencyAgent(AgentBase):
    """角色一致性检查 Agent

    检查新建角色是否与已有角色设定存在冲突，包括：
    - 名字冲突（重名或过于相似）
    - 性格重叠（两个角色定位过于相似）
    - 角色重复（在故事中扮演的功能重复）

    Attributes:
        router: AI Router 实例
    """

    SYSTEM_PROMPT = (
        "你是一位角色设定专家。你的职责是检查新角色是否与已有角色设定存在冲突。"
        "请检查名字冲突、性格重叠、角色功能重复等问题。"
    )

    def __init__(self, router: Optional['AIRouter'] = None):
        """初始化角色一致性 Agent

        Args:
            router: AI Router 实例
        """
        super().__init__(router)

    def run(self, context: Dict[str, Any]) -> List[CharacterConsistencyFinding]:
        """执行角色一致性检查

        Args:
            context: 上下文数据，必须包含:
                - new_character: 新角色设定
                - existing_characters: 已有角色列表

        Returns:
            发现项列表
        """
        new_character = context.get("new_character", {})
        existing_characters = context.get("existing_characters", [])

        if not new_character:
            logger.warning("CharacterConsistencyAgent: no new character provided")
            return []

        if self._fallback_mode:
            logger.info("CharacterConsistencyAgent: fallback mode, returning empty findings")
            return []

        # 先做简单的规则检查（不需要 LLM）
        findings = self._rule_based_check(new_character, existing_characters)

        # 如果已经发现 critical 问题，不需要 LLM 进一步检查
        if any(f.severity == "critical" for f in findings):
            return findings

        # LLM 深度检查
        import json

        prompt = (
            f"请检查以下新角色是否与已有角色设定存在冲突。\n\n"
            f"=== 新角色 ===\n"
            f"{json.dumps(new_character, ensure_ascii=False, indent=2)}\n\n"
            f"=== 已有角色 ===\n"
            f"{json.dumps(existing_characters, ensure_ascii=False, indent=2)}\n\n"
            f"请以 JSON 格式输出发现项:\n"
            f'{{"findings": [{{"character_name": "角色名", "conflict_type": "冲突类型", '
            f'"description": "描述", "severity": "critical|major|minor", "suggestion": "建议"}}]}}'
        )

        try:
            response = self.chat(prompt, system=self.SYSTEM_PROMPT, temperature=0.3)
            data = self._parse_json_response(response)
            raw_findings = data.get("findings", [])
        except Exception as e:
            logger.error("CharacterConsistencyAgent: LLM call failed: %s", e)
            return findings

        llm_findings = [
            CharacterConsistencyFinding(
                character_name=f.get("character_name", ""),
                conflict_type=f.get("conflict_type", "unknown"),
                description=f.get("description", ""),
                severity=f.get("severity", "minor"),
                suggestion=f.get("suggestion", ""),
            )
            for f in raw_findings
        ]
        findings.extend(llm_findings)

        return findings

    def _rule_based_check(
        self,
        new_character: Dict[str, Any],
        existing_characters: List[Dict[str, Any]],
    ) -> List[CharacterConsistencyFinding]:
        """基于规则的快速检查（不需要 LLM）

        Args:
            new_character: 新角色设定
            existing_characters: 已有角色列表

        Returns:
            发现项列表
        """
        findings: List[CharacterConsistencyFinding] = []

        new_name = new_character.get("name", "").strip().lower()
        if not new_name:
            return findings

        for existing in existing_characters:
            existing_name = existing.get("name", "").strip().lower()

            # 名字完全相同的冲突
            if new_name == existing_name:
                findings.append(CharacterConsistencyFinding(
                    character_name=new_name,
                    conflict_type="name_conflict",
                    description=f"角色名 '{new_name}' 与已有角色 '{existing_name}' 完全相同",
                    severity="critical",
                    suggestion=f"请为角色使用不同的名字",
                ))

            # 名字高度相似的冲突（包含关系）
            elif new_name in existing_name or existing_name in new_name:
                findings.append(CharacterConsistencyFinding(
                    character_name=new_name,
                    conflict_type="name_similarity",
                    description=f"角色名 '{new_name}' 与已有角色 '{existing_name}' 高度相似",
                    severity="major",
                    suggestion=f"建议修改角色名以避免读者混淆",
                ))

        return findings

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