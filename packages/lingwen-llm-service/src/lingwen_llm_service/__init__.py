"""lingwen-llm-service — canonical LLM service package.

Phase 43 P3-ARCHDEBT: relocated from infra/llm_service.py (309 LOC).
NOT-LEAF (depends on lingwen_shared + lingwen_llm).
DP-02 contract: business code MUST NOT import LLMService directly — use
LLMServiceAdapter from lingwen_llm.port_adapter instead.
"""

from __future__ import annotations

from lingwen_llm_service.factory import (
    _default_service_factory,  # noqa: F401 — used in set_default_factory() below
    create_task,
    get_llm_service,
)
from lingwen_llm_service.service import LLMService
from lingwen_shared.contracts.python.llm import LLMTask, TaskType

# Module-load factory registration (preserves v16.5 DP-02 contract).
# Side effect: importing lingwen_llm_service anywhere wires up
# LLMServiceAdapter() default behavior.
from lingwen_llm.port_adapter import set_default_factory

set_default_factory(_default_service_factory)

__all__ = [
    "LLMService",
    "LLMTask",
    "TaskType",
    "get_llm_service",
    "create_task",
]