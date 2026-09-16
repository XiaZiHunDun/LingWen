"""Shared b64_json envelope decoder.

Extracted from Phase 93 image_generator.py:90-110 — same safe-decode triad
(isinstance checks at every JSON-traversal level + b64decode(validate=True)).

Used by MiniMax and OpenAI adapters. Stability returns raw bytes and does
NOT use this helper.
"""
from __future__ import annotations

import base64
import binascii
import json

import httpx

from lingwen_illustrations.exceptions import GenerateError


def decode_b64_envelope(resp: httpx.Response, *, provider: str) -> bytes:
    """Decode {"data": [{"b64_json": "..."}]} envelope → raw image bytes.

    Args:
        resp: httpx.Response with status_code 200 already validated by caller.
        provider: provider name (set on GenerateError for error attribution).

    Returns:
        Decoded image bytes (JPEG for MiniMax, PNG for OpenAI DALL-E 3).

    Raises:
        GenerateError: On malformed JSON, missing fields, or invalid base64.
            All errors have provider= set (per Phase 96 spec §5.1 invariant).
    """
    try:
        body = resp.json()
    except (json.JSONDecodeError, ValueError) as e:
        raise GenerateError(f"image API non-JSON response: {e}", provider=provider) from e

    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, list) or not data:
        raise GenerateError("image API response missing 'data' array", provider=provider)

    first = data[0]
    if not isinstance(first, dict):
        raise GenerateError("image API data[0] is not an object", provider=provider)

    b64_value = first.get("b64_json")
    if not isinstance(b64_value, str) or not b64_value:
        raise GenerateError("image API data[0] missing 'b64_json' string", provider=provider)

    try:
        return base64.b64decode(b64_value, validate=True)
    except (binascii.Error, ValueError) as e:
        raise GenerateError(f"image API b64_json decode failed: {e}", provider=provider) from e
