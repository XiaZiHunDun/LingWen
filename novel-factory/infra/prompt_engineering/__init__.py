"""灵文提示词工程 (Phase 1.3)

Doc 2 (提示词工程 v1.0) 实施层。

核心导出:
- ContextItem / StepContract / PromptContext
- 12 SCENARIOS (后续 phase 1.3.c)
- 22 STEP_CONTRACTS (后续 phase 1.3.c)
- ContextBuilder + AutoSummarizer (后续 phase 1.3.e)
- load_template / render (后续 phase 1.3.g)

不导出 (后续阶段):
- 12 场景的具体 prompt 措辞 (只给 1 个示例: chapter_writing)
- 5 本网文全集蒸馏 (主公后续指定)
- 多模型分级路由 (Haiku 4.5 提及但 routing out of scope)
"""
from .context_builder import (
    AutoSummarizer,
    BudgetOverflowError,
    BuiltContext,
    ContextBuilder,
    ContextBuilderError,
    MissingContextError,
)
from .data_structures import (
    ContextItem,
    PromptContext,
    StepContract,
)
from .extraction import (
    ExtractedResolution,
    ExtractedRipple,
    ExtractionParseError,
    RippleExtractionResult,
    parse_ripple_extraction,
)
from .scenarios import (
    SCENARIOS,
    STEP_CONTRACTS,
    get_scenario,
    get_step_contract,
)
from .templates import (
    RenderedPrompt,
    Template,
    TemplateError,
    TemplateNotFoundError,
    TemplateParseError,
    load_template,
    render_template,
)

__all__ = [
    "ContextItem",
    "StepContract",
    "PromptContext",
    "SCENARIOS",
    "STEP_CONTRACTS",
    "get_scenario",
    "get_step_contract",
    "ContextBuilder",
    "AutoSummarizer",
    "BuiltContext",
    "ContextBuilderError",
    "MissingContextError",
    "BudgetOverflowError",
    "Template",
    "RenderedPrompt",
    "TemplateError",
    "TemplateNotFoundError",
    "TemplateParseError",
    "load_template",
    "render_template",
    # Phase 2.1 — LLM ripple extraction
    "ExtractedRipple",
    "ExtractedResolution",
    "RippleExtractionResult",
    "ExtractionParseError",
    "parse_ripple_extraction",
]
