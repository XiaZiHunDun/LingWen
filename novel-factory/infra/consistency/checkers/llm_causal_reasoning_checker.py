#!/usr/bin/env python3
"""
LLM辅助的复杂因果推理检测器

用于检测规则检测器无法处理的复杂逻辑矛盾：
1. 因果链断裂（复杂因果关系）
2. 情感反应比例失调
3. 物理可能性问题
4. 世界规则矛盾

这个检测器调用LLM来分析文本中的复杂逻辑矛盾。
由于LLM调用可能较慢或昂贵，它设计为可配置启用/禁用。
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from infra.consistency.engine.data_structures import (
    CheckerType,
    ConfidenceLevel,
    Issue,
    IssueLocation,
    IssueSeverity,
)

from .base_checker import BaseChecker

logger = logging.getLogger(__name__)


class LLMCausalReasoningChecker(BaseChecker):
    """LLM辅助的复杂因果推理检测器

    用于检测规则检测器无法处理的复杂逻辑矛盾：
    1. 因果链断裂（A做了X，但Y没有发生相应改变，且无法用简单规则判断）
    2. 情感反应不符合人物关系（刚认识的人死亡却极度悲伤）
    3. 物理不可能（修真世界中出现违反物理规则的情况）
    4. 世界规则矛盾（前面说不能飞，后面却飞了）

    只报告真正的逻辑矛盾，不报告：
    - 伏笔（有意隐瞒信息）
    - 视角切换造成的表面矛盾
    - 夸张修辞
    - 尚未发生但可能发生的矛盾
    """
    _checker_type = CheckerType.LLM_CAUSAL_REASONING


    SYSTEM_PROMPT = """你是一个小说一致性检测专家。
    检测以下文本是否存在以下类型的逻辑矛盾：
    1. 因果链断裂（A做了X，但Y没有发生相应改变，且无法用简单规则判断）
    2. 情感反应不符合人物关系（刚认识的人死亡却极度悲伤）
    3. 物理不可能（修真世界中出现违反物理规则的情况）
    4. 世界规则矛盾（前面说不能飞，后面却飞了）

    只报告真正的逻辑矛盾，不报告：
    - 伏笔（有意隐瞒信息）
    - 视角切换造成的表面矛盾
    - 夸张修辞
    - 尚未发生但可能发生的矛盾

    输出格式（JSON）：
    {
        "contradictions": [
            {
                "type": "causal_chain|emotional_proportion|physical_impossible|world_rule_violation",
                "location": "具体段落",
                "description": "矛盾描述",
                "evidence": "证据",
                "suggestion": "修复建议"
            }
        ]
    }

    如果没有发现矛盾，返回空列表。
    """

    def __init__(self, enabled: bool = True):
        """
        初始化LLM因果推理检测器

        Args:
            enabled: 是否启用LLM调用，默认为True
        """
        super().__init__(self._checker_type)
        self.enabled = enabled

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        执行检查

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 上下文信息（角色档案、世界规则、前文摘要等）

        Returns:
            Issue列表
        """
        if not self.enabled:
            return []

        issues = []

        # 构建prompt
        prompt = self._build_prompt(chapter_content, context or {})

        # 调用LLM
        try:
            result = self._call_llm(prompt)
            contradictions = result.get("contradictions", [])

            for c in contradictions:
                issues.append(self._create_issue(c, chapter_num))
        except Exception as e:
            # LLM调用失败时跳过，不阻塞其他检测器
            logger.warning(f"LLM因果推理检测失败（章节{chapter_num}）: {e}")
            pass

        return issues

    def _build_prompt(self, chapter_content: str, context: Dict[str, Any]) -> str:
        """
        构建prompt

        Args:
            chapter_content: 章节内容
            context: 上下文信息

        Returns:
            构建好的prompt
        """
        character_profiles = context.get("character_profiles", {})
        world_rules = context.get("world_rules", "")
        previous_summary = context.get("previous_summary", "")

        prompt = f"""
当前章节:
{chapter_content}

角色设定:
{self._format_character_profiles(character_profiles)}

世界规则:
{world_rules if world_rules else "无"}

前文摘要:
{previous_summary if previous_summary else "无"}

请检测上述场景中的逻辑矛盾，以JSON格式输出。
"""
        return prompt

    def _format_character_profiles(self, profiles: Dict[str, Any]) -> str:
        """格式化角色档案"""
        if not profiles:
            return "无角色设定"
        lines = []
        for name, info in profiles.items():
            if isinstance(info, dict):
                desc = info.get('description', '未知')
                gender = info.get('gender', '未知')
                lines.append(f"{name}: {desc}（性别：{gender}）")
            else:
                lines.append(f"{name}: {info}")
        return "\n".join(lines)

    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """
        调用MiniMax M2.7模型进行复杂因果推理

        Args:
            prompt: 构建好的prompt

        Returns:
            LLM返回的JSON结果
        """
        import os

        from ...ai_service import ProviderConfig
        from ...ai_service.router import AIRouter

        api_key = os.environ.get("MINIMAX_API_KEY")
        if not api_key:
            raise RuntimeError("MINIMAX_API_KEY environment variable not set")

        # 创建MiniMax Provider
        config = {
            "minimax": ProviderConfig(api_key=api_key, model="MiniMax-M2.7")
        }
        router = AIRouter(config=config, primary_provider="minimax", enable_failover=False)

        # 调用MiniMax
        response = router.generate(
            prompt=prompt,
            system=self.SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=2048
        )

        # 解析JSON响应
        try:
            # 尝试提取JSON
            json_text = response.strip()
            if "```json" in json_text:
                json_start = json_text.find("```json") + 7
                json_end = json_text.rfind("```")  # 用rfind避免匹配开头的
                if json_end > json_start:
                    json_text = json_text[json_start:json_end].strip()
            elif "```" in json_text:
                # 可能有多余文本，尝试找JSON开始位置
                json_start = json_text.find('{')
                json_end = json_text.rfind('}')
                if json_start >= 0 and json_end > json_start:
                    json_text = json_text[json_start:json_end+1].strip()
            elif not json_text.startswith('{'):
                # 没有任何JSON标记，尝试找{和}
                json_start = json_text.find('{')
                json_end = json_text.rfind('}')
                if json_start >= 0 and json_end > json_start:
                    json_text = json_text[json_start:json_end+1].strip()

            return json.loads(json_text)
        except json.JSONDecodeError:
            logger.warning(f"LLM返回非JSON格式: {response[:200]}")
            return {"contradictions": []}

    def _create_issue(self, contradiction: Dict[str, Any], chapter_num: int) -> Issue:
        """
        创建Issue对象

        Args:
            contradiction: 矛盾信息字典
            chapter_num: 章节号

        Returns:
            Issue对象
        """
        type_mapping = {
            "causal_chain": "causal_chain_break",
            "emotional_proportion": "emotional_proportion",
            "physical_impossible": "physical_impossible",
            "world_rule_violation": "world_rule_violation"
        }

        issue_type = type_mapping.get(contradiction.get("type", ""), "llm_detected")

        # 根据类型设置不同的严重程度
        if issue_type in ["physical_impossible", "world_rule_violation"]:
            severity = IssueSeverity.P0  # 严重的物理/世界规则矛盾
        elif issue_type == "causal_chain_break":
            severity = IssueSeverity.P1  # 因果链断裂
        else:
            severity = IssueSeverity.P1  # 其他LLM检测的问题

        location_text = contradiction.get("location", "")
        # 尝试提取段落号
        paragraph = None
        if "第" in location_text and "段" in location_text:
            match = re.search(r'第(\d+)段', location_text)
            if match:
                paragraph = int(match.group(1))

        return Issue(
            id=f"LLM_{chapter_num:03d}_{contradiction.get('type', 'unknown')}",
            severity=severity,
            checker_type=CheckerType.LLM_CAUSAL_REASONING,
            issue_type=issue_type,
            title=f"LLM检测-{issue_type}: {contradiction.get('description', '')[:50]}",
            description=contradiction.get("description", ""),
            location=IssueLocation(chapter=chapter_num, paragraph=paragraph),
            evidence=contradiction.get("evidence", ""),
            suggestion=contradiction.get("suggestion", ""),
            confidence=ConfidenceLevel.MEDIUM,
            confidence_score=0.7,  # LLM检测的置信度
            needs_llm_review=False  # 不需要再次复核，因为已经是LLM检测
        )
