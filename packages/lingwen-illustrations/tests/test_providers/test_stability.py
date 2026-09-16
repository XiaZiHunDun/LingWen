"""Test Stability AI SD3 adapter (Phase 96 provider abstraction).

Stability v2beta contract:
- Endpoint: https://api.stability.ai/v2beta/stable-image/generate/sd3
- Headers: Authorization Bearer + Accept: image/*
- Body: multipart/form-data with {prompt, output_format: "png"}
- Response: raw PNG bytes (NOT JSON envelope — header Accept: image/* bypasses JSON)
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from lingwen_illustrations.exceptions import GenerateError
from lingwen_illustrations.providers.stability import generate

PNG_MAGIC = b"\x89PNG\r\n\x1a\nfake-png-bytes-here"


def _raw_response(content, status_code=200, headers=None):
    fake = MagicMock()
    fake.status_code = status_code
    fake.headers = headers or {}
    fake.raise_for_status = MagicMock()
    if status_code == 200:
        fake.content = content
    else:
        fake.raise_for_status.side_effect = Exception(f"{status_code}")
        fake.content = content
    return fake


def _client_with_response(fake_response):
    mock_client = AsyncMock()
    mock_client.post.return_value = fake_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


@pytest.mark.asyncio
async def test_stability_returns_raw_png_bytes():
    """Stability with Accept: image/* returns raw bytes (no envelope)."""
    fake = _raw_response(PNG_MAGIC)
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.stability.httpx.AsyncClient",
        return_value=mock_client,
    ):
        result = await generate(
            prompt="test prompt", api_key="k", api_host="https://api.test"
        )
    assert result == PNG_MAGIC


@pytest.mark.asyncio
async def test_stability_provider_attribute_set():
    fake = MagicMock()
    fake.status_code = 500
    fake.headers = {}
    fake.raise_for_status.side_effect = Exception("500")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.stability.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.provider == "stability"


@pytest.mark.asyncio
async def test_stability_rate_limit_with_retry_after_header():
    fake = MagicMock()
    fake.status_code = 429
    fake.headers = {"retry-after": "15"}
    fake.raise_for_status.side_effect = Exception("429")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.stability.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retry_after == 15
    assert exc.value.provider == "stability"


@pytest.mark.asyncio
async def test_stability_rate_limit_no_retry_after_header():
    """Stability v2beta may not return retry-after — fall back to 30s default."""
    fake = MagicMock()
    fake.status_code = 429
    fake.headers = {}  # no retry-after
    fake.raise_for_status.side_effect = Exception("429")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.stability.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retry_after == 30  # stability-specific default


@pytest.mark.asyncio
async def test_stability_invalid_prompt_raises_non_retryable():
    fake = MagicMock()
    fake.status_code = 400
    fake.headers = {}
    fake.raise_for_status.side_effect = Exception("400 invalid_prompt")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.stability.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is False


@pytest.mark.asyncio
async def test_stability_insufficient_credit_raises_non_retryable():
    fake = MagicMock()
    fake.status_code = 402
    fake.headers = {}
    fake.raise_for_status.side_effect = Exception("402 insufficient_credit")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.stability.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is False


@pytest.mark.asyncio
async def test_stability_timeout_raises():
    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.TimeoutException("timeout")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    with patch(
        "lingwen_illustrations.providers.stability.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retry_after == 60
    assert exc.value.provider == "stability"


@pytest.mark.asyncio
async def test_stability_network_error_raises():
    mock_client = AsyncMock()
    mock_client.post.side_effect = ConnectionError("network down")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    with patch(
        "lingwen_illustrations.providers.stability.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.provider == "stability"
    assert exc.value.retryable is True
