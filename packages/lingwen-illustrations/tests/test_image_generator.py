"""Test Stage 3 MiniMax multimodal API call."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from lingwen_illustrations.exceptions import GenerateError
from lingwen_illustrations.image_generator import generate


@pytest.mark.asyncio
async def test_generate_returns_jpeg_bytes(monkeypatch):
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.content = b"\xff\xd8\xff\xe0fake-jpeg"
    fake_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = fake_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("lingwen_illustrations.image_generator.httpx.AsyncClient", return_value=mock_client):
        result = await generate(prompt="测试 prompt", api_key="test-key", api_host="https://api.test")

    assert result == b"\xff\xd8\xff\xe0fake-jpeg"
    mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_generate_rate_limit_raises_with_retry_after(monkeypatch):
    fake_response = MagicMock()
    fake_response.status_code = 429
    fake_response.headers = {"retry-after": "30"}
    fake_response.raise_for_status.side_effect = Exception("429 Too Many Requests")

    mock_client = AsyncMock()
    mock_client.post.return_value = fake_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("lingwen_illustrations.image_generator.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is True
    assert exc.value.retry_after == 30


@pytest.mark.asyncio
async def test_generate_network_error_raises(monkeypatch):
    mock_client = AsyncMock()
    mock_client.post.side_effect = ConnectionError("network down")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("lingwen_illustrations.image_generator.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is True


@pytest.mark.asyncio
async def test_generate_timeout_raises(monkeypatch):
    import httpx
    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.TimeoutException("timeout")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("lingwen_illustrations.image_generator.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is True
