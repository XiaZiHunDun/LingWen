"""Writer Persona 测试"""

import pytest
from writer_persona import (
    WriterPersona,
    PersonaConfig,
    TENSE_FAST,
    DELICATE_DESCRIPTIVE,
    DIALOGUE_DRIVEN,
    ALL_PERSONAS,
)


class TestWriterPersona:
    """WriterPersona 数据类测试"""

    def test_persona_creation(self):
        """测试 Persona 创建"""
        persona = WriterPersona(
            name="测试风格",
            description="测试描述",
            temperature=0.7,
            top_p=0.9,
            max_tokens=4000,
            system_prompt_suffix="测试附加"
        )

        assert persona.name == "测试风格"
        assert persona.description == "测试描述"
        assert persona.temperature == 0.7
        assert persona.top_p == 0.9
        assert persona.max_tokens == 4000
        assert persona.system_prompt_suffix == "测试附加"

    def test_predefined_personas(self):
        """测试预定义风格"""
        assert TENSE_FAST.name == "紧张快节奏"
        assert TENSE_FAST.temperature == 0.8
        assert TENSE_FAST.top_p == 0.85
        assert TENSE_FAST.max_tokens == 3000

        assert DELICATE_DESCRIPTIVE.name == "细腻描写"
        assert DELICATE_DESCRIPTIVE.temperature == 0.6
        assert DELICATE_DESCRIPTIVE.max_tokens == 5000

        assert DIALOGUE_DRIVEN.name == "对话驱动"
        assert DIALOGUE_DRIVEN.temperature == 0.7
        assert DIALOGUE_DRIVEN.max_tokens == 3500


class TestPersonaConfig:
    """PersonaConfig 管理器测试"""

    def test_get_persona(self):
        """测试获取 Persona"""
        config = PersonaConfig()

        persona = config.get_persona("紧张快节奏")
        assert persona.name == "紧张快节奏"
        assert persona.temperature == 0.8

    def test_get_persona_not_found(self):
        """测试获取不存在的 Persona"""
        config = PersonaConfig()

        with pytest.raises(ValueError, match="Unknown persona"):
            config.get_persona("不存在的风格")

    def test_list_personas(self):
        """测试列出所有 Persona"""
        config = PersonaConfig()

        personas = config.list_personas()
        assert len(personas) == 3
        assert TENSE_FAST in personas
        assert DELICATE_DESCRIPTIVE in personas
        assert DIALOGUE_DRIVEN in personas

    def test_custom_personas(self):
        """测试自定义 Persona 列表"""
        custom_personas = [
            WriterPersona(name="自定义1", description="desc1"),
            WriterPersona(name="自定义2", description="desc2"),
        ]
        config = PersonaConfig(personas=custom_personas)

        personas = config.list_personas()
        assert len(personas) == 2
        assert config.get_persona("自定义1").name == "自定义1"