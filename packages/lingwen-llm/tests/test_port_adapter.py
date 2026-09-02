"""LLMServiceAdapter — async facade unit tests.

Adapter wraps concrete infra.llm_service.LLMService. Tests use a fake
LLMService to avoid real LLM calls.
"""

from __future__ import annotations

import inspect
from typing import Any, Iterator
from unittest.mock import MagicMock

import pytest
from lingwen_llm.port_adapter import LLMServiceAdapter
from lingwen_shared.contracts.python.llm import LLMTask, TaskType


@pytest.fixture
def fake_service() -> MagicMock:
    service = MagicMock()
    service.execute.return_value = "raw text response"
    service.execute_stream.return_value = iter(["chunk1", "chunk2"])
    service.parse_json_response.return_value = {"key": "value"}
    service.provider_name = "minimax"
    service.is_available.return_value = True
    # Intentionally DO NOT pre-populate _provider so that the attribute is
    # absent from this MagicMock until a test sets it explicitly. This lets
    # each is_available() test pin down the exact state under verification
    # rather than relying on MagicMock's auto-attribute truthiness.
    return service


@pytest.mark.asyncio
async def test_adapter_execute_returns_text(fake_service: MagicMock) -> None:
    adapter = LLMServiceAdapter(service=fake_service)
    task = LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt="p", system="s")
    result = await adapter.execute(task)
    assert result == "raw text response"
    fake_service.execute.assert_called_once_with(task)


@pytest.mark.asyncio
async def test_adapter_execute_stream_returns_iterator(fake_service: MagicMock) -> None:
    adapter = LLMServiceAdapter(service=fake_service)
    task = LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt="p")
    chunks = [chunk async for chunk in adapter.execute_stream(task)]
    assert chunks == ["chunk1", "chunk2"]
    fake_service.execute_stream.assert_called_once_with(task)


def test_adapter_parse_json_response(fake_service: MagicMock) -> None:
    adapter = LLMServiceAdapter(service=fake_service)
    parsed = adapter.parse_json_response("raw text")
    assert parsed == {"key": "value"}
    fake_service.parse_json_response.assert_called_once_with("raw text")


def test_adapter_provider_name(fake_service: MagicMock) -> None:
    adapter = LLMServiceAdapter(service=fake_service)
    assert adapter.provider_name == "minimax"


def test_adapter_is_available_true_when_service_set(fake_service: MagicMock) -> None:
    fake_service.get.return_value = fake_service
    fake_service._provider = MagicMock()
    adapter = LLMServiceAdapter(service=fake_service)
    assert adapter.is_available() is True


def test_adapter_is_available_false_when_no_provider(fake_service: MagicMock) -> None:
    fake_service.get.return_value = fake_service
    fake_service._provider = None
    fake_service.is_available.return_value = False
    adapter = LLMServiceAdapter(service=fake_service)
    assert adapter.is_available() is False


def test_adapter_uses_registered_factory_when_no_service() -> None:
    """Adapter must call the registered default factory when no service is injected."""
    from lingwen_llm.port_adapter import set_default_factory

    fake = MagicMock(provider_name="minimax")
    set_default_factory(lambda: fake)
    try:
        adapter = LLMServiceAdapter()
        assert adapter.provider_name == "minimax"
        assert adapter._service is fake
    finally:
        set_default_factory(None)


# ---------------------------------------------------------------------------
# v16.5 #N.12 — Async surface conformance (Part A foundation)
# ---------------------------------------------------------------------------


class _FakeService:
    """Minimal sync service stub for async adapter tests.

    Phase 126 v16.5 #N.12: shared across 3 async tests (extracted per code review
    I2 — DRY from duplicated inline classes).
    """

    def execute(self, task):
        return "ok"

    def execute_stream(self, task):
        yield "a"
        yield "b"


@pytest.mark.asyncio
async def test_execute_is_async_returns_string():
    """Phase 126 v16.5 #N.12: LLMServiceAdapter.execute is async, returns str (NOT awaitable)."""
    from lingwen_llm.port_adapter import LLMServiceAdapter
    from lingwen_shared.contracts.python.llm import LLMTask, TaskType

    adapter = LLMServiceAdapter(service=_FakeService())
    task = LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt="x")
    assert inspect.iscoroutinefunction(adapter.execute)
    assert await adapter.execute(task) == "ok"


@pytest.mark.asyncio
async def test_execute_stream_is_async_generator():
    """Phase 126 v16.5 #N.12: LLMServiceAdapter.execute_stream is async generator."""
    from lingwen_llm.port_adapter import LLMServiceAdapter
    from lingwen_shared.contracts.python.llm import LLMTask, TaskType

    adapter = LLMServiceAdapter(service=_FakeService())
    task = LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt="x")
    chunks = []
    async for chunk in adapter.execute_stream(task):
        chunks.append(chunk)
    assert chunks == ["a", "b"]


@pytest.mark.asyncio
async def test_generate_is_async():
    """Phase 126 v16.5 #N.12: LLMServiceAdapter.generate is async (legacy API retained)."""
    from lingwen_llm.port_adapter import LLMServiceAdapter

    adapter = LLMServiceAdapter(service=_FakeService())
    assert inspect.iscoroutinefunction(adapter.generate)
    assert await adapter.generate(prompt="x", system="y") == "ok"
