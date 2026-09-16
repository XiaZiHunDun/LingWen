"""Test OpenAI DALL-E 3 adapter (Phase 96 provider abstraction).

DALL-E 3 contract:
- Endpoint: https://api.openai.com/v1/images/generations
- Payload: {model: "dall-e-3", prompt, n: 1, size: "1024x1024", response_format: "b64_json"}
- Response: {"created": ..., "data": [{"b64_json": "..."}]}
- Default size: 1024x1024 (other valid: 1024x1792, 1792x1024)
- Returns PNG bytes (DALL-E 3 default).
"""
from __future__ import annotations

import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from lingwen_illustrations.exceptions import GenerateError
from lingwen_illustrations.providers.openai import generate

PNG_MAGIC = b"\x89PNG\r\n\x1a\nfake-png-bytes-here"


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
async def test_openai_returns_decoded_png_bytes():
    """Real DALL-E 3 path: b64_json envelope → PNG bytes."""
    b64 = base64.b64encode(PNG_MAGIC).decode("ascii")
    api_body = {"created": 1234567890, "data": [{"b64_json": b64}]}
    fake = _json_response(api_body)
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.openai.httpx.AsyncClient",
        return_value=mock_client,
    ):
        result = await generate(
            prompt="test prompt", api_key="k", api_host="https://api.test"
        )
    assert result == PNG_MAGIC


@pytest.mark.asyncio
async def test_openai_provider_attribute_set_on_all_errors():
    fake = _json_response({"data": []})  # empty data
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.openai.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.provider == "openai"


@pytest.mark.asyncio
async def test_openai_content_policy_raises_non_retryable():
    """HTTP 400 content_policy_violation → non-retryable (user/prompt issue)."""
    fake = MagicMock()
    fake.status_code = 400
    fake.headers = {}
    fake.raise_for_status.side_effect = Exception("400 content_policy_violation")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.openai.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is False
    assert exc.value.provider == "openai"


@pytest.mark.asyncio
async def test_openai_billing_hard_limit_raises_non_retryable():
    fake = MagicMock()
    fake.status_code = 400
    fake.headers = {}
    fake.raise_for_status.side_effect = Exception("400 billing_hard_limit_reached")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.openai.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is False


@pytest.mark.asyncio
async def test_openai_rate_limit_raises_with_retry_after():
    fake = MagicMock()
    fake.status_code = 429
    fake.headers = {"retry-after": "20"}
    fake.raise_for_status.side_effect = Exception("429")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.openai.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retry_after == 20
    assert exc.value.provider == "openai"
    assert exc.value.retryable is True


@pytest.mark.asyncio
async def test_openai_http_500_raises_retryable():
    fake = MagicMock()
    fake.status_code = 500
    fake.headers = {}
    fake.raise_for_status.side_effect = Exception("500")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.openai.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is True


@pytest.mark.asyncio
async def test_openai_model_not_found_raises_non_retryable():
    """HTTP 404 model_not_found → non-retryable config issue."""
    fake = MagicMock()
    fake.status_code = 404
    fake.headers = {}
    fake.raise_for_status.side_effect = Exception("404 model_not_found")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.openai.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is False


@pytest.mark.asyncio
async def test_openai_timeout_raises():
    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.TimeoutException("timeout")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    with patch(
        "lingwen_illustrations.providers.openai.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retry_after == 60
    assert exc.value.provider == "openai"


@pytest.mark.asyncio
async def test_openai_malformed_json_raises():
    resp = MagicMock()
    resp.status_code = 200
    resp.headers = {}
    resp.raise_for_status = MagicMock()
    resp.json.side_effect = json.JSONDecodeError("bad", "doc", 0)
    mock_client = _client_with_response(resp)
    with patch(
        "lingwen_illustrations.providers.openai.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.provider == "openai"
    assert "non-JSON" in str(exc.value)
