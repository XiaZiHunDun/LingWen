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


@pytest.mark.asyncio
async def test_stability_uses_multipart_files_not_urlencoded_data():
    """Phase 96 regression guard: Stability requires multipart/form-data.

    httpx sends application/x-www-form-urlencoded when `data=` is used.
    Stability v2beta requires multipart/form-data and rejects urlencoded
    bodies with 4xx. This test captures the outgoing request and verifies
    `files=` kwarg structure (with (None, value) tuples for text fields).

    Per Phase 93 lesson 1: mock tests matching broken behavior mask
    implementation bugs. The 8 happy/error tests don't catch wire-format
    issues because they only inspect the mocked response, not the request.
    """
    captured = {}

    async def fake_post(url, **kwargs):
        captured["files"] = kwargs.get("files")
        captured["data"] = kwargs.get("data")
        m = MagicMock()
        m.status_code = 200
        m.content = PNG_MAGIC
        m.headers = {}
        m.raise_for_status = MagicMock()
        return m

    fake_client = AsyncMock()
    fake_client.post = fake_post
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "lingwen_illustrations.providers.stability.httpx.AsyncClient",
        return_value=fake_client,
    ):
        result = await generate(
            prompt="X", api_key="k", api_host="https://api.test"
        )

    assert captured["data"] is None, (
        "Stability must use multipart files=, not urlencoded data="
    )
    assert captured["files"] is not None, "files= kwarg must be set"
    assert captured["files"]["prompt"] == (None, "X"), (
        "multipart text field requires (None, value) tuple"
    )
    assert captured["files"]["output_format"] == (None, "png")
    assert result == PNG_MAGIC
