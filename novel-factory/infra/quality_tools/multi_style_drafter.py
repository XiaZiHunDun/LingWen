"""多风格起草器 - 方向H质量工具集"""

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from quality_tools.writer_persona import WriterPersona, ALL_PERSONAS


@dataclass
class DraftVariant:
    """起草变体"""
    persona: WriterPersona
    content: str                       # 生成的文本
    style_score: float = 0.0          # 风格契合度评分


class AIProvider:
    """AI Provider 抽象接口 - 需要外部注入"""

    async def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        raise NotImplementedError


class MultiStyleDrafter:
    """多风格起草器"""

    def __init__(self, ai_provider: AIProvider):
        self.ai_provider = ai_provider

    def _build_prompt(
        self,
        outline: Dict[str, Any],
        characters: List[Dict],
        style_guide: Dict[str, Any],
        persona: WriterPersona
    ) -> str:
        """构建生成提示词"""
        characters_str = "\n".join([
            f"- {c.get('name', '未知')}: {c.get('description', '')}"
            for c in characters
        ]) if characters else "无"

        outline_str = "\n".join([
            f"- {k}: {v}" for k, v in outline.items()
        ]) if outline else "无"

        style_str = "\n".join([
            f"- {k}: {v}" for k, v in style_guide.items()
        ]) if style_guide else "无"

        return f"""请用{persona.name}的风格撰写章节。

## 风格要求
{persona.description}
{persona.system_prompt_suffix}

## 大纲
{outline_str}

## 角色设定
{characters_str}

## 风格指南
{style_str}
"""

    async def _generate_single(
        self,
        outline: Dict[str, Any],
        characters: List[Dict],
        style_guide: Dict[str, Any],
        persona: WriterPersona
    ) -> DraftVariant:
        """生成单个变体"""
        prompt = self._build_prompt(outline, characters, style_guide, persona)

        content = await self.ai_provider.generate(
            prompt,
            temperature=persona.temperature,
            top_p=persona.top_p,
            max_tokens=persona.max_tokens
        )

        return DraftVariant(
            persona=persona,
            content=content,
            style_score=0.0  # 初始评分为0，后续由质量门禁计算
        )

    async def draft(
        self,
        outline: Dict[str, Any],
        characters: List[Dict],
        style_guide: Dict[str, Any],
        personas: Optional[List[WriterPersona]] = None
    ) -> List[DraftVariant]:
        """并行生成多个风格变体"""
        personas = personas or ALL_PERSONAS

        # 并行调用 LLM 生成所有变体
        tasks = [
            self._generate_single(outline, characters, style_guide, persona)
            for persona in personas
        ]

        variants = await asyncio.gather(*tasks)
        return list(variants)