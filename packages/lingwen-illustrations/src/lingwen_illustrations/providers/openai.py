"""OpenAI DALL-E 3 image generation adapter (Phase 96 provider abstraction).

Calls https://api.openai.com/v1/images/generations.
Returns raw PNG bytes decoded from b64_json envelope (same _b64_decode helper
as MiniMax).
"""
from __future__ import annotations

import httpx

from lingwen_illustrations.exceptions import GenerateError
from lingwen_illustrations.providers._b64_decode import decode_b64_envelope

_PROVIDER_NAME = "openai"


async def generate(
    *,
    prompt: str,
    api_key: str,
    api_host: str,
    timeout: float = 60.0,
) -> bytes:
    """Call OpenAI DALL-E 3 image generation API. Returns PNG bytes.

    Args:
        prompt: Final composed image prompt (Stage 2 output).
        api_key: OpenAI API key (from APIConfig.openai_api_key).
        api_host: Base URL (default https://api.openai.com).
        timeout: HTTP timeout in seconds.

    Returns:
        Raw PNG image bytes (decoded from b64_json envelope).

    Raises:
        GenerateError: On HTTP / network / timeout / rate-limit / decode failures.
            All errors have provider="openai".
            4xx errors (except 429) are non-retryable (Phase 96 §5.4):
            content_policy_violation, billing_hard_limit_reached, model_not_found.
    """
    url = f"{api_host.rstrip('/')}/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "response_format": "b64_json",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
    except httpx.TimeoutException as e:
        raise GenerateError(
            "OpenAI image API timeout", retry_after=60, provider=_PROVIDER_NAME
        ) from e
    except (httpx.HTTPError, ConnectionError, OSError) as e:
        raise GenerateError(
            f"OpenAI image API network error: {e}", provider=_PROVIDER_NAME
        ) from e

    if resp.status_code == 429:
        # retry-after may be integer seconds OR HTTP-date (RFC 7231 §7.1.3).
        # Fall back to 60s on non-numeric to keep uniform GenerateError contract.
        raw = resp.headers.get("retry-after", "30")
        try:
            retry_after = int(raw)
        except ValueError:
            retry_after = 60
        raise GenerateError(
            "OpenAI rate limited", retry_after=retry_after, provider=_PROVIDER_NAME
        )

    if resp.status_code >= 400:
        # Per Phase 96 §5.4: 4xx (除 429) are non-retryable user/billing issues,
        # 5xx are retryable server-side failures.
        # Check status_code directly (instead of raise_for_status() exception type)
        # to differentiate retryable vs non-retryable cleanly.
        retryable = resp.status_code >= 500
        raise GenerateError(
            f"OpenAI image API HTTP {resp.status_code}",
            provider=_PROVIDER_NAME,
            retryable=retryable,
        )

    return decode_b64_envelope(resp, provider=_PROVIDER_NAME)


__all__ = ["generate"]
