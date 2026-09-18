"""Provider i2i adapter tests (Phase 97)."""
from __future__ import annotations

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lingwen_illustrations.exceptions import GenerateError


def test_minimax_supports_i2i_true():
    from lingwen_illustrations.providers import minimax
    assert minimax.SUPPORTS_I2I is True


def test_openai_supports_i2i_false():
    from lingwen_illustrations.providers import openai
    assert openai.SUPPORTS_I2I is False


def test_stability_supports_i2i_true():
    from lingwen_illustrations.providers import stability
    assert stability.SUPPORTS_I2I is True


@pytest.mark.asyncio
async def test_minimax_generate_with_reference_sends_base64():
    from lingwen_illustrations.providers import minimax
    ref = b"\x89PNG\r\n\x1a\nfake-image-bytes"

    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {
        "data": [{"b64_json": base64.b64encode(b"fake-jpeg-bytes").decode("ascii")}]
    }

    with patch("lingwen_illustrations.providers.minimax.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post.return_value = fake_resp
        MockClient.return_value = mock_client

        with patch(
            "lingwen_illustrations.providers.minimax.decode_b64_envelope"
        ) as mock_decode:
            mock_decode.return_value = b"fake-jpeg-bytes"
            result = await minimax.generate_with_reference(
                prompt="test prompt",
                reference_image_bytes=ref,
                api_key="test-key",
                api_host="https://api.test",
            )

    assert result == b"fake-jpeg-bytes"
    call_kwargs = mock_client.__aenter__.return_value.post.call_args.kwargs
    payload = call_kwargs["json"]
    expected_b64 = base64.b64encode(ref).decode("ascii")
    assert payload["image_base64"] == expected_b64
    assert payload["prompt"] == "test prompt"


@pytest.mark.asyncio
async def test_openai_generate_with_reference_raises():
    from lingwen_illustrations.providers import openai
    with pytest.raises(GenerateError) as exc_info:
        await openai.generate_with_reference(
            prompt="test",
            reference_image_bytes=b"any-bytes",
            api_key="test-key",
            api_host="https://api.test",
        )
    assert "does not support" in str(exc_info.value)
    assert exc_info.value.provider == "openai"
    assert exc_info.value.retryable is False


@pytest.mark.asyncio
async def test_stability_generate_with_reference_sends_multipart():
    from lingwen_illustrations.providers import stability
    ref = b"\xff\xd8\xff\xe0fake-jpeg-bytes"

    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.content = b"fake-png-bytes"

    with patch("lingwen_illustrations.providers.stability.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post.return_value = fake_resp
        MockClient.return_value = mock_client

        result = await stability.generate_with_reference(
            prompt="test prompt",
            reference_image_bytes=ref,
            api_key="test-key",
            api_host="https://api.test",
        )

    assert result == b"fake-png-bytes"
    call_kwargs = mock_client.__aenter__.return_value.post.call_args.kwargs
    files = call_kwargs["files"]
    assert files["prompt"] == (None, "test prompt")
    assert files["image"][1] == ref
