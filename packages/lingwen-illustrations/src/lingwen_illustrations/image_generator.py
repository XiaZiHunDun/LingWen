"""Stage 3: MiniMax multimodal API call for image generation.

Calls https://api.MiniMax.chat/v1/image_generation (per minimax-multimodal-toolkit).
Returns raw image bytes (JPEG). Failures raise GenerateError (retryable)
with optional retry_after from rate-limit headers.
"""

from __future__ import annotations

import httpx

from lingwen_illustrations.exceptions import GenerateError


async def generate(
    *,
    prompt: str,
    api_key: str,
    api_host: str,
    timeout: float = 60.0,
) -> bytes:
    """Call MiniMax image generation API. Returns JPEG bytes.

    Args:
        prompt: Final composed image prompt (Stage 2 output).
        api_key: MiniMax API key (from config).
        api_host: Base URL (e.g. https://api.MiniMax.chat).
        timeout: HTTP timeout in seconds.

    Returns:
        Raw JPEG image bytes.

    Raises:
        GenerateError: On HTTP / network / timeout / rate-limit failures.
    """
    url = f"{api_host.rstrip('/')}/v1/image_generation"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "minimax-multimodal",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "response_format": "b64_json",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
    except httpx.TimeoutException as e:
        raise GenerateError(f"image API timeout: {e}", retry_after=60) from e
    except (httpx.HTTPError, ConnectionError, OSError) as e:
        raise GenerateError(f"image API network error: {e}") from e

    if resp.status_code == 429:
        retry_after = int(resp.headers.get("retry-after", "30"))
        raise GenerateError("rate limited", retry_after=retry_after)

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise GenerateError(f"image API HTTP {resp.status_code}: {e}") from e

    return resp.content


__all__ = ["generate"]
