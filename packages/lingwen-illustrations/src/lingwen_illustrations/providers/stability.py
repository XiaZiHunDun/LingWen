"""Stability AI SD3 image generation adapter (Phase 96 provider abstraction).

Calls https://api.stability.ai/v2beta/stable-image/generate/sd3.
Returns raw PNG bytes (header Accept: image/* bypasses JSON envelope —
unlike MiniMax/OpenAI which use _b64_decode helper).

multipart/form-data body with prompt + output_format=png.
"""
from __future__ import annotations

import httpx

from lingwen_illustrations.exceptions import GenerateError

_PROVIDER_NAME = "stability"
_DEFAULT_RETRY_AFTER = 30  # Stability v2beta often omits retry-after
SUPPORTS_I2I = True
_DEFAULT_STRENGTH = 0.35


async def generate(
    *,
    prompt: str,
    api_key: str,
    api_host: str,
    timeout: float = 60.0,
) -> bytes:
    """Call Stability AI SD3 image generation API. Returns raw PNG bytes.

    Args:
        prompt: Final composed image prompt (Stage 2 output).
        api_key: Stability API key (from APIConfig.stability_api_key).
        api_host: Base URL (default https://api.stability.ai).
        timeout: HTTP timeout in seconds.

    Returns:
        Raw PNG image bytes (from resp.content — no JSON envelope).

    Raises:
        GenerateError: On HTTP / network / timeout / rate-limit failures.
            All errors have provider="stability".
            4xx errors (except 429) are non-retryable (Phase 96 §5.4):
            invalid_prompt, insufficient_credit, etc.
    """
    url = f"{api_host.rstrip('/')}/v2beta/stable-image/generate/sd3"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "image/*",  # critical: tells Stability to return raw bytes
    }
    # Stability v2beta contract: multipart/form-data with text fields.
    # httpx requires `files=` with (None, value) tuples for text fields in
    # multipart mode. `data=` would send application/x-www-form-urlencoded.
    files = {"prompt": (None, prompt), "output_format": (None, "png")}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers=headers, files=files)
    except httpx.TimeoutException as e:
        raise GenerateError(
            "Stability image API timeout", retry_after=60, provider=_PROVIDER_NAME
        ) from e
    except (httpx.HTTPError, ConnectionError, OSError) as e:
        raise GenerateError(
            f"Stability image API network error: {e}", provider=_PROVIDER_NAME
        ) from e

    if resp.status_code == 429:
        raw = resp.headers.get("retry-after", str(_DEFAULT_RETRY_AFTER))
        try:
            retry_after = int(raw)
        except ValueError:
            retry_after = _DEFAULT_RETRY_AFTER
        raise GenerateError(
            "Stability rate limited", retry_after=retry_after, provider=_PROVIDER_NAME
        )

    # Deviation from plan: direct status_code check (Task 3 pattern).
    # Stability does NOT use _b64_decode helper — returns raw bytes.
    if resp.status_code >= 400:
        retryable = resp.status_code >= 500
        raise GenerateError(
            f"Stability image API HTTP {resp.status_code}",
            provider=_PROVIDER_NAME,
            retryable=retryable,
        )

    # With Accept: image/*, Stability returns raw image bytes — no JSON envelope.
    return resp.content


async def generate_with_reference(
    *,
    prompt: str,
    reference_image_bytes: bytes,
    api_key: str,
    api_host: str,
    strength: float = _DEFAULT_STRENGTH,
    timeout: float = 60.0,
) -> bytes:
    """Call Stability SD3 i2i endpoint. Returns raw PNG bytes via Accept: image/*."""
    url = f"{api_host.rstrip('/')}/v2beta/stable-image/generate/sd3"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "image/*",
    }
    files = {
        "prompt": (None, prompt),
        "image": ("reference.jpg", reference_image_bytes, "image/jpeg"),
        "strength": (None, str(strength)),
        "output_format": (None, "png"),
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers=headers, files=files)
    except httpx.TimeoutException as e:
        raise GenerateError(
            "Stability image API timeout", retry_after=60, provider=_PROVIDER_NAME
        ) from e
    except (httpx.HTTPError, ConnectionError, OSError) as e:
        raise GenerateError(
            f"Stability image API network error: {e}", provider=_PROVIDER_NAME
        ) from e

    if resp.status_code == 429:
        raw = resp.headers.get("retry-after", str(_DEFAULT_RETRY_AFTER))
        try:
            retry_after = int(raw)
        except ValueError:
            retry_after = _DEFAULT_RETRY_AFTER
        raise GenerateError(
            "Stability rate limited", retry_after=retry_after, provider=_PROVIDER_NAME
        )

    if resp.status_code >= 400:
        retryable = resp.status_code >= 500
        raise GenerateError(
            f"Stability image API HTTP {resp.status_code}",
            provider=_PROVIDER_NAME,
            retryable=retryable,
        )

    return resp.content


__all__ = ["generate", "generate_with_reference", "SUPPORTS_I2I"]
