"""Writer Persona 定义 - 方向H质量工具集"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class WriterPersona:
    """作家风格 Persona 定义"""
    name: str                          # "紧张快节奏" / "细腻描写" / "对话驱动"
    description: str                   # 风格描述
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 4000
    system_prompt_suffix: str = ""     # 附加的系统提示


# 预定义风格变体（3种）
TENSE_FAST = WriterPersona(
    name="紧张快节奏",
    description="高悬念、短句、快速推进",
    temperature=0.8,
    top_p=0.85,
    max_tokens=3000
)

DELICATE_DESCRIPTIVE = WriterPersona(
    name="细腻描写",
    description="环境渲染、情绪铺垫、慢热",
    temperature=0.6,
    top_p=0.9,
    max_tokens=5000
)

DIALOGUE_DRIVEN = WriterPersona(
    name="对话驱动",
    description="人物互动为主、动作描写少",
    temperature=0.7,
    top_p=0.9,
    max_tokens=3500
)

ALL_PERSONAS = [TENSE_FAST, DELICATE_DESCRIPTIVE, DIALOGUE_DRIVEN]


class PersonaConfig:
    """Persona 配置管理器"""

    def __init__(self, personas: Optional[List[WriterPersona]] = None):
        self._personas = personas or ALL_PERSONAS
        self._name_map = {p.name: p for p in self._personas}

    def get_persona(self, name: str) -> WriterPersona:
        """根据名称获取 Persona"""
        if name not in self._name_map:
            raise ValueError(f"Unknown persona: {name}. Available: {list(self._name_map.keys())}")
        return self._name_map[name]

    def list_personas(self) -> List[WriterPersona]:
        """列出所有可用的 Persona"""
        return self._personas.copy()