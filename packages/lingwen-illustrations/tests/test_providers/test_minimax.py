"""Test Stage 3 MiniMax adapter (Phase 96 provider abstraction).

Same test coverage as Phase 93 test_image_generator.py — ported to target
providers/minimax.py module path.
"""
from __future__ import annotations

import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from lingwen_illustrations.exceptions import GenerateError
from lingwen_illustrations.providers.minimax import generate

JPEG_MAGIC = b"\xff\xd8\xff\xe0fake-jpeg-bytes-here"


def _json_response(body, status_code=200):
    fake = MagicMock()
    fake.status_code = status_code
    fake.headers = {}
    fake.raise_for_status = MagicMock()
    if status_code == 200:
        fake.json.return_value = body
    else:
        fake.raise_for_status.side_effect = Exception(f"{status_code}")
        fake.json.return_value = body
    return fake


def _client_with_response(fake_response):
    mock_client = AsyncMock()
    mock_client.post.return_value = fake_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


@pytest.mark.asyncio
async def test_minimax_returns_decoded_jpeg_bytes():
    b64 = base64.b64encode(JPEG_MAGIC).decode("ascii")
    api_body = {"created": 1234567890, "data": [{"b64_json": b64}]}
    fake = _json_response(api_body)
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.minimax.httpx.AsyncClient",
        return_value=mock_client,
    ):
        result = await generate(
            prompt="test prompt", api_key="k", api_host="https://api.test"
        )
    assert result == JPEG_MAGIC


@pytest.mark.asyncio
async def test_minimax_provider_attribute_set_on_error():
    """All MiniMax errors must have provider='minimax' (Phase 96 §5.1)."""
    fake = _json_response({"data": []})  # empty data array
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.minimax.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.provider == "minimax"


@pytest.mark.asyncio
async def test_minimax_rate_limit_raises_with_provider_and_retry_after():
    fake = MagicMock()
    fake.status_code = 429
    fake.headers = {"retry-after": "30"}
    fake.raise_for_status.side_effect = Exception("429")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.minimax.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.provider == "minimax"
    assert exc.value.retry_after == 30


@pytest.mark.asyncio
async def test_minimax_rate_limit_http_date_fallback():
    fake = MagicMock()
    fake.status_code = 429
    fake.headers = {"retry-after": "Wed, 21 Oct 2026 07:28:00 GMT"}
    fake.raise_for_status.side_effect = Exception("429")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.minimax.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.provider == "minimax"
    assert exc.value.retry_after == 60  # RFC 7231 fallback


@pytest.mark.asyncio
async def test_minimax_network_error_raises():
    mock_client = AsyncMock()
    mock_client.post.side_effect = ConnectionError("network down")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    with patch(
        "lingwen_illustrations.providers.minimax.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.provider == "minimax"
    assert exc.value.retryable is True


@pytest.mark.asyncio
async def test_minimax_timeout_raises():
    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.TimeoutException("timeout")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    with patch(
        "lingwen_illustrations.providers.minimax.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retry_after == 60
    assert exc.value.provider == "minimax"


@pytest.mark.asyncio
async def test_minimax_http_500_raises_retryable():
    fake = MagicMock()
    fake.status_code = 500
    fake.headers = {}
    fake.raise_for_status.side_effect = Exception("500")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.minimax.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is True
    assert exc.value.provider == "minimax"


@pytest.mark.asyncio
async def test_minimax_http_400_raises_non_retryable():
    """Per Phase 96 §5.4: 4xx (除 429) are non-retryable."""
    fake = MagicMock()
    fake.status_code = 400
    fake.headers = {}
    fake.raise_for_status.side_effect = Exception("400")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.minimax.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is False
    assert exc.value.provider == "minimax"
