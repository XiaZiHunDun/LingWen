"""Tests for lingwen_shared.contracts.python.llm canonical data types.

v16.5: LLMTask and TaskType relocated from infra.llm_service to
lingwen_shared so the LLMServiceAdapter can import them without
crossing into infra.llm_service (which would re-trigger the DP-02
forbidden contract via grimp transitive analysis).
"""

from __future__ import annotations

import pytest
from lingwen_shared.contracts.python.llm import LLMTask, TaskType


def test_task_type_values_match_infra_baseline() -> None:
    """TaskType enum must expose the six task kinds used by infra.llm_service."""
    assert TaskType.WORLDVIEW_CHECK.value == "worldview_check"
    assert TaskType.CHARACTER_CHECK.value == "character_check"
    assert TaskType.LOGIC_CHECK.value == "logic_check"
    assert TaskType.AI_TRACE_CHECK.value == "ai_trace_check"
    assert TaskType.QUALITY_ANALYSIS.value == "quality_analysis"
    assert TaskType.REPAIR.value == "repair"


def test_llm_task_required_fields() -> None:
    """LLMTask must require task_type + prompt; everything else has defaults."""
    task = LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt="hello")
    assert task.task_type is TaskType.QUALITY_ANALYSIS
    assert task.prompt == "hello"
    assert task.max_tokens == 2000
    assert task.temperature == 0.3
    assert task.system is None


def test_llm_task_override_fields() -> None:
    """All fields are settable via constructor kwargs."""
    task = LLMTask(
        task_type=TaskType.REPAIR,
        prompt="fix it",
        max_tokens=3000,
        temperature=0.7,
        system="you are a careful editor",
    )
    assert task.task_type is TaskType.REPAIR
    assert task.prompt == "fix it"
    assert task.max_tokens == 3000
    assert task.temperature == 0.7
    assert task.system == "you are a careful editor"


def test_llm_task_equality() -> None:
    """LLMTask is a dataclass — two tasks with same fields compare equal."""
    a = LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt="x")
    b = LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt="x")
    assert a == b


def test_llm_task_is_dataclass_not_pydantic() -> None:
    """LLMTask stays a stdlib dataclass (no Pydantic overhead — internal type)."""
    import dataclasses

    assert dataclasses.is_dataclass(LLMTask)


def test_module_importable_via_package_root() -> None:
    """Symbols re-exported from lingwen_shared.contracts.python (T2)."""
    from lingwen_shared.contracts.python import LLMTask as RootTask
    from lingwen_shared.contracts.python import TaskType as RootType

    assert RootTask is LLMTask
    assert RootType is TaskType
