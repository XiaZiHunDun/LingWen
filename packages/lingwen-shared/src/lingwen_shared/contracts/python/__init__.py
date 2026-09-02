"""lingwen_shared.contracts.python — Pydantic v2 source-of-truth DTO.

Plus v16.5: plain dataclass/enum LLM data types (LLMTask, TaskType).
"""

from lingwen_shared.contracts.python.llm import LLMTask, TaskType

__all__ = ["LLMTask", "TaskType"]
