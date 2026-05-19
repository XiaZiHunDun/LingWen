"""质量工具集 - 方向H"""

from quality_tools.writer_persona import (
    WriterPersona,
    PersonaConfig,
    TENSE_FAST,
    DELICATE_DESCRIPTIVE,
    DIALOGUE_DRIVEN,
    ALL_PERSONAS,
)

from quality_tools.quality_gate import (
    QualityGate,
    QualityLevel,
    QualityResult,
)

from quality_tools.multi_style_drafter import (
    MultiStyleDrafter,
    DraftVariant,
)

__all__ = [
    # WriterPersona
    "WriterPersona",
    "PersonaConfig",
    "TENSE_FAST",
    "DELICATE_DESCRIPTIVE",
    "DIALOGUE_DRIVEN",
    "ALL_PERSONAS",
    # QualityGate
    "QualityGate",
    "QualityLevel",
    "QualityResult",
    # MultiStyleDrafter
    "MultiStyleDrafter",
    "DraftVariant",
]