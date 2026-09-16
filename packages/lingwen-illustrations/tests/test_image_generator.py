"""Test Stage 3 MiniMax multimodal API call.

v55.3 Phase 93 — b64_json real decode:
The MiniMax image API returns JSON of shape
  {"created": ..., "data": [{"b64_json": "<base64-jpeg-bytes>"}]}
when response_format=b64_json is requested. Tests now mock realistic JSON
responses (not raw JPEG bytes) to verify the decode path.
"""

from __future__ import annotations

import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from lingwen_illustrations.exceptions import GenerateError
from lingwen_illustrations.image_generator import generate

JPEG_MAGIC = b"\xff\xd8\xff\xe0fake-jpeg-bytes-here"


def _json_response(body: object, status_code: int = 200) -> MagicMock:
    """Build a mock httpx Response returning a JSON body."""
    fake = MagicMock()
    fake.status_code = status_code
    fake.headers = {}
    fake.raise_for_status = MagicMock()
    if status_code == 200:
        fake.json.return_value = body
    else:
        # For non-200, raise_for_status is the contract check path.
        fake.raise_for_status.side_effect = Exception(f"{status_code}")
        fake.json.return_value = body  # never reached but kept for safety
    return fake


def _client_with_response(fake_response: MagicMock) -> AsyncMock:
    mock_client = AsyncMock()
    mock_client.post.return_value = fake_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


@pytest.mark.asyncio
async def test_generate_returns_decoded_jpeg_bytes():
    """Real API path: JSON envelope with b64_json → decoded JPEG bytes.

    Previously this test mocked raw JPEG bytes in resp.content, which worked
    because the v1 implementation returned resp.content unchanged. Phase 93
    changed the implementation to parse JSON + base64-decode, so the mock
    must now reflect the actual API response shape.
    """
    b64_value = base64.b64encode(JPEG_MAGIC).decode("ascii")
    api_body = {
        "created": 1234567890,
        "data": [{"b64_json": b64_value}],
    }
    fake_response = _json_response(api_body)
    mock_client = _client_with_response(fake_response)

    with patch("lingwen_illustrations.image_generator.httpx.AsyncClient", return_value=mock_client):
        result = await generate(
            prompt="测试 prompt", api_key="test-key", api_host="https://api.test"
        )

    assert result == JPEG_MAGIC
    # Sanity: must NOT be the JSON envelope string (would indicate a regression
    # to the v1 behavior of returning resp.content raw).
    assert b"b64_json" not in result
    assert b"data" not in result or len(result) < 100  # not the JSON dict


@pytest.mark.asyncio
async def test_generate_picks_first_data_item_when_multiple():
    """If API returns multiple data items, take data[0] (matches n=1 contract)."""
    b64_first = base64.b64encode(b"\xff\xd8FIRST").decode("ascii")
    b64_second = base64.b64encode(b"\xff\xd8SECOND").decode("ascii")
    api_body = {
        "data": [
            {"b64_json": b64_first},
            {"b64_json": b64_second},
        ],
    }
    fake_response = _json_response(api_body)
    mock_client = _client_with_response(fake_response)

    with patch("lingwen_illustrations.image_generator.httpx.AsyncClient", return_value=mock_client):
        result = await generate(prompt="x", api_key="k", api_host="https://api.test")

    assert result == b"\xff\xd8FIRST"


@pytest.mark.asyncio
async def test_generate_malformed_json_raises_generate_error():
    """If resp.json() raises (non-JSON body), surface as GenerateError."""
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.headers = {}
    fake_response.raise_for_status = MagicMock()
    fake_response.json.side_effect = json.JSONDecodeError("bad", "doc", 0)
    mock_client = _client_with_response(fake_response)

    with patch("lingwen_illustrations.image_generator.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is True
    assert "non-JSON" in str(exc.value)


@pytest.mark.asyncio
async def test_generate_missing_data_array_raises():
    """If response JSON has no 'data' key, surface as GenerateError."""
    fake_response = _json_response({"created": 1234, "no_data_here": []})
    mock_client = _client_with_response(fake_response)

    with patch("lingwen_illustrations.image_generator.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is True
    assert "data" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_generate_empty_data_array_raises():
    """If 'data' is empty, surface as GenerateError (no usable image)."""
    fake_response = _json_response({"data": []})
    mock_client = _client_with_response(fake_response)

    with patch("lingwen_illustrations.image_generator.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is True


@pytest.mark.asyncio
async def test_generate_missing_b64_json_field_raises():
    """If data[0] has no 'b64_json', surface as GenerateError."""
    fake_response = _json_response({"data": [{"url": "https://x"}]})
    mock_client = _client_with_response(fake_response)

    with patch("lingwen_illustrations.image_generator.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is True
    assert "b64_json" in str(exc.value)


@pytest.mark.asyncio
async def test_generate_invalid_base64_raises_generate_error():
    """If b64_json is not valid base64, surface as GenerateError (not crash)."""
    fake_response = _json_response({"data": [{"b64_json": "!!!not-base64!!!"}]})
    mock_client = _client_with_response(fake_response)

    with patch("lingwen_illustrations.image_generator.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is True
    assert "decode" in str(exc.value).lower()


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
async def test_generate_rate_limit_http_date_retry_after_falls_back():
    """IMPORTANT: non-numeric retry-after (HTTP-date form per RFC 7231) must not crash."""
    fake_response = MagicMock()
    fake_response.status_code = 429
    fake_response.headers = {"retry-after": "Wed, 21 Oct 2026 07:28:00 GMT"}
    fake_response.raise_for_status.side_effect = Exception("429")

    mock_client = AsyncMock()
    mock_client.post.return_value = fake_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("lingwen_illustrations.image_generator.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is True
    assert exc.value.retry_after == 60  # fallback for non-numeric header


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
