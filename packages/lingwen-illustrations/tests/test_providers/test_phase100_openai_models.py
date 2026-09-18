"""Phase 100: OpenAI provider model catalog + threading tests."""
from __future__ import annotations

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

JPEG_MAGIC = b"\xff\xd8\xff\xe0fake-png-bytes-here"


def _json_response(body, status_code=200):
    fake = MagicMock()
    fake.status_code = status_code
    fake.headers = {}
    if status_code == 200:
        fake.json.return_value = body
        fake.content = b""
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


def test_openai_known_models_count():
    """Phase 100 catalog: 4 models for OpenAI (full spec section 3)."""
    from lingwen_illustrations.providers.openai import KNOWN_MODELS

    assert set(KNOWN_MODELS) == {"dall-e-3", "dall-e-3-hd", "dall-e-2", "gpt-image-1"}


def test_openai_default_model_in_known_models():
    from lingwen_illustrations.providers.openai import DEFAULT_MODEL, KNOWN_MODELS

    assert DEFAULT_MODEL in KNOWN_MODELS
    assert DEFAULT_MODEL == "dall-e-3"


@pytest.mark.asyncio
async def test_openai_generate_with_explicit_model_sends_in_payload():
    from lingwen_illustrations.providers.openai import generate

    b64 = base64.b64encode(JPEG_MAGIC).decode("ascii")
    api_body = {"created": 1, "data": [{"b64_json": b64}]}
    fake = _json_response(api_body)
    mock_client = _client_with_response(fake)

    captured_payload = {}

    async def capture_post(*args, **kwargs):
        captured_payload.update(kwargs.get("json", {}))
        return fake

    mock_client.post.side_effect = capture_post

    with patch(
        "lingwen_illustrations.providers.openai.httpx.AsyncClient",
        return_value=mock_client,
    ):
        await generate(
            prompt="test",
            api_key="k",
            api_host="https://api.example",
            model="gpt-image-1",
        )

    assert captured_payload["model"] == "gpt-image-1"


@pytest.mark.asyncio
async def test_openai_generate_with_none_model_uses_default_in_payload():
    from lingwen_illustrations.providers.openai import DEFAULT_MODEL, generate

    b64 = base64.b64encode(JPEG_MAGIC).decode("ascii")
    api_body = {"created": 1, "data": [{"b64_json": b64}]}
    fake = _json_response(api_body)
    mock_client = _client_with_response(fake)

    captured_payload = {}

    async def capture_post(*args, **kwargs):
        captured_payload.update(kwargs.get("json", {}))
        return fake

    mock_client.post.side_effect = capture_post

    with patch(
        "lingwen_illustrations.providers.openai.httpx.AsyncClient",
        return_value=mock_client,
    ):
        await generate(
            prompt="test",
            api_key="k",
            api_host="https://api.example",
            model=None,
        )

    assert captured_payload["model"] == DEFAULT_MODEL


@pytest.mark.asyncio
async def test_openai_generate_with_invalid_model_raises_unknown():
    from lingwen_illustrations.exceptions import UnknownModelError
    from lingwen_illustrations.providers.openai import generate

    with pytest.raises(UnknownModelError) as exc_info:
        await generate(
            prompt="test",
            api_key="k",
            api_host="https://api.example",
            model="dall-e-99",
        )
    assert exc_info.value.provider == "openai"


@pytest.mark.asyncio
async def test_openai_generate_with_reference_signature_accepts_model_kwarg():
    import inspect

    from lingwen_illustrations.providers.openai import generate_with_reference

    sig = inspect.signature(generate_with_reference)
    assert "model" in sig.parameters
    assert sig.parameters["model"].default is None
