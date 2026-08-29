"""LLMServiceAdapter — sync facade unit tests.

Adapter wraps concrete infra.llm_service.LLMService. Tests use a fake
LLMService to avoid real LLM calls.
"""
from __future__ import annotations

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


def test_adapter_execute_returns_text(fake_service: MagicMock) -> None:
    adapter = LLMServiceAdapter(service=fake_service)
    task = LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt="p", system="s")
    result = adapter.execute(task)
    assert result == "raw text response"
    fake_service.execute.assert_called_once_with(task)


def test_adapter_execute_stream_returns_iterator(fake_service: MagicMock) -> None:
    adapter = LLMServiceAdapter(service=fake_service)
    task = LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt="p")
    chunks = list(adapter.execute_stream(task))
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
