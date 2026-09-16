"""LLM data-type contracts (TaskType enum + LLMTask dataclass).

v16.5 relocation: moved from ``infra.llm_service`` to ``lingwen_shared``
so that ``lingwen_llm.port_adapter`` can import the data types without
crossing into ``infra.llm_service`` (which would re-trigger the DP-02
forbidden contract via grimp transitive analysis).

These are infrastructure-level types, not DTOs crossing the wire. They use
``@dataclass`` + ``class Enum`` for low-overhead runtime construction —
no Pydantic v2 validation needed (they're consumed inside Python only).

Back-compat: ``infra.llm_service`` re-exports ``LLMTask`` and ``TaskType``
via ``from lingwen_shared.contracts.python.llm import LLMTask, TaskType``,
so existing consumers in ``tools/`` and ``tests/`` that import from
``infra.llm_service`` keep working unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TaskType(Enum):
    """LLM task types.

    Matches the original TaskType in ``infra.llm_service`` (v15.7+) so
    existing serialized task-type string values (e.g. stored in DB or
    passed across process boundaries) remain stable.
    """

    WORLDVIEW_CHECK = "worldview_check"  # 世界观检测
    CHARACTER_CHECK = "character_check"  # 角色一致性检测
    LOGIC_CHECK = "logic_check"  # 逻辑矛盾检测
    AI_TRACE_CHECK = "ai_trace_check"  # AI痕迹检测
    QUALITY_ANALYSIS = "quality_analysis"  # 质量综合分析
    REPAIR = "repair"  # 修复任务
    # 结构化抽取（v55.2 Phase 92 P2-EXTRACT-ENUM closure）— 用于
    # lingwen-illustrations.extract_scene 等需要 schema-bounded JSON 输出的场景。
    # 语义上比 QUALITY_ANALYSIS 更精确（"extract structured data" 而非 "analyze quality"）。
    # v1 时期用 QUALITY_ANALYSIS 作语义替代,本成员补齐 v2 偏差。
    STRUCTURED_EXTRACTION = "structured_extraction"


@dataclass
class LLMTask:
    """LLM task descriptor.

    Plain dataclass (not Pydantic) because it is an internal Python-only
    type that does not cross any wire boundary. Validation happens at the
    provider layer.
    """

    task_type: TaskType
    prompt: str
    max_tokens: int = 2000
    temperature: float = 0.3
    system: str | None = None


__all__ = ["LLMTask", "TaskType"]
