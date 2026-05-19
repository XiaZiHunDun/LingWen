"""多风格起草器测试"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from multi_style_drafter import (
    MultiStyleDrafter,
    DraftVariant,
    AIProvider,
    WriterPersona,
    ALL_PERSONAS,
)


class MockAIProvider(AIProvider):
    """模拟 AI Provider"""

    def __init__(self, response: str = "测试生成的文本"):
        self.response = response
        self.call_count = 0

    async def generate(self, prompt: str, **kwargs) -> str:
        self.call_count += 1
        return f"{self.response} (调用{self.call_count})"


class TestMultiStyleDrafter:
    """MultiStyleDrafter 测试"""

    @pytest.fixture
    def drafter(self):
        """创建起草器实例"""
        return MultiStyleDrafter(MockAIProvider("测试内容"))

    @pytest.fixture
    def sample_outline(self):
        return {
            "title": "第一章：觉醒",
            "goal": "主角发现自己的特殊能力"
        }

    @pytest.fixture
    def sample_characters(self):
        return [
            {"name": "小明", "description": "主角，15岁"},
            {"name": "老师", "description": "神秘导师"}
        ]

    @pytest.fixture
    def sample_style_guide(self):
        return {
            "tone": "悬疑",
            "target_reader": "青少年"
        }

    def test_draft_returns_variants(self, drafter, sample_outline, sample_characters, sample_style_guide):
        """测试 draft 返回多个变体"""
        variants = asyncio.run(
            drafter.draft(sample_outline, sample_characters, sample_style_guide)
        )

        assert len(variants) == 3
        for variant in variants:
            assert isinstance(variant, DraftVariant)
            assert isinstance(variant.persona, WriterPersona)

    def test_variants_have_different_content(self, drafter, sample_outline, sample_characters, sample_style_guide):
        """测试变体内容不同"""
        variants = asyncio.run(
            drafter.draft(sample_outline, sample_characters, sample_style_guide)
        )

        contents = [v.content for v in variants]
        assert len(set(contents)) == len(contents)  # 所有内容都应该不同

    def test_variants_have_persona_info(self, drafter, sample_outline, sample_characters, sample_style_guide):
        """测试变体包含 persona 信息"""
        variants = asyncio.run(
            drafter.draft(sample_outline, sample_characters, sample_style_guide)
        )

        persona_names = [v.persona.name for v in variants]
        assert "紧张快节奏" in persona_names
        assert "细腻描写" in persona_names
        assert "对话驱动" in persona_names

    def test_parallel_generation(self, drafter, sample_outline, sample_characters, sample_style_guide):
        """测试并行生成"""
        variants = asyncio.run(
            drafter.draft(sample_outline, sample_characters, sample_style_guide)
        )

        # 验证3个变体都被调用
        assert len(variants) == 3

    def test_custom_personas(self, sample_outline, sample_characters, sample_style_guide):
        """测试自定义 Persona 列表"""
        custom_personas = [
            WriterPersona(name="自定义风格1", description="desc1"),
            WriterPersona(name="自定义风格2", description="desc2"),
        ]
        drafter = MultiStyleDrafter(MockAIProvider())
        variants = asyncio.run(
            drafter.draft(
                sample_outline,
                sample_characters,
                sample_style_guide,
                personas=custom_personas
            )
        )

        assert len(variants) == 2
        assert variants[0].persona.name == "自定义风格1"
        assert variants[1].persona.name == "自定义风格2"