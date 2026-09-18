"""Phase 100: Stability provider model catalog + threading tests.

Validates KNOWN_MODELS tuple + DEFAULT_MODEL constant + `model` parameter
threading through multipart HTTP request + UnknownModelError on invalid model.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

PNG_MAGIC = b"\x89PNG\r\n\x1a\nfake-png-bytes-here"


def _content_response(content=PNG_MAGIC, status_code=200):
    fake = MagicMock()
    fake.status_code = status_code
    fake.headers = {}
    if status_code == 200:
        fake.content = content
    else:
        fake.raise_for_status.side_effect = Exception(f"{status_code}")
        fake.content = b""
    return fake


def _client_with_response(fake_response):
    mock_client = AsyncMock()
    mock_client.post.return_value = fake_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


def test_stability_known_models_count():
    """Phase 100 catalog: 5 models for Stability (full spec section 3)."""
    from lingwen_illustrations.providers.stability import KNOWN_MODELS

    assert set(KNOWN_MODELS) == {
        "sd3-medium",
        "sd3-large",
        "sd3-large-turbo",
        "stable-image-core",
        "stable-image-ultra",
    }


def test_stability_default_model_in_known_models():
    from lingwen_illustrations.providers.stability import DEFAULT_MODEL, KNOWN_MODELS

    assert DEFAULT_MODEL in KNOWN_MODELS
    assert DEFAULT_MODEL == "sd3-medium"


@pytest.mark.asyncio
async def test_stability_generate_with_explicit_model_sends_in_files():
    """Stability uses multipart files= (not json=) — model goes into files dict."""
    from lingwen_illustrations.providers.stability import generate

    fake = _content_response(PNG_MAGIC)
    mock_client = _client_with_response(fake)

    captured_files = {}

    async def capture_post(*args, **kwargs):
        captured_files.update(kwargs.get("files", {}))
        return fake

    mock_client.post.side_effect = capture_post

    with patch(
        "lingwen_illustrations.providers.stability.httpx.AsyncClient",
        return_value=mock_client,
    ):
        await generate(
            prompt="test",
            api_key="k",
            api_host="https://api.example",
            model="sd3-large",
        )

    # files values are (None, str) tuples; index [1] is the string value
    assert captured_files["model"][1] == "sd3-large"


@pytest.mark.asyncio
async def test_stability_generate_with_none_model_uses_default_in_files():
    from lingwen_illustrations.providers.stability import DEFAULT_MODEL, generate

    fake = _content_response(PNG_MAGIC)
    mock_client = _client_with_response(fake)

    captured_files = {}

    async def capture_post(*args, **kwargs):
        captured_files.update(kwargs.get("files", {}))
        return fake

    mock_client.post.side_effect = capture_post

    with patch(
        "lingwen_illustrations.providers.stability.httpx.AsyncClient",
        return_value=mock_client,
    ):
        await generate(
            prompt="test",
            api_key="k",
            api_host="https://api.example",
            model=None,
        )

    assert captured_files["model"][1] == DEFAULT_MODEL


@pytest.mark.asyncio
async def test_stability_generate_with_invalid_model_raises_unknown():
    from lingwen_illustrations.exceptions import UnknownModelError
    from lingwen_illustrations.providers.stability import generate

    with pytest.raises(UnknownModelError) as exc_info:
        await generate(
            prompt="test",
            api_key="k",
            api_host="https://api.example",
            model="sd99-bogus",
        )
    assert exc_info.value.provider == "stability"
    assert exc_info.value.model == "sd99-bogus"


@pytest.mark.asyncio
async def test_stability_generate_with_reference_signature_accepts_model_kwarg():
    import inspect

    from lingwen_illustrations.providers.stability import generate_with_reference

    sig = inspect.signature(generate_with_reference)
    assert "model" in sig.parameters
    assert sig.parameters["model"].default is None
