"""
Quality Tools - 统一质量工具入口

已迁移到 novel-factory/tools/
此模块用于向后兼容
"""

import warnings

warnings.warn(
    "infra.quality.tools 已弃用，请使用 novel-factory/tools/ 下的工具。",
    DeprecationWarning,
    stacklevel=2
)

# 推荐使用的工具入口
TOOLS_INDEX = {
    # 验证工具
    "verify_quality": "tools/verify_quality.py",
    "batch_repair": "tools/batch_repair.py",
    # LLM分析器
    "llm_foreshadow_analyzer": "tools/llm_foreshadow_analyzer.py",
    "llm_emotional_resonance_checker": "tools/llm_emotional_resonance_checker.py",
    "llm_pacing_analyzer": "tools/llm_pacing_analyzer.py",
    "llm_character_arc_analyzer": "tools/llm_character_arc_analyzer.py",
    "llm_protagonist_charm_analyzer": "tools/llm_protagonist_charm_analyzer.py",
    "llm_readability_analyzer": "tools/llm_readability_analyzer.py",
    # 批量工具
    "llm_quality_deep_check": "tools/llm_quality_deep_check.py",
    "llm_polish_chapters": "tools/llm_polish_chapters.py",
}

__all__ = ["TOOLS_INDEX"]
