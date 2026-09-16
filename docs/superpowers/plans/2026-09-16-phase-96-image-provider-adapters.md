# Phase 96 — image provider adapters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `packages/lingwen-illustrations/` with a registry-based provider abstraction supporting 3 adapters (MiniMax / OpenAI DALL-E 3 / Stability SD3). Add per-project `default_provider` persisted at `<project>/.lingwen/illustration_settings.yaml` via new `PUT/GET /api/projects/{slug}/settings` endpoint. Update frontend `ProjectSettingsIllustration` + `GenerateIllustrationDialog` with provider pickers.

**Architecture:** `providers/` subpackage with `KNOWN_PROVIDERS = ("minimax", "openai", "stability")` registry. Each adapter exposes `async def generate(*, prompt, api_key, api_host, timeout=60) -> bytes`. Shared `_b64_decode.py` helper for JSON envelope providers (MiniMax + OpenAI). Stability returns raw bytes via `Accept: image/*`. `pipeline.generate_illustration(...)` adds `provider: str = "minimax"` param. `IllustrationMetadata` adds `provider: str = "minimax"` field with backwards-compat `from_dict` injection. `GenerateError` adds `provider` attribute. HTTP error payload adds `provider`. Per-project default persisted via `PUT/GET /api/projects/{slug}/settings` endpoint reading/writing `.lingwen/illustration_settings.yaml` (Pydantic `ProjectSettings` model).

**Tech Stack:** Python 3.12+ / FastAPI / Pydantic / httpx (existing); Vue 3 + Pinia + Vitest; yaml (existing in APIConfig dep chain).

**Workflow notes (LingWen 2026-09-15 simplified):** Direct commits on master, no worktree, no PR. Use `git add` + `git commit` after each task. Run tests with worktree's `.venv/bin/python` if available, else `miniconda3/bin/python` per Phase 56b2.

**Reference:** Spec at `docs/superpowers/specs/2026-09-16-phase-96-image-provider-adapters-design.md` (commit `ebd30455`). Phase 93 handoff (`b64_json real decode`) is baseline — Phase 96 builds ON, not replaces, Phase 93 work.

---

## Phase A: Provider abstraction foundation

### Task 1: Add `provider` field to `GenerateError`

**Files:**
- Modify: `packages/lingwen-illustrations/src/lingwen_illustrations/exceptions.py:54-59`
- Test: `packages/lingwen-illustrations/tests/test_exceptions.py` (existing)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_exceptions.py`:

```python
def test_generate_error_accepts_provider_field():
    """Phase 96: GenerateError must accept `provider` kwarg (default 'unknown')."""
    err = GenerateError("rate limited", retry_after=30, provider="openai")
    assert err.provider == "openai"
    assert err.retry_after == 30
    assert err.retryable is True  # default preserved from Phase 95

def test_generate_error_default_provider_is_unknown():
    err = GenerateError("network error")
    assert err.provider == "unknown"

def test_generate_error_provider_attribute_always_set():
    err = GenerateError("timeout", retry_after=60)
    assert hasattr(err, "provider")
    assert err.provider == "unknown"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/test_exceptions.py -v`
Expected: `TypeError: __init__() got an unexpected keyword argument 'provider'`

- [ ] **Step 3: Implement the change**

In `packages/lingwen-illustrations/src/lingwen_illustrations/exceptions.py`, replace `GenerateError` class:

```python
class GenerateError(IllustrationError):
    """Stage 3 image API failure (rate limit / network / timeout)."""

    def __init__(
        self,
        message: str,
        *,
        retry_after: int | None = None,
        provider: str = "unknown",
    ) -> None:
        super().__init__(Stage.GENERATE, message, retryable=True)
        self.retry_after = retry_after
        self.provider = provider
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/test_exceptions.py -v`
Expected: 3 new tests PASS; existing tests unchanged

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/src/lingwen_illustrations/exceptions.py packages/lingwen-illustrations/tests/test_exceptions.py
git commit -m "feat(phase-96): GenerateError accepts provider kwarg"
```

---

### Task 2: Create `providers/_b64_decode.py` shared helper

**Files:**
- Create: `packages/lingwen-illustrations/src/lingwen_illustrations/providers/__init__.py` (placeholder, full content in Task 6)
- Create: `packages/lingwen-illustrations/src/lingwen_illustrations/providers/_b64_decode.py`
- Test: `packages/lingwen-illustrations/tests/test_providers/__init__.py` (placeholder)
- Test: `packages/lingwen-illustrations/tests/test_providers/test_b64_decode.py`

- [ ] **Step 1: Create subpackage directory + placeholder __init__**

```bash
mkdir -p packages/lingwen-illustrations/src/lingwen_illustrations/providers
touch packages/lingwen-illustrations/src/lingwen_illustrations/providers/__init__.py
mkdir -p packages/lingwen-illustrations/tests/test_providers
touch packages/lingwen-illustrations/tests/test_providers/__init__.py
```

- [ ] **Step 2: Write the failing test for `decode_b64_envelope`**

Create `tests/test_providers/test_b64_decode.py`:

```python
"""Test shared b64_json envelope decoder (Phase 96 _b64_decode helper)."""
from __future__ import annotations
import base64
import json
from unittest.mock import MagicMock

import pytest

from lingwen_illustrations.exceptions import GenerateError
from lingwen_illustrations.providers._b64_decode import decode_b64_envelope


def _json_response(body, status_code=200):
    fake = MagicMock()
    fake.status_code = status_code
    fake.headers = {}
    fake.raise_for_status = MagicMock()
    fake.json.return_value = body
    return fake


def test_decode_returns_b64_decoded_bytes():
    b64 = base64.b64encode(b"hello-world-bytes").decode("ascii")
    api_body = {"created": 1234, "data": [{"b64_json": b64}]}
    resp = _json_response(api_body)
    result = decode_b64_envelope(resp, provider="openai")
    assert result == b"hello-world-bytes"


def test_decode_picks_first_data_item():
    b64_first = base64.b64encode(b"FIRST").decode("ascii")
    b64_second = base64.b64encode(b"SECOND").decode("ascii")
    api_body = {"data": [{"b64_json": b64_first}, {"b64_json": b64_second}]}
    resp = _json_response(api_body)
    assert decode_b64_envelope(resp, provider="openai") == b"FIRST"


def test_decode_malformed_json_raises_with_provider():
    resp = MagicMock()
    resp.json.side_effect = json.JSONDecodeError("bad", "doc", 0)
    with pytest.raises(GenerateError) as exc:
        decode_b64_envelope(resp, provider="stability")
    assert exc.value.provider == "stability"
    assert exc.value.retryable is True


def test_decode_missing_data_array_raises():
    resp = _json_response({"created": 1234, "no_data_here": []})
    with pytest.raises(GenerateError) as exc:
        decode_b64_envelope(resp, provider="openai")
    assert exc.value.provider == "openai"


def test_decode_empty_data_array_raises():
    resp = _json_response({"data": []})
    with pytest.raises(GenerateError) as exc:
        decode_b64_envelope(resp, provider="openai")


def test_decode_missing_b64_json_field_raises():
    resp = _json_response({"data": [{"url": "https://x"}]})
    with pytest.raises(GenerateError) as exc:
        decode_b64_envelope(resp, provider="openai")
    assert "b64_json" in str(exc.value)


def test_decode_invalid_base64_raises():
    resp = _json_response({"data": [{"b64_json": "!!!not-base64!!!"}]})
    with pytest.raises(GenerateError) as exc:
        decode_b64_envelope(resp, provider="openai")
    assert exc.value.provider == "openai"


def test_decode_non_dict_data_item_raises():
    resp = _json_response({"data": ["raw-base64-string"]})
    with pytest.raises(GenerateError) as exc:
        decode_b64_envelope(resp, provider="openai")
    assert "object" in str(exc.value)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/test_providers/test_b64_decode.py -v`
Expected: `ModuleNotFoundError: No module named 'lingwen_illustrations.providers._b64_decode'`

- [ ] **Step 4: Implement `providers/_b64_decode.py`**

Create `packages/lingwen-illustrations/src/lingwen_illustrations/providers/_b64_decode.py`:

```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/test_providers/test_b64_decode.py -v`
Expected: 8 tests PASS

- [ ] **Step 6: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/src/lingwen_illustrations/providers/_b64_decode.py packages/lingwen-illustrations/tests/test_providers/
git commit -m "feat(phase-96): providers/_b64_decode helper (Phase 93 safe-decode triad)"
```

---

### Task 3: Create `providers/minimax.py` adapter

**Files:**
- Create: `packages/lingwen-illustrations/src/lingwen_illustrations/providers/minimax.py`
- Test: `packages/lingwen-illustrations/tests/test_providers/test_minimax.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_providers/test_minimax.py` — port from existing `test_image_generator.py`, change mock target to `providers.minimax.httpx.AsyncClient`:

```python
"""Test Stage 3 MiniMax adapter (Phase 96 provider abstraction).

Same test coverage as Phase 93 test_image_generator.py — ported to target
providers/minimax.py module path.
"""
from __future__ import annotations

import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from lingwen_illustrations.exceptions import GenerateError
from lingwen_illustrations.providers.minimax import generate

JPEG_MAGIC = b"\xff\xd8\xff\xe0fake-jpeg-bytes-here"


def _json_response(body, status_code=200):
    fake = MagicMock()
    fake.status_code = status_code
    fake.headers = {}
    fake.raise_for_status = MagicMock()
    if status_code == 200:
        fake.json.return_value = body
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


@pytest.mark.asyncio
async def test_minimax_returns_decoded_jpeg_bytes():
    b64 = base64.b64encode(JPEG_MAGIC).decode("ascii")
    api_body = {"created": 1234567890, "data": [{"b64_json": b64}]}
    fake = _json_response(api_body)
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.minimax.httpx.AsyncClient",
        return_value=mock_client,
    ):
        result = await generate(
            prompt="test prompt", api_key="k", api_host="https://api.test"
        )
    assert result == JPEG_MAGIC


@pytest.mark.asyncio
async def test_minimax_provider_attribute_set_on_error():
    """All MiniMax errors must have provider='minimax' (Phase 96 §5.1)."""
    fake = _json_response({"data": []})  # empty data array
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.minimax.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.provider == "minimax"


@pytest.mark.asyncio
async def test_minimax_rate_limit_raises_with_provider_and_retry_after():
    fake = MagicMock()
    fake.status_code = 429
    fake.headers = {"retry-after": "30"}
    fake.raise_for_status.side_effect = Exception("429")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.minimax.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.provider == "minimax"
    assert exc.value.retry_after == 30


@pytest.mark.asyncio
async def test_minimax_rate_limit_http_date_fallback():
    fake = MagicMock()
    fake.status_code = 429
    fake.headers = {"retry-after": "Wed, 21 Oct 2026 07:28:00 GMT"}
    fake.raise_for_status.side_effect = Exception("429")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.minimax.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.provider == "minimax"
    assert exc.value.retry_after == 60  # RFC 7231 fallback


@pytest.mark.asyncio
async def test_minimax_network_error_raises():
    mock_client = AsyncMock()
    mock_client.post.side_effect = ConnectionError("network down")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    with patch(
        "lingwen_illustrations.providers.minimax.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.provider == "minimax"
    assert exc.value.retryable is True


@pytest.mark.asyncio
async def test_minimax_timeout_raises():
    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.TimeoutException("timeout")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    with patch(
        "lingwen_illustrations.providers.minimax.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retry_after == 60
    assert exc.value.provider == "minimax"


@pytest.mark.asyncio
async def test_minimax_http_500_raises_retryable():
    fake = MagicMock()
    fake.status_code = 500
    fake.headers = {}
    fake.raise_for_status.side_effect = Exception("500")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.minimax.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is True
    assert exc.value.provider == "minimax"


@pytest.mark.asyncio
async def test_minimax_http_400_raises_non_retryable():
    """Per Phase 96 §5.4: 4xx (除 429) are non-retryable."""
    fake = MagicMock()
    fake.status_code = 400
    fake.headers = {}
    fake.raise_for_status.side_effect = Exception("400")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.minimax.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is False
    assert exc.value.provider == "minimax"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/test_providers/test_minimax.py -v`
Expected: `ModuleNotFoundError: No module named 'lingwen_illustrations.providers.minimax'`

- [ ] **Step 3: Implement `providers/minimax.py`**

Create `packages/lingwen-illustrations/src/lingwen_illustrations/providers/minimax.py`:

```python
"""MiniMax image generation adapter (Phase 96 provider abstraction).

Calls https://api.minimaxi.com/v1/image_generation.
Returns raw JPEG bytes decoded from b64_json envelope (Phase 93 pattern,
extracted to shared providers/_b64_decode.py helper).
"""
from __future__ import annotations

import httpx

from lingwen_illustrations.exceptions import GenerateError
from lingwen_illustrations.providers._b64_decode import decode_b64_envelope

_PROVIDER_NAME = "minimax"


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
        api_key: MiniMax API key (from APIConfig).
        api_host: Base URL (e.g. https://api.minimaxi.com).
        timeout: HTTP timeout in seconds.

    Returns:
        Raw JPEG image bytes (decoded from b64_json envelope).

    Raises:
        GenerateError: On HTTP / network / timeout / rate-limit / decode failures.
            All errors have provider="minimax" (per Phase 96 §5.1 invariant).
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
        raise GenerateError(
            "MiniMax image API timeout", retry_after=60, provider=_PROVIDER_NAME
        ) from e
    except (httpx.HTTPError, ConnectionError, OSError) as e:
        raise GenerateError(
            f"MiniMax image API network error: {e}", provider=_PROVIDER_NAME
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
            "MiniMax rate limited", retry_after=retry_after, provider=_PROVIDER_NAME
        )

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        # Per Phase 96 §5.4: 4xx (除 429) are non-retryable user/billing issues.
        retryable = not (400 <= resp.status_code < 500)
        raise GenerateError(
            f"MiniMax image API HTTP {resp.status_code}: {e}",
            provider=_PROVIDER_NAME,
            retryable=retryable,
        ) from e

    return decode_b64_envelope(resp, provider=_PROVIDER_NAME)


__all__ = ["generate"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/test_providers/test_minimax.py -v`
Expected: 8 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/src/lingwen_illustrations/providers/minimax.py packages/lingwen-illustrations/tests/test_providers/test_minimax.py
git commit -m "feat(phase-96): providers/minimax adapter (Phase 93 logic extracted)"
```

---

### Task 4: Create `providers/openai.py` adapter

**Files:**
- Create: `packages/lingwen-illustrations/src/lingwen_illustrations/providers/openai.py`
- Test: `packages/lingwen-illustrations/tests/test_providers/test_openai.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_providers/test_openai.py`:

```python
"""Test OpenAI DALL-E 3 adapter (Phase 96 provider abstraction).

DALL-E 3 contract:
- Endpoint: https://api.openai.com/v1/images/generations
- Payload: {model: "dall-e-3", prompt, n: 1, size: "1024x1024", response_format: "b64_json"}
- Response: {"created": ..., "data": [{"b64_json": "..."}]}
- Default size: 1024x1024 (other valid: 1024x1792, 1792x1024)
- Returns PNG bytes (DALL-E 3 default).
"""
from __future__ import annotations

import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from lingwen_illustrations.exceptions import GenerateError
from lingwen_illustrations.providers.openai import generate

PNG_MAGIC = b"\x89PNG\r\n\x1a\nfake-png-bytes-here"


def _json_response(body, status_code=200):
    fake = MagicMock()
    fake.status_code = status_code
    fake.headers = {}
    fake.raise_for_status = MagicMock()
    if status_code == 200:
        fake.json.return_value = body
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


@pytest.mark.asyncio
async def test_openai_returns_decoded_png_bytes():
    """Real DALL-E 3 path: b64_json envelope → PNG bytes."""
    b64 = base64.b64encode(PNG_MAGIC).decode("ascii")
    api_body = {"created": 1234567890, "data": [{"b64_json": b64}]}
    fake = _json_response(api_body)
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.openai.httpx.AsyncClient",
        return_value=mock_client,
    ):
        result = await generate(
            prompt="test prompt", api_key="k", api_host="https://api.test"
        )
    assert result == PNG_MAGIC


@pytest.mark.asyncio
async def test_openai_provider_attribute_set_on_all_errors():
    fake = _json_response({"data": []})  # empty data
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.openai.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.provider == "openai"


@pytest.mark.asyncio
async def test_openai_content_policy_raises_non_retryable():
    """HTTP 400 content_policy_violation → non-retryable (user/prompt issue)."""
    fake = MagicMock()
    fake.status_code = 400
    fake.headers = {}
    fake.raise_for_status.side_effect = Exception("400 content_policy_violation")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.openai.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is False
    assert exc.value.provider == "openai"


@pytest.mark.asyncio
async def test_openai_billing_hard_limit_raises_non_retryable():
    fake = MagicMock()
    fake.status_code = 400
    fake.headers = {}
    fake.raise_for_status.side_effect = Exception("400 billing_hard_limit_reached")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.openai.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is False


@pytest.mark.asyncio
async def test_openai_rate_limit_raises_with_retry_after():
    fake = MagicMock()
    fake.status_code = 429
    fake.headers = {"retry-after": "20"}
    fake.raise_for_status.side_effect = Exception("429")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.openai.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retry_after == 20
    assert exc.value.provider == "openai"
    assert exc.value.retryable is True


@pytest.mark.asyncio
async def test_openai_http_500_raises_retryable():
    fake = MagicMock()
    fake.status_code = 500
    fake.headers = {}
    fake.raise_for_status.side_effect = Exception("500")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.openai.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is True


@pytest.mark.asyncio
async def test_openai_model_not_found_raises_non_retryable():
    """HTTP 404 model_not_found → non-retryable config issue."""
    fake = MagicMock()
    fake.status_code = 404
    fake.headers = {}
    fake.raise_for_status.side_effect = Exception("404 model_not_found")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.openai.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is False


@pytest.mark.asyncio
async def test_openai_timeout_raises():
    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.TimeoutException("timeout")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    with patch(
        "lingwen_illustrations.providers.openai.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retry_after == 60
    assert exc.value.provider == "openai"


@pytest.mark.asyncio
async def test_openai_malformed_json_raises():
    resp = MagicMock()
    resp.status_code = 200
    resp.headers = {}
    resp.raise_for_status = MagicMock()
    resp.json.side_effect = json.JSONDecodeError("bad", "doc", 0)
    mock_client = _client_with_response(resp)
    with patch(
        "lingwen_illustrations.providers.openai.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.provider == "openai"
    assert "non-JSON" in str(exc.value)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/test_providers/test_openai.py -v`
Expected: `ModuleNotFoundError: No module named 'lingwen_illustrations.providers.openai'`

- [ ] **Step 3: Implement `providers/openai.py`**

Create `packages/lingwen-illustrations/src/lingwen_illustrations/providers/openai.py`:

```python
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
        raw = resp.headers.get("retry-after", "30")
        try:
            retry_after = int(raw)
        except ValueError:
            retry_after = 60
        raise GenerateError(
            "OpenAI rate limited", retry_after=retry_after, provider=_PROVIDER_NAME
        )

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        retryable = not (400 <= resp.status_code < 500)
        raise GenerateError(
            f"OpenAI image API HTTP {resp.status_code}: {e}",
            provider=_PROVIDER_NAME,
            retryable=retryable,
        ) from e

    return decode_b64_envelope(resp, provider=_PROVIDER_NAME)


__all__ = ["generate"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/test_providers/test_openai.py -v`
Expected: 9 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/src/lingwen_illustrations/providers/openai.py packages/lingwen-illustrations/tests/test_providers/test_openai.py
git commit -m "feat(phase-96): providers/openai adapter (DALL-E 3)"
```

---

### Task 5: Create `providers/stability.py` adapter

**Files:**
- Create: `packages/lingwen-illustrations/src/lingwen_illustrations/providers/stability.py`
- Test: `packages/lingwen-illustrations/tests/test_providers/test_stability.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_providers/test_stability.py`:

```python
"""Test Stability AI SD3 adapter (Phase 96 provider abstraction).

Stability v2beta contract:
- Endpoint: https://api.stability.ai/v2beta/stable-image/generate/sd3
- Headers: Authorization Bearer + Accept: image/*
- Body: multipart/form-data with {prompt, output_format: "png"}
- Response: raw PNG bytes (NOT JSON envelope — header Accept: image/* bypasses JSON)
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from lingwen_illustrations.exceptions import GenerateError
from lingwen_illustrations.providers.stability import generate

PNG_MAGIC = b"\x89PNG\r\n\x1a\nfake-png-bytes-here"


def _raw_response(content, status_code=200, headers=None):
    fake = MagicMock()
    fake.status_code = status_code
    fake.headers = headers or {}
    fake.raise_for_status = MagicMock()
    if status_code == 200:
        fake.content = content
    else:
        fake.raise_for_status.side_effect = Exception(f"{status_code}")
        fake.content = content
    return fake


def _client_with_response(fake_response):
    mock_client = AsyncMock()
    mock_client.post.return_value = fake_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


@pytest.mark.asyncio
async def test_stability_returns_raw_png_bytes():
    """Stability with Accept: image/* returns raw bytes (no envelope)."""
    fake = _raw_response(PNG_MAGIC)
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.stability.httpx.AsyncClient",
        return_value=mock_client,
    ):
        result = await generate(
            prompt="test prompt", api_key="k", api_host="https://api.test"
        )
    assert result == PNG_MAGIC


@pytest.mark.asyncio
async def test_stability_provider_attribute_set():
    fake = MagicMock()
    fake.status_code = 500
    fake.headers = {}
    fake.raise_for_status.side_effect = Exception("500")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.stability.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.provider == "stability"


@pytest.mark.asyncio
async def test_stability_rate_limit_with_retry_after_header():
    fake = MagicMock()
    fake.status_code = 429
    fake.headers = {"retry-after": "15"}
    fake.raise_for_status.side_effect = Exception("429")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.stability.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retry_after == 15
    assert exc.value.provider == "stability"


@pytest.mark.asyncio
async def test_stability_rate_limit_no_retry_after_header():
    """Stability v2beta may not return retry-after — fall back to 30s default."""
    fake = MagicMock()
    fake.status_code = 429
    fake.headers = {}  # no retry-after
    fake.raise_for_status.side_effect = Exception("429")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.stability.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retry_after == 30  # stability-specific default


@pytest.mark.asyncio
async def test_stability_invalid_prompt_raises_non_retryable():
    fake = MagicMock()
    fake.status_code = 400
    fake.headers = {}
    fake.raise_for_status.side_effect = Exception("400 invalid_prompt")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.stability.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is False


@pytest.mark.asyncio
async def test_stability_insufficient_credit_raises_non_retryable():
    fake = MagicMock()
    fake.status_code = 402
    fake.headers = {}
    fake.raise_for_status.side_effect = Exception("402 insufficient_credit")
    mock_client = _client_with_response(fake)
    with patch(
        "lingwen_illustrations.providers.stability.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is False


@pytest.mark.asyncio
async def test_stability_timeout_raises():
    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.TimeoutException("timeout")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    with patch(
        "lingwen_illustrations.providers.stability.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retry_after == 60
    assert exc.value.provider == "stability"


@pytest.mark.asyncio
async def test_stability_network_error_raises():
    mock_client = AsyncMock()
    mock_client.post.side_effect = ConnectionError("network down")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    with patch(
        "lingwen_illustrations.providers.stability.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.provider == "stability"
    assert exc.value.retryable is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/test_providers/test_stability.py -v`
Expected: `ModuleNotFoundError: No module named 'lingwen_illustrations.providers.stability'`

- [ ] **Step 3: Implement `providers/stability.py`**

Create `packages/lingwen-illustrations/src/lingwen_illustrations/providers/stability.py`:

```python
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
    # httpx handles multipart when `data=` dict contains string values.
    form_data = {"prompt": prompt, "output_format": "png"}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers=headers, data=form_data)
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

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        retryable = not (400 <= resp.status_code < 500)
        raise GenerateError(
            f"Stability image API HTTP {resp.status_code}: {e}",
            provider=_PROVIDER_NAME,
            retryable=retryable,
        ) from e

    # With Accept: image/*, Stability returns raw image bytes — no JSON envelope.
    return resp.content


__all__ = ["generate"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/test_providers/test_stability.py -v`
Expected: 8 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/src/lingwen_illustrations/providers/stability.py packages/lingwen-illustrations/tests/test_providers/test_stability.py
git commit -m "feat(phase-96): providers/stability adapter (SD3)"
```

---

### Task 6: Create `providers/__init__.py` registry

**Files:**
- Modify: `packages/lingwen-illustrations/src/lingwen_illustrations/providers/__init__.py` (replace placeholder)
- Test: `packages/lingwen-illustrations/tests/test_providers/test_registry.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_providers/test_registry.py`:

```python
"""Test provider registry (Phase 96 providers/__init__.py)."""
from __future__ import annotations

import pytest

from lingwen_illustrations.providers import (
    DEFAULT_PROVIDER,
    KNOWN_PROVIDERS,
    UnknownProviderError,
    get_provider,
)


def test_known_providers_tuple_is_canonical():
    assert KNOWN_PROVIDERS == ("minimax", "openai", "stability")


def test_default_provider_is_minimax():
    assert DEFAULT_PROVIDER == "minimax"


def test_get_provider_returns_callable_for_each_known():
    for name in KNOWN_PROVIDERS:
        fn = get_provider(name)
        assert callable(fn)
        import inspect
        assert inspect.iscoroutinefunction(fn)


def test_get_provider_minimax_returns_minimax_generate():
    from lingwen_illustrations.providers import minimax
    fn = get_provider("minimax")
    assert fn is minimax.generate


def test_get_provider_unknown_raises():
    with pytest.raises(UnknownProviderError) as exc:
        get_provider("anthropic")
    assert "anthropic" in str(exc.value)
    assert "expected one of" in str(exc.value)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/test_providers/test_registry.py -v`
Expected: `ImportError: cannot import name 'DEFAULT_PROVIDER' from 'lingwen_illustrations.providers'`

- [ ] **Step 3: Implement `providers/__init__.py`**

Replace `packages/lingwen-illustrations/src/lingwen_illustrations/providers/__init__.py`:

```python
"""Image generation provider registry (Phase 96).

Exposes KNOWN_PROVIDERS tuple + get_provider(name) lookup function.
Each provider module (minimax/openai/stability) exports `generate(...)`
with uniform signature: `async def generate(*, prompt, api_key, api_host, timeout=60) -> bytes`.
"""
from lingwen_illustrations.providers import minimax, openai, stability  # noqa: F401

KNOWN_PROVIDERS: tuple[str, ...] = ("minimax", "openai", "stability")
DEFAULT_PROVIDER: str = "minimax"


class UnknownProviderError(ValueError):
    """Raised when get_provider(name) gets a name not in KNOWN_PROVIDERS."""


_REGISTRY: dict[str, "object"] = {
    "minimax": minimax.generate,
    "openai": openai.generate,
    "stability": stability.generate,
}


def get_provider(name: str):
    """Return the adapter generate() callable for the named provider.

    Args:
        name: Provider name (must be one of KNOWN_PROVIDERS).

    Returns:
        Async function with signature (prompt, *, api_key, api_host, timeout=60) -> bytes.

    Raises:
        UnknownProviderError: If name is not in KNOWN_PROVIDERS.
    """
    if name not in _REGISTRY:
        raise UnknownProviderError(
            f"unknown provider '{name}', expected one of {KNOWN_PROVIDERS}"
        )
    return _REGISTRY[name]


__all__ = [
    "KNOWN_PROVIDERS",
    "DEFAULT_PROVIDER",
    "UnknownProviderError",
    "get_provider",
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/test_providers/test_registry.py -v`
Expected: 5 tests PASS

- [ ] **Step 5: Run all provider tests to verify integration**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/test_providers/ -v`
Expected: 8 + 9 + 8 + 5 = 30 tests PASS

- [ ] **Step 6: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/src/lingwen_illustrations/providers/__init__.py packages/lingwen-illustrations/tests/test_providers/test_registry.py
git commit -m "feat(phase-96): providers/__init__.py registry with KNOWN_PROVIDERS + get_provider()"
```

---

### Task 7: Convert `image_generator.py` to thin wrapper

**Files:**
- Modify: `packages/lingwen-illustrations/src/lingwen_illustrations/image_generator.py`
- Test: `packages/lingwen-illustrations/tests/test_image_generator.py` (existing — should still pass)

- [ ] **Step 1: Verify existing test_image_generator tests still pass**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/test_image_generator.py -v`
Expected: Tests currently pass (uses real API code). We'll keep them passing via wrapper delegation.

- [ ] **Step 2: Replace `image_generator.py` content with thin wrapper**

Replace entire file content of `packages/lingwen-illustrations/src/lingwen_illustrations/image_generator.py`:

```python
"""Legacy thin wrapper for backwards compat (Phase 96).

Phase 90-95 callers used `image_generator.generate(prompt, api_key, api_host)`.
Phase 96 redirects this to the MiniMax provider adapter via the registry.
New code should call `lingwen_illustrations.providers.get_provider(name).generate(...)`
directly, or use `pipeline.generate_illustration(..., provider=name)`.

Phase 93 b64_json real decode logic is now in providers/_b64_decode.py —
this module exists only for backwards compatibility with existing test mocks
that patch `lingwen_illustrations.image_generator.httpx.AsyncClient`.
"""
from __future__ import annotations

from lingwen_illustrations.providers import get_provider


async def generate(
    *,
    prompt: str,
    api_key: str,
    api_host: str,
    timeout: float = 60.0,
) -> bytes:
    """Backwards-compatible wrapper. Delegates to MiniMax provider.

    Equivalent to:
        from lingwen_illustrations.providers import get_provider
        return await get_provider("minimax").generate(
            prompt=prompt, api_key=api_key, api_host=api_host, timeout=timeout
        )

    All Phase 93 behavior (b64_json decoding, error mapping) is preserved
    via the providers/minimax.py adapter.
    """
    fn = get_provider("minimax")
    return await fn(
        prompt=prompt, api_key=api_key, api_host=api_host, timeout=timeout
    )


__all__ = ["generate"]
```

- [ ] **Step 3: Update existing test_image_generator mock targets**

Existing `tests/test_image_generator.py` patches `lingwen_illustrations.image_generator.httpx.AsyncClient`. Since the wrapper now delegates to `providers.minimax.generate`, the mock target must change. Edit each test in `test_image_generator.py`:

Find: `patch("lingwen_illustrations.image_generator.httpx.AsyncClient"`
Replace with: `patch("lingwen_illustrations.providers.minimax.httpx.AsyncClient"`

This is a global replace across all tests in the file. Use Edit tool with `replace_all=true`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/test_image_generator.py -v`
Expected: All 11 existing tests PASS

- [ ] **Step 5: Run full illustrations test suite**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/ -v`
Expected: All tests PASS (78 preserved + 30 new = 108 total)

- [ ] **Step 6: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/src/lingwen_illustrations/image_generator.py packages/lingwen-illustrations/tests/test_image_generator.py
git commit -m "refactor(phase-96): image_generator.py → thin wrapper to MiniMax provider"
```

---

## Phase B: Metadata schema + pipeline dispatch

### Task 8: Add `provider` field to `IllustrationMetadata`

**Files:**
- Modify: `packages/lingwen-illustrations/src/lingwen_illustrations/metadata.py:19-56`
- Test: `packages/lingwen-illustrations/tests/test_metadata.py` (existing)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_metadata.py`:

```python
def test_metadata_provider_field_default():
    """Phase 96: provider defaults to 'minimax' for backwards compat."""
    meta = IllustrationMetadata(
        id="x", type="chapter", project_slug="s", chapter_num=1,
        style_preset="ink", custom_prompt=None,
        scene_json={}, final_prompt="p", prompt_hash="h",
        model="minimax-multimodal", created_at="2026-09-16T00:00:00Z",
    )
    assert meta.provider == "minimax"


def test_metadata_provider_field_explicit():
    meta = IllustrationMetadata(
        id="x", type="chapter", project_slug="s", chapter_num=1,
        style_preset="ink", custom_prompt=None,
        scene_json={}, final_prompt="p", prompt_hash="h",
        model="dall-e-3", provider="openai",
        created_at="2026-09-16T00:00:00Z",
    )
    assert meta.provider == "openai"


def test_metadata_from_dict_backwards_compat_missing_provider():
    """Old .meta.json files lack provider field → from_dict injects 'minimax'."""
    old_dict = {
        "id": "x", "type": "chapter", "project_slug": "s", "chapter_num": 1,
        "style_preset": "ink", "custom_prompt": None,
        "scene_json": {}, "final_prompt": "p", "prompt_hash": "h",
        "model": "minimax-multimodal",
        "created_at": "2026-09-16T00:00:00Z",
        # NOTE: no "provider" key
    }
    meta = IllustrationMetadata.from_dict(old_dict)
    assert meta.provider == "minimax"


def test_metadata_from_dict_with_provider():
    new_dict = {
        "id": "x", "type": "chapter", "project_slug": "s", "chapter_num": 1,
        "style_preset": "ink", "custom_prompt": None,
        "scene_json": {}, "final_prompt": "p", "prompt_hash": "h",
        "model": "dall-e-3", "provider": "openai",
        "created_at": "2026-09-16T00:00:00Z",
    }
    meta = IllustrationMetadata.from_dict(new_dict)
    assert meta.provider == "openai"


def test_metadata_to_dict_includes_provider():
    meta = IllustrationMetadata(
        id="x", type="cover", project_slug="s", chapter_num=None,
        style_preset="realistic", custom_prompt=None,
        scene_json={}, final_prompt="p", prompt_hash="h",
        model="sd3-medium", provider="stability",
        created_at="2026-09-16T00:00:00Z",
    )
    d = meta.to_dict()
    assert d["provider"] == "stability"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/test_metadata.py -v`
Expected: `TypeError: __init__() missing 1 required positional argument: 'provider'` (or similar)

- [ ] **Step 3: Implement metadata changes**

In `packages/lingwen-illustrations/src/lingwen_illustrations/metadata.py`, replace `IllustrationMetadata`:

```python
@dataclass(frozen=True)
class IllustrationMetadata:
    """Immutable metadata for one generated illustration asset.

    Phase 96: added `provider` field for per-provider attribution.
    Default 'minimax' for backwards compat with old .meta.json files
    (no provider field). New code always passes provider explicitly.
    """

    id: str
    type: Literal["chapter", "cover"]
    project_slug: str
    chapter_num: int | None  # None for cover
    style_preset: str  # "ink" | "realistic" | "anime"
    custom_prompt: str | None
    scene_json: dict[str, Any]  # Stage 1 output
    final_prompt: str
    prompt_hash: str
    model: str  # "minimax-multimodal" | "dall-e-3" | "sd3-medium" etc.
    provider: str = "minimax"  # NEW (Phase 96). "minimax" | "openai" | "stability".
    created_at: str  # ISO 8601 with trailing Z (UTC)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "IllustrationMetadata":
        # Phase 96 backwards compat: inject "minimax" if old .meta.json
        # lacks provider field (Phase 90-95 era).
        if "provider" not in d:
            d = {**d, "provider": "minimax"}
        try:
            return cls(**d)
        except (KeyError, TypeError) as e:
            from lingwen_illustrations.exceptions import LoadError
            raise LoadError(f"invalid metadata dict: {e}") from e

    @classmethod
    def from_json(cls, raw: str) -> "IllustrationMetadata":
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            from lingwen_illustrations.exceptions import LoadError
            raise LoadError(f"invalid metadata JSON: {e}") from e
        return cls.from_dict(data)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/test_metadata.py -v`
Expected: All tests PASS (existing + 5 new)

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/src/lingwen_illustrations/metadata.py packages/lingwen-illustrations/tests/test_metadata.py
git commit -m "feat(phase-96): IllustrationMetadata + provider field (backwards compat)"
```

---

### Task 9: Update `pipeline.py` to dispatch via `get_provider`

**Files:**
- Modify: `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py:60-205`
- Test: `packages/lingwen-illustrations/tests/test_pipeline.py` (existing)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_pipeline.py`:

```python
@pytest.mark.asyncio
async def test_generate_illustration_dispatches_to_specified_provider(
    monkeypatch, tmp_path
):
    """Phase 96: pipeline should call the named provider's generate()."""
    from lingwen_illustrations import pipeline

    # Set up minimal project layout
    (tmp_path / "chapters" / "001.md").write_text("# Ch 1\ntext", encoding="utf-8")
    (tmp_path / "config" / "illustrations").mkdir(parents=True)
    (tmp_path / "config" / "illustrations" / "characters.json").write_text("[]", encoding="utf-8")

    # Mock scene extract + compose to return predictable values
    monkeypatch.setattr(
        pipeline, "extract_scene",
        lambda chapter_text, character_bible: {"scene": "X"},
    )
    monkeypatch.setattr(
        pipeline, "compose_prompt",
        lambda preset, scene_json, custom_prompt: "FAKE_PROMPT",
    )

    # Track which provider's generate() got called
    called_providers = []
    async def fake_minimax_generate(*, prompt, api_key, api_host, timeout=60.0):
        called_providers.append("minimax")
        return b"\xff\xd8\xff\xe0fake-jpeg"

    async def fake_openai_generate(*, prompt, api_key, api_host, timeout=60.0):
        called_providers.append("openai")
        return b"\x89PNG\r\n\x1a\nfake-png"

    monkeypatch.setattr(
        "lingwen_illustrations.providers.minimax.generate",
        fake_minimax_generate,
    )
    monkeypatch.setattr(
        "lingwen_illustrations.providers.openai.generate",
        fake_openai_generate,
    )

    # Run pipeline with provider="openai"
    meta = await pipeline.generate_illustration(
        project_root=tmp_path,
        project_slug="test",
        type="chapter",
        chapter_num=1,
        style_preset="ink",
        custom_prompt=None,
        api_key="k",
        api_host="https://test",
        provider="openai",
    )

    assert called_providers == ["openai"]
    assert meta.provider == "openai"
    assert meta.model == "dall-e-3"


@pytest.mark.asyncio
async def test_generate_illustration_default_provider_is_minimax(
    monkeypatch, tmp_path
):
    """Default provider (no arg) = 'minimax' (Phase 96 backwards compat)."""
    from lingwen_illustrations import pipeline

    (tmp_path / "chapters" / "001.md").write_text("# Ch 1\ntext", encoding="utf-8")
    (tmp_path / "config" / "illustrations").mkdir(parents=True)
    (tmp_path / "config" / "illustrations" / "characters.json").write_text("[]", encoding="utf-8")

    monkeypatch.setattr(pipeline, "extract_scene", lambda *a, **kw: {})
    monkeypatch.setattr(pipeline, "compose_prompt", lambda *a, **kw: "P")

    called_providers = []
    async def fake_minimax(*, prompt, api_key, api_host, timeout=60.0):
        called_providers.append("minimax")
        return b"\xff\xd8\xff\xe0"

    monkeypatch.setattr(
        "lingwen_illustrations.providers.minimax.generate", fake_minimax,
    )

    meta = await pipeline.generate_illustration(
        project_root=tmp_path, project_slug="s", type="chapter",
        chapter_num=1, style_preset="ink", custom_prompt=None,
        api_key="k", api_host="https://t",
    )
    assert called_providers == ["minimax"]
    assert meta.provider == "minimax"
    assert meta.model == "minimax-multimodal"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/test_pipeline.py -v`
Expected: `TypeError: generate_illustration() got an unexpected keyword argument 'provider'`

- [ ] **Step 3: Implement pipeline changes**

Replace `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py`. Critical changes (full file shown):

```python
"""Pipeline orchestrator: load -> extract -> compose -> generate -> store.

Single entry point for the 4-stage illustration generation pipeline.
Each stage raises a stage-specific exception on failure; the orchestrator
propagates without wrapping.

Phase 96: added `provider: str = "minimax"` parameter to dispatch via
`providers.get_provider(name).generate(...)`. Existing callers without
provider arg default to MiniMax (backwards compat with Phase 90-95).

Layout assumptions (tested + canonical for Phase 90/91/96):
    <project_root>/chapters/<NNN>.md                       — chapter markdown
    <project_root>/config/illustrations/characters.json    — character bible (Phase 91)
    <project_root>/assets/...                              — written by storage

Character bible (Phase 91, P2-ILLUSTRATIONS-BIBLE-CANONICAL):
    Loaded via bible_loader.load_character_bible. Permissive schema:
    list[{name, role, description}]. Missing file silently returns []
    (LLM proceeds with empty character hint). Malformed file raises LoadError.

    Why not ProjectPaths: ProjectPaths enforces canonical layout
    (03_内容仓库/角色设定/character_profiles.json) which doesn't carry
    visual descriptions. Bible is illustration-specific; independent
    of character_profiles.json (no cross-ref, no I073 coupling).

Phase 96: provider abstraction
    Adapters in providers/ subpackage (minimax/openai/stability). Each
    exposes async generate(*, prompt, api_key, api_host, timeout=60) -> bytes.
    Pipeline calls get_provider(provider) for dispatch. ImageGenerator
    provider field on IllustrationMetadata records which provider produced
    each asset (for analytics + future per-provider regeneration).
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from lingwen_illustrations import image_generator, storage
from lingwen_illustrations.bible_loader import load_character_bible
from lingwen_illustrations.exceptions import LoadError
from lingwen_illustrations.metadata import IllustrationMetadata
from lingwen_illustrations.providers import UnknownProviderError, get_provider
from lingwen_illustrations.prompt_builder import extract_scene
from lingwen_illustrations.style_templates import compose as compose_prompt

_TYPE = Literal["cover", "chapter"]

# Per-provider model name for metadata.model field.
_MODEL_FOR_PROVIDER: dict[str, str] = {
    "minimax": "minimax-multimodal",
    "openai": "dall-e-3",
    "stability": "sd3-medium",
}


def _load_chapter_text(project_root: Path, type: _TYPE, chapter_num: int | None) -> str:
    """Load chapter markdown. Empty string for cover type."""
    if type != "chapter":
        return ""
    if chapter_num is None:
        raise LoadError("chapter_num required for chapter type")
    chapter_file = project_root / "chapters" / f"{chapter_num:03d}.md"
    if not chapter_file.exists():
        raise LoadError(f"chapter {chapter_num} not found at {chapter_file}")
    return chapter_file.read_text(encoding="utf-8")


def _iso_utc_now() -> str:
    """ISO 8601 with trailing Z (matches storage.list_assets sort contract)."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _resolve_model(provider: str) -> str:
    if provider not in _MODEL_FOR_PROVIDER:
        raise UnknownProviderError(
            f"unknown provider '{provider}', expected one of {tuple(_MODEL_FOR_PROVIDER)}"
        )
    return _MODEL_FOR_PROVIDER[provider]


async def generate_illustration(
    *,
    project_root: Path,
    project_slug: str,
    type: _TYPE,
    chapter_num: int | None,
    style_preset: str,
    custom_prompt: str | None,
    api_key: str,
    api_host: str,
    provider: str = "minimax",  # NEW (Phase 96)
) -> IllustrationMetadata:
    """Run the full pipeline. Returns metadata of saved asset.

    Phase 96: dispatches Stage 3 to the provider named by `provider`
    (default "minimax" for backwards compat).

    Raises:
        LoadError: Project / chapter / character bible missing or malformed.
        ExtractError: Stage 1 LLM failed.
        ComposeError: Stage 2 template failed (invalid preset).
        GenerateError: Stage 3 image API failed (provider attribution in exc.provider).
        StoreError: Stage 4 file write failed.
        UnknownProviderError: provider name not in providers.KNOWN_PROVIDERS.
    """
    # Stage 1a: load chapter text + character bible.
    chapter_text = _load_chapter_text(project_root, type, chapter_num)
    character_bible = load_character_bible(project_root)

    # Stage 2: LLM extract (raises ExtractError on failure).
    scene_json = extract_scene(
        chapter_text=chapter_text,
        character_bible=character_bible,
    )

    # Stage 3: compose prompt (raises ComposeError on invalid preset).
    final_prompt = compose_prompt(
        style_preset,
        scene_json=scene_json,
        custom_prompt=custom_prompt,
    )

    # Stage 4: provider dispatch (Phase 96). get_provider raises
    # UnknownProviderError if name not in KNOWN_PROVIDERS.
    provider_fn = get_provider(provider)
    image_bytes = await provider_fn(
        prompt=final_prompt,
        api_key=api_key,
        api_host=api_host,
    )

    # Stage 5: store. Build metadata + save.
    asset_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
    prompt_hash = f"sha256:{hashlib.sha256(final_prompt.encode('utf-8')).hexdigest()[:16]}"

    meta = IllustrationMetadata(
        id=asset_id,
        type=type,
        project_slug=project_slug,
        chapter_num=chapter_num,
        style_preset=style_preset,
        custom_prompt=custom_prompt,
        scene_json=scene_json,
        final_prompt=final_prompt,
        prompt_hash=prompt_hash,
        model=_resolve_model(provider),
        provider=provider,  # NEW
        created_at=_iso_utc_now(),
    )

    storage.save_asset(project_root, image_bytes, meta)
    return meta


async def regenerate_illustration(
    *,
    project_root: Path,
    existing_meta: IllustrationMetadata,
    api_key: str,
    api_host: str,
    provider: str | None = None,  # NEW (Phase 96). None → use existing_meta.provider.
) -> IllustrationMetadata:
    """Re-run the extract + compose + generate stages for an existing asset.

    Preserves the original asset_id (v55.4 Phase 94 atomic regenerate).
    Updates scene_json + final_prompt + prompt_hash + created_at to reflect
    the new generation. style_preset + custom_prompt + type + chapter_num
    stay the same as the existing meta.

    Phase 96: `provider` parameter overrides existing_meta.provider.
    If None, reuse the original provider (most common case).

    Atomicity:
    Uses ``storage.replace_asset`` (temp file + POSIX rename) to swap bytes
    in place. Concurrent readers see either the old bytes or the new bytes —
    never a partial mix. If the replace fails (e.g. disk full, permissions),
    the original asset is preserved (no destructive behavior).

    Raises:
        LoadError: Chapter text / character bible missing for regeneration.
        ExtractError: Stage 1 LLM failed (transient).
        ComposeError: Stage 2 template failed (should not happen — preset
            inherited from existing_meta, but defend anyway).
        GenerateError: Stage 3 image API failed (transient).
        StoreError: Stage 4 atomic replace failed.
        UnknownProviderError: provider name not in providers.KNOWN_PROVIDERS.
    """
    effective_provider = provider if provider is not None else existing_meta.provider

    type = existing_meta.type  # type: ignore[assignment]
    chapter_num = existing_meta.chapter_num
    style_preset = existing_meta.style_preset
    custom_prompt = existing_meta.custom_prompt

    # Stage 1a: re-load chapter text + character bible (current state).
    chapter_text = _load_chapter_text(project_root, type, chapter_num)
    character_bible = load_character_bible(project_root)

    # Stage 2: re-run LLM extract.
    scene_json = extract_scene(
        chapter_text=chapter_text,
        character_bible=character_bible,
    )

    # Stage 3: re-compose prompt (preset validated via ComposeError).
    final_prompt = compose_prompt(
        style_preset,
        scene_json=scene_json,
        custom_prompt=custom_prompt,
    )

    # Stage 4: regenerate image bytes via provider.
    provider_fn = get_provider(effective_provider)
    image_bytes = await provider_fn(
        prompt=final_prompt,
        api_key=api_key,
        api_host=api_host,
    )

    # Stage 5: build new metadata (preserve asset_id, refresh dynamic fields).
    prompt_hash = f"sha256:{hashlib.sha256(final_prompt.encode('utf-8')).hexdigest()[:16]}"
    new_meta = IllustrationMetadata(
        id=existing_meta.id,  # preserve identity
        type=existing_meta.type,
        project_slug=existing_meta.project_slug,
        chapter_num=existing_meta.chapter_num,
        style_preset=style_preset,
        custom_prompt=custom_prompt,
        scene_json=scene_json,
        final_prompt=final_prompt,
        prompt_hash=prompt_hash,
        model=_resolve_model(effective_provider),
        provider=effective_provider,
        created_at=_iso_utc_now(),  # refresh timestamp
    )

    # Atomic swap — original preserved if this fails.
    storage.replace_asset(project_root, image_bytes, new_meta)
    return new_meta


__all__ = ["generate_illustration", "regenerate_illustration"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/test_pipeline.py -v`
Expected: All tests PASS (existing 4 + 2 new = 6)

- [ ] **Step 5: Run full illustrations test suite**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/ -v`
Expected: All 108+ tests PASS

- [ ] **Step 6: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py packages/lingwen-illustrations/tests/test_pipeline.py
git commit -m "feat(phase-96): pipeline dispatches via get_provider(provider) + provider param"
```

---

## Phase C: Backend persistence + routes

### Task 10: Extend APIConfig with stability/openai hosts

**Files:**
- Modify: `packages/lingwen-config/src/lingwen_config/api_config_loader.py:79-86`

- [ ] **Step 1: Add `openai_api_host` + `stability_api_key` + `stability_api_host` properties**

Append after the existing `openai_api_key` property in `api_config_loader.py`:

```python
    @property
    def openai_api_key(self) -> Optional[str]:
        return self.get("openai_api_key")

    @property
    def openai_api_host(self) -> Optional[str]:
        # Phase 96: forward-looking property for OpenAI DALL-E 3 adapter.
        return self.get("openai_api_host", "https://api.openai.com")

    @property
    def stability_api_key(self) -> Optional[str]:
        # Phase 96: new key for Stability AI SD3 adapter.
        return self.get("stability_api_key")

    @property
    def stability_api_host(self) -> Optional[str]:
        # Phase 96: forward-looking property for Stability SD3 adapter.
        return self.get("stability_api_host", "https://api.stability.ai")

    @property
    def anthropic_api_key(self) -> Optional[str]:
        # Phase 83 forward-looking; NOT used by Phase 96 (Anthropic has no
        # native image API). Property retained for forward compat with
        # future Anthropic-based image gen (e.g., Stable Diffusion XL via
        # Anthropic prompt chain — not v1).
        return self.get("anthropic_api_key")
```

- [ ] **Step 2: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-config/src/lingwen_config/api_config_loader.py
git commit -m "feat(phase-96): APIConfig + openai_api_host + stability_api_key/host"
```

---

### Task 11: Extract `_project_root_for` helper to shared module

**Files:**
- Create: `apps/studio_api/routes/_project_helpers.py`
- Modify: `apps/studio_api/routes/illustrations.py` (import from new module)

- [ ] **Step 1: Create helper module**

Create `apps/studio_api/routes/_project_helpers.py`:

```python
"""Shared project helpers (Phase 96).

Extracted from apps/studio_api/routes/illustrations.py for reuse across
project_settings.py and other future per-project routes.
"""
from __future__ import annotations

from pathlib import Path

from lingwen_illustrations.exceptions import LoadError


def project_root_for(slug: str) -> Path:
    """Resolve project root from slug.

    v1: scan `projects/` for the slug. Uses cwd-relative resolution so
    tests can `monkeypatch.chdir(tmp_path)` to isolate per-test.

    Phase 96: extracted from illustrations.py for reuse by project_settings.py.
    """
    candidate = Path("projects") / slug
    if not candidate.exists():
        raise LoadError(f"project '{slug}' not found at {candidate}")
    return candidate


__all__ = ["project_root_for"]
```

- [ ] **Step 2: Update `illustrations.py` to use the shared helper**

In `apps/studio_api/routes/illustrations.py`:

Find: `def _project_root_for(slug: str) -> Path:`
Replace with: `# Phase 96: _project_root_for extracted to _project_helpers.py`
And remove the entire function body up to the `return candidate` line.

Then change the call sites: find all `_project_root_for(` → `project_root_for(` (from `_project_helpers`).

Add import at top of file: `from apps.studio_api.routes._project_helpers import project_root_for`

- [ ] **Step 3: Verify existing illustrations tests still pass**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_illustrations_api.py -v`
Expected: All existing tests PASS

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/studio_api/routes/_project_helpers.py apps/studio_api/routes/illustrations.py
git commit -m "refactor(phase-96): extract _project_root_for to _project_helpers for reuse"
```

---

### Task 12: Create `project_settings.py` route (PUT/GET)

**Files:**
- Create: `apps/studio_api/routes/project_settings.py`
- Test: `apps/studio_api/tests/test_project_settings_api.py`

- [ ] **Step 1: Write the failing test**

Create `apps/studio_api/tests/test_project_settings_api.py`:

```python
"""Test PUT/GET /api/projects/{slug}/settings (Phase 96)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.studio_api.app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """TestClient with tmp_path as project_root parent."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "projects" / "test-slug").mkdir(parents=True)
    app = create_app()
    return TestClient(app)


def test_get_settings_returns_defaults_when_yaml_missing(client):
    """No yaml on disk → returns ProjectSettings() with default_provider='minimax'."""
    resp = client.get("/api/projects/test-slug/settings")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"default_provider": "minimax"}


def test_put_settings_persists_yaml(client):
    resp = client.put(
        "/api/projects/test-slug/settings",
        json={"default_provider": "openai"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"default_provider": "openai"}

    yaml_path = Path("projects") / "test-slug" / ".lingwen" / "illustration_settings.yaml"
    assert yaml_path.exists()
    assert yaml_path.read_text(encoding="utf-8").strip() == "default_provider: openai"


def test_put_then_get_round_trips(client):
    client.put("/api/projects/test-slug/settings", json={"default_provider": "stability"})
    resp = client.get("/api/projects/test-slug/settings")
    assert resp.json() == {"default_provider": "stability"}


def test_get_settings_corrupt_yaml_returns_defaults(client, tmp_path):
    """Corrupt yaml file → silently fallback to defaults (Phase 96 §3.8)."""
    yaml_path = tmp_path / "projects" / "test-slug" / ".lingwen"
    yaml_path.mkdir(parents=True)
    (yaml_path / "illustration_settings.yaml").write_text("not: valid: yaml: [", encoding="utf-8")

    resp = client.get("/api/projects/test-slug/settings")
    assert resp.status_code == 200
    assert resp.json() == {"default_provider": "minimax"}


def test_put_settings_invalid_provider_rejected(client):
    """Pydantic Literal validation: unknown provider name → 422."""
    resp = client.put(
        "/api/projects/test-slug/settings",
        json={"default_provider": "anthropic"},  # not in Literal
    )
    assert resp.status_code == 422


def test_put_settings_unknown_project_404(client):
    """Project slug not in projects/ → 404."""
    resp = client.put(
        "/api/projects/nonexistent-slug/settings",
        json={"default_provider": "openai"},
    )
    assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_project_settings_api.py -v`
Expected: `ModuleNotFoundError: No module named 'apps.studio_api.routes.project_settings'`

- [ ] **Step 3: Implement `project_settings.py`**

Create `apps/studio_api/routes/project_settings.py`:

```python
"""Project settings persistence (Phase 96).

PUT/GET /api/projects/{slug}/settings — stores per-project illustration
preferences (default_provider) at <project_root>/.lingwen/illustration_settings.yaml.

Extends Phase 95 deferred work ("持久化在 v2 走 /api/projects/{slug}/settings").
Future phases add fields (auto_generate, max_assets, confirm_before_generate)
without breaking schema (Pydantic Literal + Optional fields).
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError

from apps.studio_api.routes._project_helpers import project_root_for
from lingwen_illustrations.exceptions import LoadError

# Future fields (auto_generate, max_assets, confirm_before_generate) added
# in subsequent phases without breaking this schema.
class ProjectSettings(BaseModel):
    default_provider: Literal["minimax", "openai", "stability"] = "minimax"


def _settings_path(project_root: Path) -> Path:
    return project_root / ".lingwen" / "illustration_settings.yaml"


def _save_settings(project_root: Path, settings: ProjectSettings) -> None:
    target = _settings_path(project_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        yaml.safe_dump(settings.model_dump(), allow_unicode=True),
        encoding="utf-8",
    )


def _load_settings(project_root: Path) -> ProjectSettings:
    """Load settings, silently falling back to defaults on missing/corrupt yaml.

    Returns ProjectSettings() (all defaults) when:
    - yaml file does not exist
    - yaml is malformed (YAMLError)
    - yaml content fails Pydantic validation (ValidationError)
    """
    target = _settings_path(project_root)
    if not target.exists():
        return ProjectSettings()
    try:
        data = yaml.safe_load(target.read_text(encoding="utf-8"))
        return ProjectSettings(**(data or {}))
    except (yaml.YAMLError, ValidationError):
        return ProjectSettings()


def register_project_settings(app: FastAPI, ctx: object) -> None:
    """Mount /api/projects/{slug}/settings routes."""

    @app.put("/api/projects/{slug}/settings", response_model=ProjectSettings)
    async def put_settings(slug: str, settings: ProjectSettings) -> ProjectSettings:
        try:
            root = project_root_for(slug)
        except LoadError as e:
            raise HTTPException(404, detail={"stage": "load", "error": e.message})
        _save_settings(root, settings)
        return settings

    @app.get("/api/projects/{slug}/settings", response_model=ProjectSettings)
    def get_settings(slug: str) -> ProjectSettings:
        try:
            root = project_root_for(slug)
        except LoadError as e:
            raise HTTPException(404, detail={"stage": "load", "error": e.message})
        return _load_settings(root)


__all__ = ["register_project_settings", "ProjectSettings"]
```

- [ ] **Step 4: Register the route in app**

Find `apps/studio_api/app.py` and locate where `register_illustrations` is called. Add:

```python
from apps.studio_api.routes.project_settings import register_project_settings
# ...
register_project_settings(app, ctx)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_project_settings_api.py -v`
Expected: 6 tests PASS

- [ ] **Step 6: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/studio_api/routes/project_settings.py apps/studio_api/tests/test_project_settings_api.py apps/studio_api/app.py
git commit -m "feat(phase-96): PUT/GET /api/projects/{slug}/settings endpoint"
```

---

### Task 13: Update illustrations route with provider field + `_api_credentials_for`

**Files:**
- Modify: `apps/studio_api/routes/illustrations.py`
- Modify: `apps/studio_api/tests/test_illustrations_api.py`

- [ ] **Step 1: Add provider field to `GenerateRequest`**

In `apps/studio_api/routes/illustrations.py`, modify `GenerateRequest`:

```python
class GenerateRequest(BaseModel):
    project_slug: str
    type: str = Field(pattern="^(cover|chapter)$")
    chapter_num: Optional[int] = None
    style_preset: str
    custom_prompt: Optional[str] = None
    provider: Optional[str] = None  # NEW (Phase 96). None → fetch from project settings.
```

- [ ] **Step 2: Add `_api_credentials_for` helper**

Replace existing `_api_credentials()` with two functions:

```python
def _api_credentials_for(provider: str) -> tuple[str, str]:
    """Dispatch API key + host by provider name.

    Phase 96: replaces _api_credentials() which only handled MiniMax.
    Raises ValueError for unknown provider (caller should validate first
    via providers.KNOWN_PROVIDERS).
    """
    from lingwen_config import APIConfig
    cfg = APIConfig()
    if provider == "minimax":
        return cfg.minimax_api_key or "", cfg.minimax_api_host or "https://api.minimaxi.com"
    if provider == "openai":
        return cfg.openai_api_key or "", cfg.openai_api_host or "https://api.openai.com"
    if provider == "stability":
        return cfg.stability_api_key or "", cfg.stability_api_host or "https://api.stability.ai"
    raise ValueError(f"unknown provider '{provider}'")


def _resolve_provider_for_request(req_project_slug: str, body_provider: Optional[str]) -> str:
    """Resolve provider with priority: body > project_settings > 'minimax'.

    Phase 96 §3.7 single source of truth.
    """
    from apps.studio_api.routes.project_settings import ProjectSettings, _load_settings
    from lingwen_illustrations.providers import KNOWN_PROVIDERS

    if body_provider is not None:
        if body_provider not in KNOWN_PROVIDERS:
            raise HTTPException(
                status_code=400,
                detail=f"unknown provider '{body_provider}', expected one of {KNOWN_PROVIDERS}",
            )
        return body_provider
    try:
        root = project_root_for(req_project_slug)
        settings = _load_settings(root)
    except LoadError:
        return "minimax"
    return settings.default_provider
```

- [ ] **Step 3: Update `generate_illustration` route handler**

Modify the `generate_illustration` route body:

```python
    @app.post("/api/illustrations/generate", response_model=GenerateResponse)
    async def generate_illustration(req: GenerateRequest = Body(...)) -> GenerateResponse:
        try:
            project_root = project_root_for(req.project_slug)
        except LoadError as e:
            raise HTTPException(404, detail=_err_detail(e)) from e

        provider = _resolve_provider_for_request(req.project_slug, req.provider)
        api_key, api_host = _api_credentials_for(provider)

        from lingwen_illustrations.pipeline import generate_illustration as run_pipeline

        try:
            meta = await run_pipeline(
                project_root=project_root,
                project_slug=req.project_slug,
                type=req.type,
                chapter_num=req.chapter_num,
                style_preset=req.style_preset,
                custom_prompt=req.custom_prompt,
                api_key=api_key,
                api_host=api_host,
                provider=provider,
            )
        except IllustrationError as e:
            _raise_stage_error(e)

        return GenerateResponse(
            id=meta.id,
            type=meta.type,
            chapter_num=meta.chapter_num,
            style_preset=meta.style_preset,
            scene_json=meta.scene_json,
            url=f"/api/illustrations/{meta.id}/image?project_slug={req.project_slug}",
        )
```

- [ ] **Step 4: Update `_err_detail` to include provider field**

```python
def _err_detail(exc: IllustrationError) -> dict:
    """Build the standard error detail payload."""
    payload = {"stage": exc.stage.value, "error": exc.message, "retryable": exc.retryable}
    if isinstance(exc, GenerateError):
        if exc.retry_after is not None:
            payload["retry_after"] = exc.retry_after
        payload["provider"] = exc.provider  # NEW (Phase 96)
    return payload
```

- [ ] **Step 5: Update regenerate route to accept `?provider=` query param**

Modify the `regenerate_illustration` route signature and body:

```python
    @app.put("/api/illustrations/{asset_id}/regenerate", response_model=GenerateResponse)
    async def regenerate_illustration(
        asset_id: str,
        project_slug: str = Query(...),
        provider: Optional[str] = Query(None),  # NEW (Phase 96). None → existing_meta.provider.
    ) -> GenerateResponse:
        """Atomic regenerate: re-runs extract+compose+generate, swaps bytes in place.

        Phase 96: provider query param overrides existing_meta.provider. If None,
        reuse the original provider (most common case).
        """
        try:
            project_root = project_root_for(project_slug)
        except LoadError as e:
            raise HTTPException(404, detail=_err_detail(e)) from e

        all_assets = storage.list_assets(project_root)
        meta = next((a for a in all_assets if a.id == asset_id), None)
        if meta is None:
            raise HTTPException(404, detail=f"asset {asset_id} not found")

        effective_provider = provider if provider is not None else meta.provider
        api_key, api_host = _api_credentials_for(effective_provider)

        from lingwen_illustrations.pipeline import regenerate_illustration as run_regen

        try:
            new_meta = await run_regen(
                project_root=project_root,
                existing_meta=meta,
                api_key=api_key,
                api_host=api_host,
                provider=provider,  # None → pipeline reads existing_meta.provider
            )
        except IllustrationError as e:
            _raise_stage_error(e)

        return GenerateResponse(
            id=new_meta.id,
            type=new_meta.type,
            chapter_num=new_meta.chapter_num,
            style_preset=new_meta.style_preset,
            scene_json=new_meta.scene_json,
            url=f"/api/illustrations/{new_meta.id}/image?project_slug={project_slug}",
        )
```

- [ ] **Step 6: Write tests for provider field on illustrations route**

Add to `apps/studio_api/tests/test_illustrations_api.py`:

```python
def test_generate_request_accepts_provider_field():
    """Phase 96: provider is optional in body; defaults via project settings."""
    from apps.studio_api.routes.illustrations import GenerateRequest
    req = GenerateRequest(
        project_slug="x", type="chapter", chapter_num=1,
        style_preset="ink", custom_prompt=None, provider="openai",
    )
    assert req.provider == "openai"


def test_generate_request_provider_optional():
    from apps.studio_api.routes.illustrations import GenerateRequest
    req = GenerateRequest(
        project_slug="x", type="chapter", chapter_num=1,
        style_preset="ink", custom_prompt=None,
    )
    assert req.provider is None


def test_err_detail_includes_provider_for_generate_error():
    """Phase 96 §5.2: HTTP error payload includes provider."""
    from apps.studio_api.routes.illustrations import _err_detail
    from lingwen_illustrations.exceptions import GenerateError
    err = GenerateError("test", retry_after=30, provider="openai")
    detail = _err_detail(err)
    assert detail["provider"] == "openai"
    assert detail["retry_after"] == 30


def test_err_detail_no_provider_for_non_generate_error():
    """Non-GenerateError exceptions don't have provider field."""
    from apps.studio_api.routes.illustrations import _err_detail
    from lingwen_illustrations.exceptions import LoadError
    err = LoadError("missing file")
    detail = _err_detail(err)
    assert "provider" not in detail


def test_api_credentials_for_each_provider(monkeypatch):
    """_api_credentials_for dispatches API key + host by provider name."""
    from apps.studio_api.routes.illustrations import _api_credentials_for

    # Mock APIConfig to return predictable values
    from lingwen_config import APIConfig
    cfg = APIConfig()

    monkeypatch.setattr(cfg, "minimax_api_key", "minimax-key")
    monkeypatch.setattr(cfg, "openai_api_key", "openai-key")
    monkeypatch.setattr(cfg, "stability_api_key", "stability-key")

    key, host = _api_credentials_for("minimax")
    assert key == "minimax-key"
    assert host == "https://api.minimaxi.com"

    key, host = _api_credentials_for("openai")
    assert key == "openai-key"
    assert host == "https://api.openai.com"

    key, host = _api_credentials_for("stability")
    assert key == "stability-key"
    assert host == "https://api.stability.ai"


def test_api_credentials_for_unknown_raises():
    from apps.studio_api.routes.illustrations import _api_credentials_for
    with pytest.raises(ValueError) as exc:
        _api_credentials_for("anthropic")
    assert "anthropic" in str(exc.value)
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/ -v`
Expected: All tests PASS (existing 90 + new ~10)

- [ ] **Step 8: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/studio_api/routes/illustrations.py apps/studio_api/tests/test_illustrations_api.py
git commit -m "feat(phase-96): illustrations route + provider field + _api_credentials_for"
```

---

### Task 14: Update background task `_get_illustration_settings`

**Files:**
- Modify: `apps/studio_api/background.py:58-67`

- [ ] **Step 1: Update `_get_illustration_settings` to read from yaml**

Replace `apps/studio_api/background.py:58-67`:

```python
def _get_illustration_settings(project_slug: str) -> dict[str, Any]:
    """Read illustration settings for the project.

    Phase 96: reads from <project>/.lingwen/illustration_settings.yaml
    (populated by PUT /api/projects/{slug}/settings). Falls back to
    defaults (auto_generate OFF, style_preset 'ink', default_provider
    'minimax') when yaml is missing or corrupt.

    Future fields (max_assets, confirm_before_generate) will be added
    here when ProjectSettings schema extends.
    """
    from apps.studio_api.routes._project_helpers import project_root_for
    from apps.studio_api.routes.project_settings import _load_settings
    from lingwen_illustrations.exceptions import LoadError

    try:
        root = project_root_for(project_slug)
        settings = _load_settings(root)
    except LoadError:
        # Project not found — silent no-op (matches existing Phase 90 behavior).
        return {
            "style_preset": "ink",
            "auto_generate": False,
            "default_provider": "minimax",
        }

    return {
        "style_preset": "ink",  # TODO v2: add style_preset to ProjectSettings
        "auto_generate": False,  # TODO v2: add auto_generate to ProjectSettings
        "default_provider": settings.default_provider,
    }


__all__ = ["illustrations_auto_generate_task", "_get_illustration_settings"]
```

Also update `illustrations_auto_generate_task` to pass `provider=settings.get("default_provider", "minimax")`:

```python
    try:
        project_root = _project_root_for(project_slug)
        provider = settings.get("default_provider", "minimax")
        api_key, api_host = _api_credentials_for(provider)
        await generate_illustration(
            project_root=project_root,
            project_slug=project_slug,
            type="chapter",
            chapter_num=chapter_num,
            style_preset=settings.get("style_preset", "ink"),
            custom_prompt=None,
            api_key=api_key,
            api_host=api_host,
            provider=provider,
        )
```

And update the error log to include provider (per §5.6):

```python
    except IllustrationError as e:
        log.warning(
            f"auto-generate failed [{e.stage.value}] "
            f"provider={getattr(e, 'provider', 'unknown')}: {e.message}"
        )
```

- [ ] **Step 2: Verify existing studio_api tests still pass**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/ -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/studio_api/background.py
git commit -m "feat(phase-96): background task reads default_provider from project settings"
```

---

## Phase D: Frontend

### Task 15: Create `useProjectSettings.js` Pinia store

**Files:**
- Create: `apps/dashboard/src/stores/useProjectSettings.js`
- Test: `apps/dashboard/src/stores/useProjectSettings.spec.js` (or `.test.js`)

- [ ] **Step 1: Read existing store conventions**

Run: `ls apps/dashboard/src/stores/` to see existing Pinia store naming patterns.

- [ ] **Step 2: Create the store**

Create `apps/dashboard/src/stores/useProjectSettings.js`:

```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * Project settings Pinia store (Phase 96).
 *
 * State: { settings: { default_provider } | null, slug: string | null, loading: bool }
 * Actions: { fetch(slug), save(slug, partial) }
 *
 * Backed by PUT/GET /api/projects/{slug}/settings endpoint.
 */
export const useProjectSettingsStore = defineStore('projectSettings', () => {
  const settings = ref(null)
  const slug = ref(null)
  const loading = ref(false)

  async function fetch(targetSlug) {
    if (!targetSlug) return
    loading.value = true
    slug.value = targetSlug
    try {
      const resp = await fetch(`/api/projects/${targetSlug}/settings`)
      if (resp.ok) {
        settings.value = await resp.json()
      } else {
        settings.value = { default_provider: 'minimax' }
      }
    } catch {
      settings.value = { default_provider: 'minimax' }
    } finally {
      loading.value = false
    }
  }

  async function save(targetSlug, partial) {
    const current = settings.value || { default_provider: 'minimax' }
    const next = { ...current, ...partial }
    loading.value = true
    try {
      const resp = await fetch(`/api/projects/${targetSlug}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(next),
      })
      if (resp.ok) {
        settings.value = await resp.json()
      } else {
        throw new Error(`save failed: ${resp.status}`)
      }
    } finally {
      loading.value = false
    }
  }

  return { settings, slug, loading, fetch, save }
})
```

- [ ] **Step 3: Write test**

Create `apps/dashboard/src/stores/useProjectSettings.spec.js`:

```javascript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useProjectSettingsStore } from './useProjectSettings.js'

describe('useProjectSettingsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    globalThis.fetch = vi.fn()
  })

  it('fetch loads settings from API', async () => {
    globalThis.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ default_provider: 'openai' }),
    })
    const store = useProjectSettingsStore()
    await store.fetch('test-slug')
    expect(store.settings).toEqual({ default_provider: 'openai' })
    expect(store.slug).toBe('test-slug')
  })

  it('fetch falls back to defaults on 404', async () => {
    globalThis.fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({}),
    })
    const store = useProjectSettingsStore()
    await store.fetch('test-slug')
    expect(store.settings).toEqual({ default_provider: 'minimax' })
  })

  it('fetch falls back to defaults on network error', async () => {
    globalThis.fetch.mockRejectedValueOnce(new Error('network'))
    const store = useProjectSettingsStore()
    await store.fetch('test-slug')
    expect(store.settings).toEqual({ default_provider: 'minimax' })
  })

  it('save persists to API', async () => {
    globalThis.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ default_provider: 'stability' }),
    })
    const store = useProjectSettingsStore()
    store.settings = { default_provider: 'minimax' }
    await store.save('test-slug', { default_provider: 'stability' })
    expect(store.settings).toEqual({ default_provider: 'stability' })
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/projects/test-slug/settings',
      expect.objectContaining({ method: 'PUT' }),
    )
  })

  it('save throws on non-ok response', async () => {
    globalThis.fetch.mockResolvedValueOnce({ ok: false, status: 500 })
    const store = useProjectSettingsStore()
    store.settings = { default_provider: 'minimax' }
    await expect(store.save('test-slug', { default_provider: 'openai' }))
      .rejects.toThrow('save failed: 500')
  })
})
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/stores/useProjectSettings.spec.js`
Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/stores/useProjectSettings.js apps/dashboard/src/stores/useProjectSettings.spec.js
git commit -m "feat(phase-96): useProjectSettings Pinia store + tests"
```

---

### Task 16: Update `ProjectSettingsIllustration.vue` with provider dropdown

**Files:**
- Modify: `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue`
- Test: `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.spec.js` (existing)

- [ ] **Step 1: Add `slug` prop + provider dropdown**

Modify the `<script setup>` block:

```javascript
<script setup>
import { useProjectSettingsStore } from '@/stores/useProjectSettings.js'

const props = defineProps({
  modelValue: { type: Object, required: true },
  slug: { type: String, required: true },  // NEW (Phase 96)
})
const emit = defineEmits(['update:modelValue'])

const store = useProjectSettingsStore()

const presets = [
  { id: 'ink', label: '古风水墨' },
  { id: 'realistic', label: '现代写实' },
  { id: 'anime', label: '动漫厚涂' },
]

const providers = [
  { id: 'minimax', label: 'MiniMax' },
  { id: 'openai', label: 'OpenAI DALL-E 3' },
  { id: 'stability', label: 'Stability SD3' },
]

function update(key, value) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}

async function on_provider_change(value) {
  update('default_provider', value)
  await store.save(props.slug, { default_provider: value })
}
</script>
```

Add this section in the template (after the existing auto-generate toggle):

```html
    <div class="field project-settings-illustration-field">
      <label class="project-settings-illustration-label" for="project-settings-illustration-default-provider">
        默认图片生成器
      </label>
      <select
        id="project-settings-illustration-default-provider"
        class="project-settings-illustration-provider-select"
        :value="modelValue.default_provider || 'minimax'"
        data-testid="project-settings-illustration-default-provider"
        @change="on_provider_change($event.target.value)"
      >
        <option v-for="p in providers" :key="p.id" :value="p.id">
          {{ p.label }}
        </option>
      </select>
    </div>
```

- [ ] **Step 2: Add component test for new dropdown**

Add to `ProjectSettingsIllustration.spec.js`:

```javascript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ProjectSettingsIllustration from './ProjectSettingsIllustration.vue'

describe('ProjectSettingsIllustration (Phase 96: provider dropdown)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    globalThis.fetch = vi.fn()
  })

  it('renders default_provider dropdown with three options', () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          style_preset: 'ink',
          auto_generate: false,
          max_assets: 10,
          confirm_before_generate: true,
          default_provider: 'minimax',
        },
        slug: 'test',
      },
    })
    const select = wrapper.find('[data-testid="project-settings-illustration-default-provider"]')
    expect(select.exists()).toBe(true)
    const options = select.findAll('option')
    expect(options.length).toBe(3)
    expect(options.map(o => o.attributes('value'))).toEqual(['minimax', 'openai', 'stability'])
  })

  it('selects current default_provider value', () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          style_preset: 'ink', auto_generate: false,
          max_assets: 10, confirm_before_generate: true,
          default_provider: 'openai',
        },
        slug: 'test',
      },
    })
    const select = wrapper.find('[data-testid="project-settings-illustration-default-provider"]')
    expect(select.element.value).toBe('openai')
  })

  it('emits update:modelValue when provider changed', async () => {
    globalThis.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ default_provider: 'stability' }),
    })
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          style_preset: 'ink', auto_generate: false,
          max_assets: 10, confirm_before_generate: true,
          default_provider: 'minimax',
        },
        slug: 'test',
      },
    })
    const select = wrapper.find('[data-testid="project-settings-illustration-default-provider"]')
    await select.setValue('stability')
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    const last = wrapper.emitted('update:modelValue').at(-1)[0]
    expect(last.default_provider).toBe('stability')
  })

  it('persists via store.save when provider changed', async () => {
    globalThis.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ default_provider: 'openai' }),
    })
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          style_preset: 'ink', auto_generate: false,
          max_assets: 10, confirm_before_generate: true,
          default_provider: 'minimax',
        },
        slug: 'test-slug',
      },
    })
    const select = wrapper.find('[data-testid="project-settings-illustration-default-provider"]')
    await select.setValue('openai')
    // Wait for async save to fire
    await new Promise(r => setTimeout(r, 10))
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/projects/test-slug/settings',
      expect.objectContaining({ method: 'PUT' }),
    )
  })
})
```

- [ ] **Step 3: Update parent SettingsPage to pass `slug` prop**

Find the parent component that mounts `ProjectSettingsIllustration`. Likely `apps/dashboard/src/pages/SettingsPage.vue`. Update the template usage:

Find:
```html
<ProjectSettingsIllustration v-model="..." />
```

Replace with (where `currentProjectSlug` is the active project slug):
```html
<ProjectSettingsIllustration v-model="..." :slug="currentProjectSlug" />
```

If `currentProjectSlug` doesn't exist, determine the right way to source it from the active project state. (If SettingsPage is global with no project context, this becomes a design issue — note in handoff.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/components/illustrations/ProjectSettingsIllustration.spec.js`
Expected: existing + 4 new tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.spec.js apps/dashboard/src/pages/SettingsPage.vue
git commit -m "feat(phase-96): ProjectSettingsIllustration + default_provider dropdown"
```

---

### Task 17: Update `GenerateIllustrationDialog.vue` with provider picker

**Files:**
- Modify: `apps/dashboard/src/components/illustrations/GenerateIllustrationDialog.vue`
- Test: `apps/dashboard/src/components/illustrations/GenerateIllustrationDialog.spec.js` (existing)

- [ ] **Step 1: Add provider picker state + emit `provider` in payload**

Modify the `<script setup>` block:

```javascript
<script setup>
import { ref, computed, onMounted } from 'vue'
import { NDialog, NButton, NInput } from 'naive-ui'
import { useProjectSettingsStore } from '@/stores/useProjectSettings.js'

const props = defineProps({
  projectSlug: { type: String, required: true },
  chapterNum: { type: Number, default: null },
  type: { type: String, default: 'chapter' },
  modelValue: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'generate'])

const presets = [
  { id: 'ink', label: '古风水墨', icon: '🏯' },
  { id: 'realistic', label: '现代写实', icon: '📷' },
  { id: 'anime', label: '动漫厚涂', icon: '🎨' },
]

const providers = [
  { id: 'minimax', label: 'MiniMax' },
  { id: 'openai', label: 'OpenAI DALL-E 3' },
  { id: 'stability', label: 'Stability SD3' },
]

const store = useProjectSettingsStore()

const selectedPreset = ref('ink')
const customPrompt = ref('')
const selectedProvider = ref('minimax')  // NEW (Phase 96)

// Preselect from project default on mount
onMounted(async () => {
  if (props.projectSlug) {
    await store.fetch(props.projectSlug)
    if (store.settings?.default_provider) {
      selectedProvider.value = store.settings.default_provider
    }
  }
})

const isValid = computed(() => selectedPreset.value !== null)

function close() {
  emit('update:modelValue', false)
}

function submit() {
  if (!isValid.value) return
  emit('generate', {
    type: props.type,
    chapter_num: props.chapterNum,
    style_preset: selectedPreset.value,
    custom_prompt: customPrompt.value || null,
    provider: selectedProvider.value,  // NEW (Phase 96). Per-call override.
  })
  close()
}

// Expose for tests
defineExpose({ selectedPreset, customPrompt, selectedProvider })
</script>
```

Add provider picker UI in the template (before the "使用上下文" section):

```html
      <p class="label">图片生成器</p>
      <div class="providers">
        <button
          v-for="p in providers"
          :key="p.id"
          type="button"
          :class="['provider', 'provider-' + p.id, { selected: selectedProvider === p.id }]"
          :data-testid="`illustration-provider-${p.id}`"
          @click="selectedProvider = p.id"
        >
          {{ p.label }}
        </button>
      </div>
```

- [ ] **Step 2: Add component tests for provider picker**

Add to `GenerateIllustrationDialog.spec.js`:

```javascript
  it('preselects provider from project default', async () => {
    globalThis.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ default_provider: 'openai' }),
    })
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    // Wait for store.fetch to resolve
    await new Promise(r => setTimeout(r, 10))
    expect(wrapper.vm.selectedProvider).toBe('openai')
  })

  it('emits provider in generate payload', async () => {
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    wrapper.vm.selectedProvider = 'stability'
    wrapper.vm.submit()
    const generated = wrapper.emitted('generate')
    expect(generated).toBeTruthy()
    expect(generated[0][0].provider).toBe('stability')
  })

  it('user can override provider per call', async () => {
    globalThis.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ default_provider: 'openai' }),
    })
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    await new Promise(r => setTimeout(r, 10))
    wrapper.vm.selectedProvider = 'stability'  // override
    wrapper.vm.submit()
    const generated = wrapper.emitted('generate')
    expect(generated[0][0].provider).toBe('stability')
    // Verify NOT persisted to store
    expect(wrapper.vm.store.settings.default_provider).toBe('openai')
  })
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/components/illustrations/GenerateIllustrationDialog.spec.js`
Expected: existing + 3 new tests PASS

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/components/illustrations/GenerateIllustrationDialog.vue apps/dashboard/src/components/illustrations/GenerateIllustrationDialog.spec.js
git commit -m "feat(phase-96): GenerateIllustrationDialog + provider picker (per-call override)"
```

---

## Phase E: Regression guards

### Task 18: Create `tests/test_phase96_image_provider_adapters.py`

**Files:**
- Create: `tests/test_phase96_image_provider_adapters.py`

- [ ] **Step 1: Implement all 14 guards in one file**

Create `tests/test_phase96_image_provider_adapters.py`:

```python
"""Phase 96 regression guards (image provider abstraction).

Source-only checks (no runtime / no API calls). Pattern follows
Phase 90-95 regression guards in tests/test_phase9[0-5]_*.py.

Each guard defends a specific invariant from spec
`docs/superpowers/specs/2026-09-16-phase-96-image-provider-adapters-design.md`
that future refactors might accidentally regress.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest


# Source files to read (for guards that need source inspection).
_PROVIDERS_DIR = Path("packages/lingwen-illustrations/src/lingwen_illustrations/providers")
_PIPELINE_PY = Path("packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py")
_METADATA_PY = Path("packages/lingwen-illustrations/src/lingwen_illustrations/metadata.py")
_EXCEPTIONS_PY = Path("packages/lingwen-illustrations/src/lingwen_illustrations/exceptions.py")
_IMAGE_GENERATOR_PY = Path("packages/lingwen-illustrations/src/lingwen_illustrations/image_generator.py")
_ILLUSTRATIONS_ROUTE = Path("apps/studio_api/routes/illustrations.py")
_PROJECT_SETTINGS_ROUTE = Path("apps/studio_api/routes/project_settings.py")
_APICONFIG_PY = Path("packages/lingwen-config/src/lingwen_config/api_config_loader.py")
_PROJECT_SETTINGS_VUE = Path("apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue")
_GEN_DIALOG_VUE = Path("apps/dashboard/src/components/illustrations/GenerateIllustrationDialog.vue")


def _strip_docstrings(text: str) -> str:
    """N.14 lesson 1 v21: strip docstrings before regex search (Phase 57b pattern).

    Phase 96 docstrings may legitimately mention deleted patterns (e.g. when
    describing the v1 behavior a refactor replaces). Strip triple-quoted
    docstrings before regex matching to avoid false positives.
    """
    return re.sub(r'\"\"\"[\s\S]*?\"\"\"', "", text, flags=re.DOTALL)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------- G1: providers/ subpackage structure ----------

def test_g1_providers_subpackage_has_4_modules():
    """G1: providers/ has __init__, _b64_decode, minimax, openai, stability."""
    expected = {"__init__.py", "_b64_decode.py", "minimax.py", "openai.py", "stability.py"}
    actual = {p.name for p in _PROVIDERS_DIR.glob("*.py")}
    assert expected.issubset(actual), f"missing: {expected - actual}"


# ---------- G2: KNOWN_PROVIDERS tuple ----------

def test_g2_known_providers_tuple_is_canonical():
    """G2: providers/__init__.py defines KNOWN_PROVIDERS = ('minimax', 'openai', 'stability')."""
    text = _strip_docstrings(_read(_PROVIDERS_DIR / "__init__.py"))
    match = re.search(r"KNOWN_PROVIDERS\s*:\s*tuple\[str,\s*\.\.\.\]\s*=\s*\(([^)]+)\)", text)
    assert match, "KNOWN_PROVIDERS tuple not found"
    items = tuple(s.strip().strip('"').strip("'") for s in match.group(1).split(","))
    assert items == ("minimax", "openai", "stability")


# ---------- G3: each adapter exports async generate ----------

@pytest.mark.parametrize("module_name", ["minimax", "openai", "stability"])
def test_g3_adapter_module_exports_async_generate(module_name):
    """G3: each adapter module exports async def generate(...)."""
    module_path = _PROVIDERS_DIR / f"{module_name}.py"
    tree = ast.parse(_read(module_path))
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "generate":
            found = True
            break
    assert found, f"{module_name}.py must define `async def generate(...)`"


# ---------- G4: GenerateError accepts provider kwarg ----------

def test_g4_generate_error_accepts_provider_kwarg():
    """G4: GenerateError.__init__ has `provider: str = "unknown"` parameter."""
    tree = ast.parse(_read(_EXCEPTIONS_PY))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "GenerateError":
            init = next(
                (n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == "__init__"),
                None,
            )
            assert init is not None
            args = init.args
            kwarg_names = {a.arg for a in args.kwonlyargs}
            assert "provider" in kwarg_names
            return
    pytest.fail("GenerateError class not found")


# ---------- G5: IllustrationMetadata has provider field ----------

def test_g5_illustration_metadata_has_provider_field():
    """G5: IllustrationMetadata dataclass has `provider: str = "minimax"` field."""
    tree = ast.parse(_read(_METADATA_PY))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "IllustrationMetadata":
            for field in node.body:
                if isinstance(field, ast.AnnAssign) and isinstance(field.target, ast.Name):
                    if field.target.id == "provider":
                        # Verify default is "minimax"
                        if field.value is None:
                            pytest.fail("provider field must have default")
                        if isinstance(field.value, ast.Constant):
                            assert field.value.value == "minimax"
                        return
    pytest.fail("provider field not found in IllustrationMetadata")


# ---------- G6: from_dict backwards compat ----------

def test_g6_from_dict_backwards_compat_injects_provider():
    """G6: IllustrationMetadata.from_dict injects 'minimax' when provider missing."""
    text = _strip_docstrings(_read(_METADATA_PY))
    assert '"provider" not in d' in text or "'provider' not in d" in text
    assert 'provider": "minimax"' in text or "provider='minimax'" in text


# ---------- G7: pipeline.generate_illustration accepts provider ----------

def test_g7_pipeline_generate_illustration_signature_has_provider():
    """G7: pipeline.generate_illustration has `provider: str = 'minimax'` parameter."""
    tree = ast.parse(_read(_PIPELINE_PY))
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "generate_illustration":
            args = node.args
            kwarg_names = {a.arg for a in args.kwonlyargs}
            assert "provider" in kwarg_names
            return
    pytest.fail("generate_illustration function not found")


# ---------- G8: pipeline.regenerate_illustration reads existing_meta.provider ----------

def test_g8_regenerate_uses_existing_meta_provider_as_default():
    """G8: pipeline.regenerate_illustration uses existing_meta.provider when provider is None."""
    text = _strip_docstrings(_read(_PIPELINE_PY))
    # Find regenerate_illustration body
    assert "existing_meta.provider" in text
    assert "provider is not None" in text


# ---------- G9: GenerateRequest has provider field ----------

def test_g9_generate_request_has_provider_field():
    """G9: apps GenerateRequest Pydantic has `provider: Optional[str] = None` field."""
    tree = ast.parse(_read(_ILLUSTRATIONS_ROUTE))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "GenerateRequest":
            for field in node.body:
                if isinstance(field, ast.AnnAssign) and isinstance(field.target, ast.Name):
                    if field.target.id == "provider":
                        return
    pytest.fail("provider field not found in GenerateRequest")


# ---------- G10: route resolves provider priority ----------

def test_g10_route_resolves_provider_priority():
    """G10: route resolver implements body > project_settings > 'minimax' priority."""
    text = _strip_docstrings(_read(_ILLUSTRATIONS_ROUTE))
    assert "_resolve_provider_for_request" in text
    assert "KNOWN_PROVIDERS" in text
    # Verify priority chain: body first, then settings
    assert "body_provider" in text
    assert "settings.default_provider" in text or "default_provider" in text


# ---------- G11: project_settings.py route exists with PUT/GET ----------

def test_g11_project_settings_route_has_put_and_get():
    """G11: apps/studio_api/routes/project_settings.py exists with PUT + GET routes."""
    assert _PROJECT_SETTINGS_ROUTE.exists()
    text = _read(_PROJECT_SETTINGS_ROUTE)
    assert '"/api/projects/{slug}/settings"' in text
    # Both PUT and GET handlers
    assert "@app.put" in text
    assert "@app.get" in text


# ---------- G12: APIConfig has openai_api_host + stability_api_key + stability_api_host ----------

def test_g12_apiconfig_has_new_provider_hosts():
    """G12: APIConfig exposes openai_api_host, stability_api_key, stability_api_host."""
    tree = ast.parse(_read(_APICONFIG_PY))
    properties_seen = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and any(
            isinstance(d, ast.Name) and d.id == property
            for d in node.decorator_list
        ):
            properties_seen.add(node.name)
    expected = {"openai_api_host", "stability_api_key", "stability_api_host"}
    missing = expected - properties_seen
    assert not missing, f"missing APIConfig properties: {missing}"


# ---------- G13: ProjectSettingsIllustration has default_provider dropdown ----------

def test_g13_project_settings_illustration_has_default_provider_dropdown():
    """G13: ProjectSettingsIllustration.vue has default_provider dropdown with data-testid."""
    text = _read(_PROJECT_SETTINGS_VUE)
    assert "project-settings-illustration-default-provider" in text
    assert "<select" in text
    # Provider options
    assert "value=\"minimax\"" in text or "value='minimax'" in text or "value=\"openai\"" in text


# ---------- G14: GenerateIllustrationDialog emits provider ----------

def test_g14_generate_illustration_dialog_emits_provider():
    """G14: GenerateIllustrationDialog.vue emits `provider` in generate payload."""
    text = _read(_GEN_DIALOG_VUE)
    assert "selectedProvider" in text
    assert "provider:" in text or "provider =" in text
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/test_phase96_image_provider_adapters.py -v`
Expected: 14 tests PASS (counting parametrized G3 as 3 = 16 total test cases)

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add tests/test_phase96_image_provider_adapters.py
git commit -m "test(phase-96): 14 regression guards for image provider adapters"
```

---

## Phase F: Validation gates + docs + handoff

### Task 19: Run full backend test suite + lint

**Files:** none (validation only)

- [ ] **Step 1: Run lingwen-illustrations tests**

Run: `cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/ -v`
Expected: ALL tests PASS (78 preserved + 30 new providers + 8 metadata + 2 pipeline = 118+ tests)

- [ ] **Step 2: Run studio_api tests**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/ -v`
Expected: ALL tests PASS (90 preserved + 6 project_settings + ~10 illustrations + existing)

- [ ] **Step 3: Run full test_phase96 regression guards**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/test_phase96_image_provider_adapters.py tests/test_phase90_illustrations.py -v`
Expected: All guards PASS (Phase 96 14 + Phase 90 29 = 43+ tests)

- [ ] **Step 4: Run ruff**

Run: `cd /home/ailearn/projects/LingWen && ruff check packages/lingwen-illustrations/ packages/lingwen-config/ apps/studio_api/routes/project_settings.py apps/studio_api/routes/illustrations.py apps/studio_api/routes/_project_helpers.py apps/studio_api/background.py tests/test_phase96_image_provider_adapters.py`
Expected: Clean on introduced (any pre-existing E741 untouched)

- [ ] **Step 5: Commit any ruff auto-fixes**

If ruff --fix suggested changes: `git add -u && git commit -m "style(phase-96): ruff auto-fix"`. Otherwise skip.

---

### Task 20: Run frontend validation gates

**Files:** none (validation only)

- [ ] **Step 1: Run vitest**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run`
Expected: ALL tests PASS (existing + 5 store + 4 ProjectSettingsIllustration + 3 GenerateIllustrationDialog = 12 new)

- [ ] **Step 2: Run vue-tsc type check**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm tsc --noEmit`
Expected: 0 new errors (pre-existing unrelated errors untouched)

- [ ] **Step 3: Run knip dead code detection**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip`
Expected: 0 new dead exports (pre-existing unrelated untouched)

- [ ] **Step 4: Run ESLint**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm eslint .`
Expected: 0 new errors

- [ ] **Step 5: Commit any auto-fixes**

If tsc/eslint suggested changes: `git add -u && git commit -m "style(phase-96): frontend auto-fix"`. Otherwise skip.

---

### Task 21: Update CLAUDE.md version + invariants

**Files:**
- Modify: `CLAUDE.md:1-15`

- [ ] **Step 1: Update version line**

Edit CLAUDE.md version line at top:

Find the current version annotation starting with `> **版本**: v55.5`. Replace with `v56.0 (Phase 96 image provider adapters — REQ-002 v2 multi-provider)` and update the body summary.

Briefly describe Phase 96: "Phase 96 — image provider adapters (REQ-002 v2 first sub-project). 3 adapters: MiniMax + OpenAI DALL-E 3 + Stability SD3. Per-project default via PUT/GET /api/projects/{slug}/settings. ~77 new tests + 14 regression guards. v56.0."

- [ ] **Step 2: Add new invariant entry (I088)**

After I087 in the invariants table, add:

```markdown
| I088 | `packages/lingwen-illustrations/src/lingwen_illustrations/providers/` 是 image generation provider 抽象（registry-based dispatch: `KNOWN_PROVIDERS = ('minimax', 'openai', 'stability')` + `get_provider(name)` + `UnknownProviderError` + 3 adapter modules [minimax/openai/stability] + shared `_b64_decode.py` envelope helper）的唯一实包；`providers.<x>.generate(...)` 是 adapter 唯一入口，pipeline / image_generator / route 层不直接调具体 API；`infra.providers.*` / `infra.image_provider.*` 路径非法 (Phase 96 REQ-002 v2 multi-provider, NOT-LEAF package [0 new workspace deps, only stdlib + httpx]) |
```

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add CLAUDE.md
git commit --file=- <<'EOF'
docs(phase-96): CLAUDE.md v55.5 → v56.0 + I088 invariant

Phase 96 — image provider adapters (REQ-002 v2 multi-provider).
3 adapters (MiniMax / OpenAI DALL-E 3 / Stability SD3).
Per-project default via PUT/GET /api/projects/{slug}/settings.

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
```

---

### Task 22: Update BACKLOG.md + CURRENT_STATUS.md

**Files:**
- Modify: `collaboration/BACKLOG.md`
- Modify: `collaboration/CURRENT_STATUS.md`

- [ ] **Step 1: Add Phase 96 row to CURRENT_STATUS.md**

Add new row to the phases table:

```
| Phase 96 | image provider adapters (REQ-002 v2) | 3 adapters (MiniMax + OpenAI DALL-E 3 + Stability SD3), registry dispatch, per-project default via PUT/GET /api/projects/{slug}/settings yaml. ~77 new tests + 14 regression guards. v56.0. |
```

- [ ] **Step 2: Update BACKLOG.md**

Strike the Phase 95 deferred row (now closed by Phase 96) and add Phase 96 row.

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add collaboration/CURRENT_STATUS.md collaboration/BACKLOG.md
git commit -m "docs(phase-96): CURRENT_STATUS + BACKLOG updates"
```

---

### Task 23: Create Phase 96 handoff doc

**Files:**
- Create: `docs/superpowers/handoffs/2026-09-16-phase-96-image-provider-adapters-handoff.md`

- [ ] **Step 1: Write the handoff**

Create `docs/superpowers/handoffs/2026-09-16-phase-96-image-provider-adapters-handoff.md`:

```markdown
# Phase 96 — image provider adapters handoff

> **Date**: 2026-09-16
> **Branch**: master (direct commits per 2026-09-15 simplified workflow)
> **Version**: v55.5 → v56.0
> **Type**: REQ-002 v2 sub-project — multi-provider abstraction

## 1. Goal

Ship multi-provider image generation: 3 adapters (MiniMax / OpenAI DALL-E 3 / Stability SD3) behind a registry-based dispatch. Per-project default provider persisted at `<project_root>/.lingwen/illustration_settings.yaml` via new `PUT/GET /api/projects/{slug}/settings` endpoint. Frontend gains default-provider dropdown (ProjectSettingsIllustration) and per-call override picker (GenerateIllustrationDialog).

## 2. What Phase 96 delivered

### 2.1 Backend

- `packages/lingwen-illustrations/src/lingwen_illustrations/providers/` (NEW subpackage)
  - `__init__.py` — KNOWN_PROVIDERS + DEFAULT_PROVIDER + UnknownProviderError + get_provider()
  - `_b64_decode.py` — shared Phase 93 safe-decode triad (extracted)
  - `minimax.py` — MiniMax adapter (Phase 93 logic moved here)
  - `openai.py` — OpenAI DALL-E 3 adapter (NEW)
  - `stability.py` — Stability SD3 adapter (NEW, raw bytes via Accept: image/*)
- `image_generator.py` — converted to thin wrapper around MiniMax provider (backwards compat)
- `pipeline.py` — `generate_illustration` + `regenerate_illustration` accept `provider` arg; resolve model per-provider
- `metadata.py` — `IllustrationMetadata` adds `provider: str = "minimax"` field with backwards-compat `from_dict` injection
- `exceptions.py` — `GenerateError` adds `provider: str = "unknown"` attribute
- `packages/lingwen-config/api_config_loader.py` — new properties: `openai_api_host`, `stability_api_key`, `stability_api_host`
- `apps/studio_api/routes/_project_helpers.py` (NEW) — extracted `project_root_for()` for cross-route reuse
- `apps/studio_api/routes/project_settings.py` (NEW) — `PUT/GET /api/projects/{slug}/settings` endpoints
- `apps/studio_api/routes/illustrations.py` — GenerateRequest + provider field, regenerate `?provider=` query param, `_api_credentials_for()`, `_resolve_provider_for_request()`, `_err_detail` adds provider
- `apps/studio_api/background.py` — `_get_illustration_settings` reads default_provider from yaml

### 2.2 Frontend

- `apps/dashboard/src/stores/useProjectSettings.js` (NEW) — Pinia store: fetch/save actions
- `ProjectSettingsIllustration.vue` — added `slug: String` prop + provider dropdown + auto-save on change
- `GenerateIllustrationDialog.vue` — added provider picker (preselected from project default, per-call override, no persistence on override)
- `SettingsPage.vue` — passes `slug` prop to ProjectSettingsIllustration

### 2.3 Tests + guards

- `packages/lingwen-illustrations/tests/test_providers/` (NEW) — 4 test files: test_b64_decode (8), test_minimax (8), test_openai (9), test_stability (8), test_registry (5) = 38 new tests
- `tests/test_metadata.py` — 5 new provider/backwards-compat tests
- `tests/test_pipeline.py` — 2 new dispatch tests
- `apps/studio_api/tests/test_project_settings_api.py` (NEW) — 6 tests
- `apps/studio_api/tests/test_illustrations_api.py` — augmented with ~6 provider tests
- `apps/dashboard/src/stores/useProjectSettings.spec.js` (NEW) — 5 store tests
- `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.spec.js` — 4 new dropdown tests
- `apps/dashboard/src/components/illustrations/GenerateIllustrationDialog.spec.js` — 3 new picker tests
- `tests/test_phase96_image_provider_adapters.py` (NEW) — 14 regression guards (G1-G14)

**Totals**: ~77 new tests, 14 regression guards, 118+ total backend tests preserved + new, 27+ frontend tests.

### 2.4 Docs + invariants

- Spec: `docs/superpowers/specs/2026-09-16-phase-96-image-provider-adapters-design.md` (commit ebd30455)
- Plan: this file (the one you're reading)
- CLAUDE.md: v55.5 → v56.0 + I088 invariant (providers/ subpackage is the canonical home for provider abstraction; infra.providers.* paths illegal)
- CURRENT_STATUS.md + BACKLOG.md updates

## 3. Validation gates

| Gate | Result |
|---|---|
| `pytest packages/lingwen-illustrations/tests/` | 118+/118+ PASS |
| `pytest apps/studio_api/tests/` | 102+/102+ PASS |
| `pytest tests/test_phase96_image_provider_adapters.py` | 14/14 PASS (G1-G14) |
| `pytest tests/test_phase90_illustrations.py` (preserved) | 29/29 PASS |
| `ruff check` (introduced files) | Clean on introduced |
| `pnpm vitest run` | All PASS |
| `pnpm tsc --noEmit` | 0 new errors |
| `pnpm exec knip` | 0 new dead exports |
| `pnpm eslint .` | 0 new errors |

## 4. Architectural decisions (carried from spec)

- **Provider scope**: MiniMax + OpenAI DALL-E 3 + Stability SD3. Anthropic deleted (no native image API).
- **Adapter signature**: Minimal `(prompt, *, api_key, api_host, timeout=60) → bytes`. All 3 adapters uniform.
- **Selection model**: Per-project default (yaml) + per-call override (body or query).
- **Persistence**: yaml at `<project_root>/.lingwen/illustration_settings.yaml`, Pydantic `ProjectSettings` model.
- **Error attribution**: `GenerateError.provider` always set on provider dispatch path. HTTP error payload includes provider field.
- **Backwards compat**: `image_generator.generate()` thin wrapper → MiniMax provider. Old test mocks adapted.

## 5. Out of scope (deferred to v2 followups)

- Real-API integration tests (need keys + CI infra) — BACKLOG v2
- Reference image i2i — REQ-002 v2 separate phase
- LRU archive + notification center — REQ-002 v2 separate phases
- Multi-model per provider — v2 once user feedback
- Style preset per-provider (provider-specific templates) — v2 if consistency issue
- Atomic provider fallback chain (auto-retry on alt provider) — v2 user request
- Extend ProjectSettings with `auto_generate`, `max_assets`, `confirm_before_generate` (Phase 95 v1 stub fields) — v2 schema extension

## 6. Carryover chain (after Phase 96)

| Item | Status |
|---|---|
| Phase 90 deviations | 5/5 closed (Phase 91/92/93/94/95) ✅ |
| Phase 95 deferred (`/api/projects/{slug}/settings`) | ✅ closed by Phase 96 |
| Phase 96 → v2 followups | i2i / LRU archive / notification center / real-API tests |

## 7. Lessons

### 7.1 Adapter pattern enables DRY helper extraction (Phase 93 lesson applied)

By choosing minimal `(prompt, *, api_key, api_host) → bytes` signature upfront (vs extended with model/size), the `_b64_decode.py` shared helper became natural. MiniMax + OpenAI both return b64_json envelope → both use the helper. Stability uses raw bytes path. Three adapters, one helper, two-thirds DRY.

### 7.2 Backwards compat via thin wrapper, not migration

`image_generator.generate()` kept as thin wrapper that delegates to MiniMax provider. Existing test mocks retargeted from `image_generator.httpx.AsyncClient` → `providers.minimax.httpx.AsyncClient` via global replace. No consumer of `image_generator.generate()` needed updating. **Lesson: when refactoring an existing API, keep the entry point and update internals.**

### 7.3 APIConfig forward-looking properties paid off

Phase 83 P3-ARCHDEBT added `openai_api_key` + `anthropic_api_key` properties. Phase 96 reused the openai one and added new `openai_api_host` + `stability_api_key` + `stability_api_host`. No new config layer needed. **Lesson: forward-looking infrastructure (when genuinely forward-looking) is worth the 5-line cost.**

### 7.4 YAML persistence > SQLite for v1

`<project>/.lingwen/illustration_settings.yaml` + Pydantic model = ~30 LOC. SQLite would need a migration story, schema versioning, query layer. Phase 96 v1 uses the simplest tool that meets the requirement. **Lesson: defer SQLite until schema complexity demands it.**

### 7.5 Spec drafted for v1; deferred design intent vs reality (Phase 95 lesson applied)

Phase 90 spec mentioned 3 providers + "provider selection". Phase 95 substitution closure validated the choice. Phase 96 spec made the design concrete (registry, persistence, error attribution). **Lesson: spec drift is OK if carryover chain is tracked — Phase 95 carried forward to Phase 96 rather than re-deriving from Phase 90.**

## 8. References

- Spec: `docs/superpowers/specs/2026-09-16-phase-96-image-provider-adapters-design.md`
- Plan: `docs/superpowers/plans/2026-09-16-phase-96-image-provider-adapters.md` (this file)
- Phase 90 spec: REQ-002 multimodal v1
- Phase 93 handoff: b64_json real-API decoding (Phase 96 builds on Phase 93 helper extraction)
- Phase 95 handoff: ProjectSettingsPage substitution (Phase 96 picks up deferred persistence)
- APIConfig: `packages/lingwen-config/src/lingwen_config/api_config_loader.py`
- I087 (illustrations) + I088 (providers) invariants
```

- [ ] **Step 2: Commit handoff**

```bash
cd /home/ailearn/projects/LingWen
git add docs/superpowers/handoffs/2026-09-16-phase-96-image-provider-adapters-handoff.md
git commit -m "docs(phase-96): handoff doc"
```

---

### Task 24: Final validation pass

**Files:** none (validation only)

- [ ] **Step 1: Run all validation gates in sequence**

```bash
# Backend
cd packages/lingwen-illustrations && /home/ailearn/miniconda3/bin/python -m pytest tests/ -v
cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/ tests/test_phase96_image_provider_adapters.py tests/test_phase90_illustrations.py -v
cd /home/ailearn/projects/LingWen && ruff check packages/lingwen-illustrations/ packages/lingwen-config/ apps/studio_api/

# Frontend
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run && pnpm tsc --noEmit && pnpm exec knip && pnpm eslint .
```

Expected: ALL gates green.

- [ ] **Step 2: Verify git log**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -25
```

Expected: ~20 Phase 96 commits, each with descriptive message + Co-Authored-By footer.

- [ ] **Step 3: Push to origin**

```bash
cd /home/ailearn/projects/LingWen && git push origin master
```

Expected: Push succeeds, no conflicts.

---

## Summary

Phase 96 ships **3 image provider adapters** (MiniMax + OpenAI DALL-E 3 + Stability SD3) behind a registry-based dispatch, **per-project default persistence** via new endpoint, and **frontend pickers** for both project-level default and per-call override.

**Total scope**:
- 9 files created (providers/ subpackage with 5 files + 1 helper + 1 route + 1 store)
- 7 files modified (image_generator wrapper + pipeline + metadata + exceptions + APIConfig + illustrations route + background + 3 Vue components)
- ~77 new tests + 14 regression guards
- ~1200 LOC net (production ~600, tests ~400, docs ~200)
- 1 new invariant (I088)

**Phase 96 closes**: Phase 95 deferred persistence (`/api/projects/{slug}/settings`).

**Phase 96 opens**: REQ-002 v2 sub-project scope — i2i / LRU archive / notification center / real-API tests (v2 backlog).