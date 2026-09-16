"""Stage 3: MiniMax multimodal API call for image generation.

Calls https://api.minimax.chat/v1/image_generation (per minimax-multimodal-toolkit).
Returns raw image bytes (JPEG) decoded from the b64_json field of the API
response. Failures raise GenerateError (retryable) with optional retry_after
from rate-limit headers.

v55.3 Phase 93 — b64_json real decode:
Previously this module returned ``resp.content`` raw bytes, which works only
if the API returned raw bytes. The real MiniMax image API returns JSON like
``{"created": ..., "data": [{"b64_json": "..."}, ...]}`` when
``response_format: b64_json`` is requested. Phase 93 parses the JSON,
extracts ``data[0].b64_json``, base64-decodes it, and returns the JPEG bytes.

Malformed JSON, missing ``data`` array, or absent ``b64_json`` field raise
GenerateError with retryable=True (transient API contract drift).
"""

from __future__ import annotations

import base64
import binascii
import json

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
        api_host: Base URL (e.g. https://api.minimax.chat).
        timeout: HTTP timeout in seconds.

    Returns:
        Raw JPEG image bytes (decoded from b64_json).

    Raises:
        GenerateError: On HTTP / network / timeout / rate-limit / decode failures.
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
        # retry-after may be integer seconds OR HTTP-date (RFC 7231 §7.1.3).
        # Fall back to 60s on non-numeric to keep uniform GenerateError contract.
        raw = resp.headers.get("retry-after", "30")
        try:
            retry_after = int(raw)
        except ValueError:
            retry_after = 60
        raise GenerateError("rate limited", retry_after=retry_after)

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise GenerateError(f"image API HTTP {resp.status_code}: {e}") from e

    # v55.3 Phase 93 — parse JSON response + base64-decode data[0].b64_json.
    # Real MiniMax response shape:
    #   {"created": 1234567890, "data": [{"b64_json": "<base64>"}]}
    try:
        body = resp.json()
    except (json.JSONDecodeError, ValueError) as e:
        raise GenerateError(f"image API non-JSON response: {e}") from e

    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, list) or not data:
        raise GenerateError("image API response missing 'data' array")

    first = data[0]
    if not isinstance(first, dict):
        raise GenerateError("image API data[0] is not an object")

    b64_value = first.get("b64_json")
    if not isinstance(b64_value, str) or not b64_value:
        raise GenerateError("image API data[0] missing 'b64_json' string")

    try:
        return base64.b64decode(b64_value, validate=True)
    except (binascii.Error, ValueError) as e:
        raise GenerateError(f"image API b64_json decode failed: {e}") from e


__all__ = ["generate"]
