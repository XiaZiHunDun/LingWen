"""Factory helpers + module-load DP-02 contract registration.

Phase 43 P3-ARCHDEBT: relocated from infra/llm_service.py (factory + helpers).

DP-02 contract: when this package is imported anywhere in the process,
``set_default_factory(_default_service_factory)`` is called at module load
of ``lingwen_llm_service/__init__.py`` (see __init__.py:final). This wires
up ``LLMServiceAdapter()`` default behavior so business code can construct
adapters without explicit service injection.

Triggers:
  - ``infra/core/__init__.py`` wildcard ``from lingwen_llm_service import *``
  - ``tests/tools/conftest.py`` plain ``import lingwen_llm_service``
  - Any process that imports lingwen_llm_service transitively

Why module-load: the v16.4 grimp-evasion hack in port_adapter.py (which
used string-concat to hide ``importlib.import_module("infra.llm_service")``)
was eliminated in v16.5 by relocating LLMTask/TaskType to lingwen_shared
and using a factory for the default service. Module-load registration
preserves that contract without the grimp-evasion pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from lingwen_shared.contracts.python.llm import LLMTask, TaskType

if TYPE_CHECKING:
    from lingwen_llm_service.service import LLMService


# Convenience helpers
def get_llm_service() -> "LLMService":
    """获取LLM服务实例"""
    from lingwen_llm_service.service import LLMService

    return LLMService.get()


def create_task(task_type: TaskType, prompt: str, **kwargs) -> LLMTask:
    """创建LLM任务"""
    return LLMTask(task_type=task_type, prompt=prompt, **kwargs)


def _default_service_factory() -> "LLMService":
    """Factory returning the LLMService singleton (lazy).

    Imported by lingwen_llm_service/__init__.py to wire up the LLMServiceAdapter
    default factory at module load time.
    """
    from lingwen_llm_service.service import LLMService

    return LLMService.get()


__all__ = ["get_llm_service", "create_task", "_default_service_factory"]