# Phase 97 Reference Image i2i Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add image-to-image (i2i) generation capability to `lingwen-illustrations` package, enabling style consistency across multi-illustration projects by uploading one reference image that anchors subsequent illustrations.

**Architecture:** Extend Phase 96's provider registry from bare function to `ProviderAdapter` dataclass (4 fields: name/generate/generate_with_reference/supports_i2i). Add new `reference_image.py` storage module + 3 REST endpoints. Each provider gets `SUPPORTS_I2I` constant + `generate_with_reference()` function. Pipeline dispatches based on `reference_image_bytes is not None`. Frontend adds ReferenceImageUpload.vue + 3 component/store extensions.

**Tech Stack:** Python 3.12 / FastAPI / pytest / httpx (mock) / Pydantic; Vue 3 / TypeScript strict / Pinia / Vitest / naive-ui; ruff; vue-tsc.

**Spec:** `docs/superpowers/specs/2026-09-18-phase-97-reference-image-i2i-design.md`

**Workflow:** Atomic direct commits on master (per 2026-09-15 simplified workflow, no worktree / no ff-merge).

---

## File Structure

### New Files (8)

| Path | Responsibility |
|------|----------------|
| `packages/lingwen-illustrations/src/lingwen_illustrations/reference_image.py` | Save/load/delete/info for `<project>/.lingwen/reference_image.{jpg,png}` |
| `apps/studio_api/routes/reference_image.py` | 3 endpoints: POST/GET/DELETE `/api/projects/{slug}/reference-image` |
| `packages/lingwen-illustrations/tests/test_reference_image.py` | Storage tests (~14) |
| `packages/lingwen-illustrations/tests/test_providers_i2i.py` | Provider i2i tests (~16) |
| `packages/lingwen-illustrations/tests/test_providers_registry_adapter.py` | Adapter registry tests (~6) |
| `packages/lingwen-illustrations/tests/test_pipeline_i2i.py` | Pipeline i2i dispatch tests (~12) |
| `apps/studio_api/tests/test_routes_reference_image.py` | Reference image route tests (~8) |
| `apps/dashboard/src/components/illustrations/ReferenceImageUpload.vue` | Upload/preview/delete UI component |

### Modified Files (10)

| Path | Changes |
|------|---------|
| `packages/lingwen-illustrations/src/lingwen_illustrations/providers/__init__.py` | `get_provider()` returns `ProviderAdapter`; new SUPPORTS_I2I-aware code |
| `packages/lingwen-illustrations/src/lingwen_illustrations/providers/minimax.py` | Add `SUPPORTS_I2I=True` + `generate_with_reference()` |
| `packages/lingwen-illustrations/src/lingwen_illustrations/providers/openai.py` | Add `SUPPORTS_I2I=False` + `generate_with_reference()` raises |
| `packages/lingwen-illustrations/src/lingwen_illustrations/providers/stability.py` | Add `SUPPORTS_I2I=True` + `generate_with_reference()` |
| `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py` | Add `reference_image_bytes` param + dispatch + openai hard error |
| `packages/lingwen-illustrations/src/lingwen_illustrations/metadata.py` | Add `used_reference_image: bool = False` field + from_dict compat |
| `apps/studio_api/routes/illustrations.py` | Add `file: UploadFile | None` + `use_project_reference: bool` to GenerateRequest + multipart path |
| `apps/studio_api/app.py` | Register reference_image router |
| `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue` | Embed ReferenceImageUpload component |
| `apps/dashboard/src/components/illustrations/GenerateIllustrationDialog.vue` | Add "use project reference" toggle + per-call file input |
| `apps/dashboard/src/stores/useProjectSettings.js` | Add referenceImage state + 4 methods (fetch/upload/delete/blob) |
| `apps/dashboard/src/stores/useIllustrationStore.js` | generate() detects File → multipart, else JSON |
| `apps/dashboard/src/api/illustrations.ts` | Typed wrappers for reference-image endpoints |

### Test Counts

- Backend pytest: ~62 new tests (existing 245 + 62 = ~307)
- Frontend vitest: ~24 new tests (existing 2036 + 24 = ~2060)
- Regression guards: G1-G12 (12 new)

---

## Task 1: reference_image.py storage module — test (TDD red)

**Files:**
- Create: `packages/lingwen-illustrations/tests/test_reference_image.py`

- [ ] **Step 1: Write the failing test**

Create `packages/lingwen-illustrations/tests/test_reference_image.py` with these test functions (each one is a real test, not placeholders):

```python
"""reference_image.py storage tests (Phase 97)."""
from __future__ import annotations

from pathlib import Path

import pytest

from lingwen_illustrations.reference_image import (
    MAX_REFERENCE_BYTES,
    save_reference_image,
    load_reference_image,
    delete_reference_image,
    reference_image_info,
)

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # fake PNG signature + padding
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 100  # fake JPEG signature + padding


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    return tmp_path


def test_save_writes_jpg_file(project_root):
    save_reference_image(project_root, JPEG_BYTES, "image/jpeg")
    saved = project_root / ".lingwen" / "reference_image.jpg"
    assert saved.exists()
    assert saved.read_bytes() == JPEG_BYTES


def test_save_writes_png_file(project_root):
    save_reference_image(project_root, PNG_BYTES, "image/png")
    saved = project_root / ".lingwen" / "reference_image.png"
    assert saved.exists()
    assert saved.read_bytes() == PNG_BYTES


def test_save_creates_lingwen_dir(project_root):
    assert not (project_root / ".lingwen").exists()
    save_reference_image(project_root, JPEG_BYTES, "image/jpeg")
    assert (project_root / ".lingwen").is_dir()


def test_save_overwrites_existing(project_root):
    save_reference_image(project_root, JPEG_BYTES, "image/jpeg")
    new_bytes = b"different-content"
    save_reference_image(project_root, new_bytes, "image/jpeg")
    loaded = load_reference_image(project_root)
    assert loaded == new_bytes


def test_save_rejects_unsupported_mime(project_root):
    with pytest.raises(ValueError, match="image/jpeg or image/png"):
        save_reference_image(project_root, PNG_BYTES, "image/gif")


def test_save_rejects_oversize(project_root):
    oversize = b"\xff\xd8\xff\xe0" + b"\x00" * (MAX_REFERENCE_BYTES + 1)
    with pytest.raises(ValueError, match="exceeds"):
        save_reference_image(project_root, oversize, "image/jpeg")


def test_load_returns_none_when_missing(project_root):
    assert load_reference_image(project_root) is None


def test_load_returns_bytes_when_present(project_root):
    save_reference_image(project_root, PNG_BYTES, "image/png")
    assert load_reference_image(project_root) == PNG_BYTES


def test_delete_returns_true_when_existed(project_root):
    save_reference_image(project_root, PNG_BYTES, "image/png")
    assert delete_reference_image(project_root) is True


def test_delete_returns_false_when_missing(project_root):
    assert delete_reference_image(project_root) is False


def test_delete_removes_file(project_root):
    save_reference_image(project_root, PNG_BYTES, "image/png")
    delete_reference_image(project_root)
    assert load_reference_image(project_root) is None


def test_info_returns_none_when_missing(project_root):
    assert reference_image_info(project_root) is None


def test_info_returns_size_and_mime_when_present(project_root):
    save_reference_image(project_root, PNG_BYTES, "image/png")
    info = reference_image_info(project_root)
    assert info is not None
    assert info["size_bytes"] == len(PNG_BYTES)
    assert info["mime_type"] == "image/png"


def test_info_includes_exists_flag(project_root):
    save_reference_image(project_root, PNG_BYTES, "image/png")
    info = reference_image_info(project_root)
    assert info["exists"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/projects/LingWen/.venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_reference_image.py -v --rootdir=packages/lingwen-illustrations`

Expected: FAIL with `ModuleNotFoundError: No module named 'lingwen_illustrations.reference_image'`

- [ ] **Step 3: Commit (test-only)**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/tests/test_reference_image.py
git commit -m "test(phase-97): reference_image.py storage tests (TDD red)"
```

---

## Task 2: reference_image.py storage module — implementation (TDD green)

**Files:**
- Create: `packages/lingwen-illustrations/src/lingwen_illustrations/reference_image.py`

- [ ] **Step 1: Write minimal implementation**

Create `packages/lingwen-illustrations/src/lingwen_illustrations/reference_image.py`:

```python
"""Project-level reference image storage (Phase 97 REQ-002 v2 i2i).

Layout:
  <project_root>/.lingwen/reference_image.{jpg|png}

Why a single file (not a library):
- v1 simplicity: 1 project = 1 style reference
- avoids binary-in-yaml bloat
- independent lifecycle from .lingwen/illustration_settings.yaml
"""
from __future__ import annotations

from pathlib import Path

MAX_REFERENCE_BYTES: int = 10 * 1024 * 1024  # 10 MB

_ALLOWED_MIME_TO_EXT: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
}


def _resolve_path(project_root: Path, mime_type: str) -> Path:
    if mime_type not in _ALLOWED_MIME_TO_EXT:
        raise ValueError(
            f"unsupported mime_type '{mime_type}', expected one of {list(_ALLOWED_MIME_TO_EXT)}"
        )
    ext = _ALLOWED_MIME_TO_EXT[mime_type]
    return project_root / ".lingwen" / f"reference_image.{ext}"


def save_reference_image(
    project_root: Path,
    image_bytes: bytes,
    mime_type: str,
) -> Path:
    """Save reference image. Overwrites if exists.

    Raises:
        ValueError: If mime_type not image/jpeg or image/png, or size > MAX_REFERENCE_BYTES.
    """
    if mime_type not in _ALLOWED_MIME_TO_EXT:
        raise ValueError(
            f"unsupported mime_type '{mime_type}', expected image/jpeg or image/png"
        )
    if len(image_bytes) > MAX_REFERENCE_BYTES:
        raise ValueError(
            f"reference image size {len(image_bytes)} exceeds max {MAX_REFERENCE_BYTES}"
        )

    target = _resolve_path(project_root, mime_type)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(image_bytes)

    # If saving a different format, remove the stale file from the other format.
    for other_mime, other_ext in _ALLOWED_MIME_TO_EXT.items():
        if other_mime == mime_type:
            continue
        stale = target.parent / f"reference_image.{other_ext}"
        if stale.exists():
            stale.unlink()

    return target


def delete_reference_image(project_root: Path) -> bool:
    """Remove both jpg and png variants. Returns True if any existed."""
    existed = False
    for ext in _ALLOWED_MIME_TO_EXT.values():
        path = project_root / ".lingwen" / f"reference_image.{ext}"
        if path.exists():
            path.unlink()
            existed = True
    return existed


def load_reference_image(project_root: Path) -> bytes | None:
    """Return bytes of whichever variant exists, else None."""
    for mime_type in _ALLOWED_MIME_TO_EXT:
        path = _resolve_path(project_root, mime_type)
        if path.exists():
            return path.read_bytes()
    return None


def reference_image_info(project_root: Path) -> dict | None:
    """Return {exists, size_bytes, mime_type} or None if no file."""
    for mime_type in _ALLOWED_MIME_TO_EXT:
        path = _resolve_path(project_root, mime_type)
        if path.exists():
            return {
                "exists": True,
                "size_bytes": path.stat().st_size,
                "mime_type": mime_type,
            }
    return None


__all__ = [
    "MAX_REFERENCE_BYTES",
    "save_reference_image",
    "delete_reference_image",
    "load_reference_image",
    "reference_image_info",
]
```

- [ ] **Step 2: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/projects/LingWen/.venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_reference_image.py -v --rootdir=packages/lingwen-illustrations`

Expected: 14 PASSED

- [ ] **Step 3: Run lint**

Run: `cd /home/ailearn/projects/LingWen && ruff check packages/lingwen-illustrations/src/lingwen_illustrations/reference_image.py`

Expected: clean (0 errors)

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/src/lingwen_illustrations/reference_image.py
git commit -m "feat(phase-97): reference_image.py storage module"
```

---

## Task 3: Provider adapters — SUPPORTS_I2I constant + generate_with_reference (3 providers in 1 commit)

**Files:**
- Modify: `packages/lingwen-illustrations/src/lingwen_illustrations/providers/minimax.py`
- Modify: `packages/lingwen-illustrations/src/lingwen_illustrations/providers/openai.py`
- Modify: `packages/lingwen-illustrations/src/lingwen_illustrations/providers/stability.py`

- [ ] **Step 1: Write tests (TDD red)**

Create `packages/lingwen-illustrations/tests/test_providers_i2i.py`:

```python
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

    with patch("lingwen_illustrations.providers._b64_decode.decode_b64_envelope") as mock_decode:
        mock_decode.return_value = b"fake-jpeg-bytes"
        with patch("lingwen_illustrations.providers.minimax.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.post.return_value = fake_resp
            MockClient.return_value = mock_client

            result = await minimax.generate_with_reference(
                prompt="test prompt",
                reference_image_bytes=ref,
                api_key="test-key",
                api_host="https://api.test",
            )

    assert result == b"fake-jpeg-bytes"
    # Verify the JSON payload included image_base64
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
    assert files["strength"][1] in ("0.35", "0.5")  # accepts provider default
```

Add `pytest-asyncio` configuration to `packages/lingwen-illustrations/pyproject.toml` if missing (check first).

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/projects/LingWen/.venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_providers_i2i.py -v --rootdir=packages/lingwen-illustrations`

Expected: FAIL with `AttributeError: module ... has no attribute 'SUPPORTS_I2I'`

- [ ] **Step 3: Add SUPPORTS_I2I + generate_with_reference to minimax.py**

Modify `packages/lingwen-illustrations/src/lingwen_illustrations/providers/minimax.py` — add at top after `_PROVIDER_NAME`:

```python
SUPPORTS_I2I = True
_DEFAULT_STRENGTH = 0.5
```

Then append to end of file (before `__all__`):

```python
async def generate_with_reference(
    *,
    prompt: str,
    reference_image_bytes: bytes,
    api_key: str,
    api_host: str,
    strength: float = _DEFAULT_STRENGTH,
    timeout: float = 60.0,
) -> bytes:
    """Call MiniMax image generation API with a reference image (i2i mode).

    Returns raw JPEG bytes decoded from b64_json envelope.

    Raises:
        GenerateError: Same conditions as `generate`, plus all errors carry
            provider="minimax".
    """
    import base64

    url = f"{api_host.rstrip('/')}/v1/image_generation"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    image_b64 = base64.b64encode(reference_image_bytes).decode("ascii")
    payload = {
        "model": "minimax-multimodal",
        "prompt": prompt,
        "image_base64": image_b64,
        "strength": strength,
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
        raw = resp.headers.get("retry-after", "30")
        try:
            retry_after = int(raw)
        except ValueError:
            retry_after = 60
        raise GenerateError(
            "MiniMax rate limited", retry_after=retry_after, provider=_PROVIDER_NAME
        )

    if resp.status_code >= 400:
        retryable = resp.status_code >= 500
        raise GenerateError(
            f"MiniMax image API HTTP {resp.status_code}",
            provider=_PROVIDER_NAME,
            retryable=retryable,
        )

    return decode_b64_envelope(resp, provider=_PROVIDER_NAME)
```

Update `__all__` to `["generate", "generate_with_reference", "SUPPORTS_I2I"]`.

- [ ] **Step 4: Add SUPPORTS_I2I + generate_with_reference to openai.py**

Modify `packages/lingwen-illustrations/src/lingwen_illustrations/providers/openai.py`:

After `_PROVIDER_NAME = "openai"` add `SUPPORTS_I2I = False`.

Then append to end of file:

```python
async def generate_with_reference(
    *,
    prompt: str,
    reference_image_bytes: bytes,  # noqa: ARG001 — ignored, signature parity only
    api_key: str,                   # noqa: ARG001
    api_host: str,                  # noqa: ARG001
    strength: float = 0.0,          # noqa: ARG001
    timeout: float = 60.0,          # noqa: ARG001
) -> bytes:
    """OpenAI DALL-E 3 has no i2i capability. Always raises GenerateError.

    Pipeline should check `adapter.supports_i2i` before calling; this function
    exists for signature parity and defensive programming only.
    """
    raise GenerateError(
        "OpenAI DALL-E 3 does not support image-to-image generation",
        provider=_PROVIDER_NAME,
        retryable=False,
    )
```

Update `__all__` to `["generate", "generate_with_reference", "SUPPORTS_I2I"]`.

- [ ] **Step 5: Add SUPPORTS_I2I + generate_with_reference to stability.py**

Modify `packages/lingwen-illustrations/src/lingwen_illustrations/providers/stability.py`:

After `_DEFAULT_RETRY_AFTER = 30` add:
```python
SUPPORTS_I2I = True
_DEFAULT_STRENGTH = 0.35
```

Then append to end of file:

```python
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
```

Update `__all__` to `["generate", "generate_with_reference", "SUPPORTS_I2I"]`.

- [ ] **Step 6: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/projects/LingWen/.venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_providers_i2i.py -v --rootdir=packages/lingwen-illustrations`

Expected: 6+ PASSED (or 3 if pytest-asyncio config is missing — add it then re-run)

- [ ] **Step 7: Run ruff + commit**

```bash
cd /home/ailearn/projects/LingWen
ruff check packages/lingwen-illustrations/src/lingwen_illustrations/providers/
git add packages/lingwen-illustrations/src/lingwen_illustrations/providers/ packages/lingwen-illustrations/tests/test_providers_i2i.py
git commit -m "feat(phase-97): providers SUPPORTS_I2I + generate_with_reference (3 providers)"
```

---

## Task 4: ProviderAdapter dataclass + get_provider refactor

**Files:**
- Modify: `packages/lingwen-illustrations/src/lingwen_illustrations/providers/__init__.py`
- Create: `packages/lingwen-illustrations/tests/test_providers_registry_adapter.py`

- [ ] **Step 1: Write test (TDD red)**

Create `packages/lingwen-illustrations/tests/test_providers_registry_adapter.py`:

```python
"""ProviderAdapter registry tests (Phase 97)."""
from __future__ import annotations

from dataclasses import is_dataclass


def test_get_provider_returns_adapter_with_4_fields():
    from lingwen_illustrations.providers import get_provider

    adapter = get_provider("minimax")
    assert is_dataclass(adapter) or hasattr(adapter, "__dataclass_fields__")
    assert hasattr(adapter, "name")
    assert hasattr(adapter, "generate")
    assert hasattr(adapter, "generate_with_reference")
    assert hasattr(adapter, "supports_i2i")
    assert adapter.name == "minimax"


def test_get_provider_adapter_for_openai():
    from lingwen_illustrations.providers import get_provider

    adapter = get_provider("openai")
    assert adapter.name == "openai"
    assert adapter.supports_i2i is False


def test_get_provider_adapter_for_stability():
    from lingwen_illustrations.providers import get_provider

    adapter = get_provider("stability")
    assert adapter.name == "stability"
    assert adapter.supports_i2i is True


def test_get_provider_dynamic_lookup_monkeypatch_compat(monkeypatch):
    """Phase 96 tests monkeypatch lingwen_illustrations.providers.minimax.generate
    and expect get_provider('minimax').generate to return the patched function."""
    from lingwen_illustrations import providers

    async def patched_generate(*, prompt, api_key, api_host, timeout=60.0):
        return b"patched-bytes"

    monkeypatch.setattr(providers.minimax, "generate", patched_generate)
    adapter = providers.get_provider("minimax")
    assert adapter.generate is patched_generate


def test_get_provider_unknown_raises():
    from lingwen_illustrations.providers import UnknownProviderError, get_provider

    with __import__("pytest").raises(UnknownProviderError):
        get_provider("unknown-provider")


def test_provider_adapter_has_all_3_generate_functions():
    """Each adapter should have callable generate and generate_with_reference."""
    from lingwen_illustrations.providers import KNOWN_PROVIDERS, get_provider

    for name in KNOWN_PROVIDERS:
        adapter = get_provider(name)
        assert callable(adapter.generate), f"{name}.generate not callable"
        assert callable(adapter.generate_with_reference), f"{name}.generate_with_reference not callable"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/projects/LingWen/.venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_providers_registry_adapter.py -v --rootdir=packages/lingwen-illustrations`

Expected: FAIL (current get_provider returns a function, not an adapter object)

- [ ] **Step 3: Refactor providers/__init__.py**

Replace `packages/lingwen-illustrations/src/lingwen_illustrations/providers/__init__.py`:

```python
"""Image generation provider registry (Phase 96 + Phase 97 adapter).

Exposes KNOWN_PROVIDERS tuple + get_provider(name) lookup.
Phase 97: get_provider returns a ProviderAdapter dataclass with 4 fields:
- name: str
- generate: async callable (text-only, Phase 96)
- generate_with_reference: async callable (i2i, Phase 97)
- supports_i2i: bool capability declaration

Dynamic module attribute lookup preserves Phase 96 monkeypatch compatibility:
`monkeypatch.setattr("lingwen_illustrations.providers.minimax.generate", fake)`
still works because get_provider reads module.generate at call time.
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from lingwen_illustrations.providers import minimax, openai, stability  # noqa: F401

KNOWN_PROVIDERS: tuple[str, ...] = ("minimax", "openai", "stability")
DEFAULT_PROVIDER: str = "minimax"


class UnknownProviderError(ValueError):
    """Raised when get_provider(name) gets a name not in KNOWN_PROVIDERS."""


@dataclass(frozen=True)
class ProviderAdapter:
    """Adapter bundling text + i2i generation for one provider (Phase 97).

    `generate` and `generate_with_reference` are looked up from the provider
    module dynamically at adapter creation time, so test monkeypatching
    (which mutates the module attribute) is reflected in subsequently-
    created adapters.
    """

    name: str
    generate: Callable[..., Awaitable[bytes]]
    generate_with_reference: Callable[..., Awaitable[bytes]]
    supports_i2i: bool


def get_provider(name: str) -> ProviderAdapter:
    """Return the ProviderAdapter for the named provider.

    Args:
        name: Provider name (must be one of KNOWN_PROVIDERS).

    Returns:
        ProviderAdapter with all 4 fields populated.

    Raises:
        UnknownProviderError: If name not in KNOWN_PROVIDERS.
    """
    if name not in KNOWN_PROVIDERS:
        raise UnknownProviderError(
            f"unknown provider '{name}', expected one of {KNOWN_PROVIDERS}"
        )
    module = importlib.import_module(f"lingwen_illustrations.providers.{name}")
    return ProviderAdapter(
        name=name,
        generate=module.generate,
        generate_with_reference=module.generate_with_reference,
        supports_i2i=module.SUPPORTS_I2I,
    )


__all__ = [
    "KNOWN_PROVIDERS",
    "DEFAULT_PROVIDER",
    "UnknownProviderError",
    "ProviderAdapter",
    "get_provider",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/projects/LingWen/.venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_providers_registry_adapter.py -v --rootdir=packages/lingwen-illustrations`

Expected: 6 PASSED

- [ ] **Step 5: Run existing pipeline tests to verify Phase 96 didn't regress**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/projects/LingWen/.venv/bin/python -m pytest packages/lingwen-illustrations/tests/ -v --rootdir=packages/lingwen-illustrations`

Expected: All previous tests still pass (Phase 96's `pipeline.py` and `image_generator.py` use `module.generate` directly, not through adapter, so they're unaffected)

- [ ] **Step 6: Update image_generator.py wrapper if needed**

Check `packages/lingwen-illustrations/src/lingwen_illustrations/image_generator.py`. It currently calls `get_provider("minimax")` and returns the `generate` function. With the new adapter, this needs adjustment. Update it to:

```python
"""Legacy thin wrapper for backwards compat (Phase 96 + 97).

Phase 90-95 callers used `image_generator.generate(prompt, api_key, api_host)`.
Phase 96 redirects this to the MiniMax provider adapter via the registry.
Phase 97: get_provider returns ProviderAdapter; we extract `.generate` from it.
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
    """Backwards-compatible wrapper. Delegates to MiniMax provider's .generate."""
    adapter = get_provider("minimax")
    return await adapter.generate(
        prompt=prompt, api_key=api_key, api_host=api_host, timeout=timeout
    )


__all__ = ["generate"]
```

- [ ] **Step 7: Update pipeline.py to use adapter.generate**

In `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py`, find:
```python
provider_fn = get_provider(provider)
image_bytes = await provider_fn(...)
```

Replace with:
```python
adapter = get_provider(provider)
image_bytes = await adapter.generate(prompt=final_prompt, api_key=api_key, api_host=api_host)
```

Both occurrences (in `generate_illustration` and `regenerate_illustration`).

- [ ] **Step 8: Run all lingwen-illustrations tests**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/projects/LingWen/.venv/bin/python -m pytest packages/lingwen-illustrations/tests/ -v --rootdir=packages/lingwen-illustrations`

Expected: All pass (existing + new = ~210)

- [ ] **Step 9: Run ruff + commit**

```bash
cd /home/ailearn/projects/LingWen
ruff check packages/lingwen-illustrations/src/lingwen_illustrations/providers/ packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py packages/lingwen-illustrations/src/lingwen_illustrations/image_generator.py
git add -A
git commit -m "refactor(phase-97): get_provider returns ProviderAdapter dataclass"
```

---

## Task 5: Pipeline `reference_image_bytes` dispatch (TDD red + green)

**Files:**
- Create: `packages/lingwen-illustrations/tests/test_pipeline_i2i.py`
- Modify: `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py`
- Modify: `packages/lingwen-illustrations/src/lingwen_illustrations/metadata.py`

- [ ] **Step 1: Write tests**

Create `packages/lingwen-illustrations/tests/test_pipeline_i2i.py`:

```python
"""Pipeline i2i dispatch tests (Phase 97)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from lingwen_illustrations.exceptions import GenerateError


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Create a minimal project layout with a chapter file."""
    (tmp_path / "chapters").mkdir()
    (tmp_path / "chapters" / "001.md").write_text("# Chapter 1\n\nTest content.\n")
    (tmp_path / "config" / "illustrations").mkdir(parents=True)
    (tmp_path / "config" / "illustrations" / "characters.json").write_text("[]")
    return tmp_path


@pytest.mark.asyncio
async def test_generate_with_reference_bytes_dispatches_to_i2i(project_root):
    """When reference_image_bytes provided, pipeline calls adapter.generate_with_reference."""
    from lingwen_illustrations import pipeline

    fake_adapter = AsyncMock()
    fake_adapter.supports_i2i = True
    fake_adapter.generate_with_reference = AsyncMock(return_value=b"fake-bytes")
    fake_adapter.generate = AsyncMock(return_value=b"text-only-bytes")

    with patch("lingwen_illustrations.pipeline.get_provider", return_value=fake_adapter):
        with patch("lingwen_illustrations.pipeline.extract_scene", return_value={"scene": "x"}):
            with patch("lingwen_illustrations.pipeline.compose_prompt", return_value="prompt"):
                with patch("lingwen_illustrations.pipeline.storage.save_asset") as mock_save:
                    meta = await pipeline.generate_illustration(
                        project_root=project_root,
                        project_slug="test",
                        type="chapter",
                        chapter_num=1,
                        style_preset="ink",
                        custom_prompt=None,
                        api_key="k",
                        api_host="h",
                        provider="minimax",
                        reference_image_bytes=b"ref-bytes",
                    )

    assert fake_adapter.generate_with_reference.called
    assert not fake_adapter.generate.called
    mock_save.assert_called_once()


@pytest.mark.asyncio
async def test_generate_without_reference_dispatches_to_text(project_root):
    """When reference_image_bytes is None, pipeline calls adapter.generate."""
    from lingwen_illustrations import pipeline

    fake_adapter = AsyncMock()
    fake_adapter.supports_i2i = True
    fake_adapter.generate_with_reference = AsyncMock(return_value=b"i2i-bytes")
    fake_adapter.generate = AsyncMock(return_value=b"text-bytes")

    with patch("lingwen_illustrations.pipeline.get_provider", return_value=fake_adapter):
        with patch("lingwen_illustrations.pipeline.extract_scene", return_value={"scene": "x"}):
            with patch("lingwen_illustrations.pipeline.compose_prompt", return_value="prompt"):
                with patch("lingwen_illustrations.pipeline.storage.save_asset"):
                    await pipeline.generate_illustration(
                        project_root=project_root,
                        project_slug="test",
                        type="chapter",
                        chapter_num=1,
                        style_preset="ink",
                        custom_prompt=None,
                        api_key="k",
                        api_host="h",
                        provider="minimax",
                    )

    assert fake_adapter.generate.called
    assert not fake_adapter.generate_with_reference.called


@pytest.mark.asyncio
async def test_generate_openai_with_reference_raises(project_root):
    """openai + reference_image_bytes → GenerateError (capability mismatch)."""
    from lingwen_illustrations import pipeline

    fake_adapter = AsyncMock()
    fake_adapter.supports_i2i = False
    fake_adapter.generate = AsyncMock()
    fake_adapter.generate_with_reference = AsyncMock()

    with patch("lingwen_illustrations.pipeline.get_provider", return_value=fake_adapter):
        with patch("lingwen_illustrations.pipeline.extract_scene", return_value={"scene": "x"}):
            with patch("lingwen_illustrations.pipeline.compose_prompt", return_value="prompt"):
                with pytest.raises(GenerateError) as exc_info:
                    await pipeline.generate_illustration(
                        project_root=project_root,
                        project_slug="test",
                        type="chapter",
                        chapter_num=1,
                        style_preset="ink",
                        custom_prompt=None,
                        api_key="k",
                        api_host="h",
                        provider="openai",
                        reference_image_bytes=b"any-bytes",
                    )

    assert exc_info.value.provider == "openai"
    assert "does not support" in str(exc_info.value)


@pytest.mark.asyncio
async def test_metadata_marks_used_reference_image_true(project_root):
    """Pipeline should set used_reference_image=True when reference image provided."""
    from lingwen_illustrations import pipeline
    from lingwen_illustrations.metadata import IllustrationMetadata

    fake_adapter = AsyncMock()
    fake_adapter.supports_i2i = True
    fake_adapter.generate_with_reference = AsyncMock(return_value=b"i2i-bytes")

    with patch("lingwen_illustrations.pipeline.get_provider", return_value=fake_adapter):
        with patch("lingwen_illustrations.pipeline.extract_scene", return_value={"scene": "x"}):
            with patch("lingwen_illustrations.pipeline.compose_prompt", return_value="prompt"):
                with patch("lingwen_illustrations.pipeline.storage.save_asset"):
                    meta = await pipeline.generate_illustration(
                        project_root=project_root,
                        project_slug="test",
                        type="chapter",
                        chapter_num=1,
                        style_preset="ink",
                        custom_prompt=None,
                        api_key="k",
                        api_host="h",
                        provider="stability",
                        reference_image_bytes=b"ref-bytes",
                    )

    assert isinstance(meta, IllustrationMetadata)
    assert meta.used_reference_image is True
    assert meta.provider == "stability"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/projects/LingWen/.venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_pipeline_i2i.py -v --rootdir=packages/lingwen-illustrations`

Expected: FAIL (pipeline doesn't accept reference_image_bytes param)

- [ ] **Step 3: Add `used_reference_image` to IllustrationMetadata**

Modify `packages/lingwen-illustrations/src/lingwen_illustrations/metadata.py` — add field after `provider`:

```python
    # NEW (Phase 97). Default False for backwards compat with Phase 90-96 metadata.json
    # (no used_reference_image field). New code always passes this explicitly.
    used_reference_image: bool = False
```

Update `from_dict` to inject default:

```python
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "IllustrationMetadata":
        # Phase 96 backwards compat: inject "minimax" if old .meta.json
        # lacks provider field (Phase 90-95 era).
        if "provider" not in d:
            d = {**d, "provider": "minimax"}
        # Phase 97 backwards compat: inject False if old .meta.json
        # lacks used_reference_image field (Phase 90-96 era).
        if "used_reference_image" not in d:
            d = {**d, "used_reference_image": False}
        try:
            return cls(**d)
        except (KeyError, TypeError) as e:
            from lingwen_illustrations.exceptions import LoadError
            raise LoadError(f"invalid metadata dict: {e}") from e
```

- [ ] **Step 4: Update pipeline.py**

Modify `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py` — update `generate_illustration` signature and body. Find:

```python
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
```

Replace with:
```python
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
    reference_image_bytes: bytes | None = None,  # NEW (Phase 97)
) -> IllustrationMetadata:
```

Replace Stage 4 dispatch block:
```python
    # Stage 4: provider dispatch (Phase 96). get_provider raises
    # UnknownProviderError if name not in KNOWN_PROVIDERS.
    adapter = get_provider(provider)

    # Phase 97: dispatch to i2i vs text based on reference_image_bytes.
    if reference_image_bytes is not None:
        if not adapter.supports_i2i:
            raise GenerateError(
                f"provider '{provider}' does not support image-to-image generation",
                provider=provider,
                retryable=False,
            )
        image_bytes = await adapter.generate_with_reference(
            prompt=final_prompt,
            reference_image_bytes=reference_image_bytes,
            api_key=api_key,
            api_host=api_host,
        )
    else:
        image_bytes = await adapter.generate(
            prompt=final_prompt,
            api_key=api_key,
            api_host=api_host,
        )
```

Update Stage 5 metadata build:
```python
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
        provider=provider,
        used_reference_image=reference_image_bytes is not None,  # NEW (Phase 97)
        created_at=_iso_utc_now(),
    )
```

Also update `regenerate_illustration` to add `reference_image_bytes: bytes | None = None` param with same dispatch logic (use same control flow as `generate_illustration`).

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/projects/LingWen/.venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_pipeline_i2i.py -v --rootdir=packages/lingwen-illustrations`

Expected: 4 PASSED

- [ ] **Step 6: Run all lingwen-illustrations tests**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/projects/LingWen/.venv/bin/python -m pytest packages/lingwen-illustrations/tests/ -v --rootdir=packages/lingwen-illustrations`

Expected: All pass (existing + new)

- [ ] **Step 7: Run ruff + commit**

```bash
cd /home/ailearn/projects/LingWen
ruff check packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py packages/lingwen-illustrations/src/lingwen_illustrations/metadata.py
git add packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py packages/lingwen-illustrations/src/lingwen_illustrations/metadata.py packages/lingwen-illustrations/tests/test_pipeline_i2i.py
git commit -m "feat(phase-97): pipeline reference_image_bytes dispatch + metadata flag"
```

---

## Task 6: Routes reference_image.py — 3 endpoints (TDD red + green)

**Files:**
- Create: `apps/studio_api/routes/reference_image.py`
- Create: `apps/studio_api/tests/test_routes_reference_image.py`
- Modify: `apps/studio_api/app.py`

- [ ] **Step 1: Write test (TDD red)**

Create `apps/studio_api/tests/test_routes_reference_image.py`:

```python
"""Reference image route tests (Phase 97)."""
from __future__ import annotations

import io
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.studio_api.routes.reference_image import register_reference_image
from apps.studio_api.routes.ctx import RoutesContext


@pytest.fixture
def project_root(tmp_path: Path, monkeypatch) -> Path:
    """Create a project root and patch project_root_for to return it."""
    from apps.studio_api.routes import _project_helpers
    monkeypatch.setattr(
        _project_helpers, "project_root_for", lambda slug: tmp_path if slug == "test-slug" else None
    )
    return tmp_path


@pytest.fixture
def client(project_root: Path) -> TestClient:
    app = FastAPI()
    register_reference_image(app, RoutesContext())
    return TestClient(app)


def test_get_returns_404_when_no_reference_image(client):
    response = client.get("/api/projects/test-slug/reference-image")
    assert response.status_code == 404


def test_post_uploads_jpeg(client):
    jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    response = client.post(
        "/api/projects/test-slug/reference-image",
        files={"file": ("test.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["exists"] is True
    assert body["size_bytes"] == len(jpeg_bytes)
    assert body["mime_type"] == "image/jpeg"


def test_post_uploads_png(client):
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    response = client.post(
        "/api/projects/test-slug/reference-image",
        files={"file": ("test.png", io.BytesIO(png_bytes), "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["mime_type"] == "image/png"


def test_post_rejects_unsupported_mime(client):
    response = client.post(
        "/api/projects/test-slug/reference-image",
        files={"file": ("test.gif", io.BytesIO(b"GIF89a"), "image/gif")},
    )
    assert response.status_code == 415


def test_post_rejects_oversize(client):
    # 11 MB exceeds 10 MB limit
    big = b"\xff\xd8\xff\xe0" + b"\x00" * (11 * 1024 * 1024)
    response = client.post(
        "/api/projects/test-slug/reference-image",
        files={"file": ("big.jpg", io.BytesIO(big), "image/jpeg")},
    )
    assert response.status_code == 413


def test_post_requires_file_field(client):
    response = client.post("/api/projects/test-slug/reference-image")
    assert response.status_code in (400, 422)  # FastAPI missing-file response


def test_get_returns_info_after_upload(client):
    jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    client.post(
        "/api/projects/test-slug/reference-image",
        files={"file": ("test.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")},
    )
    response = client.get("/api/projects/test-slug/reference-image")
    assert response.status_code == 200
    assert response.json()["exists"] is True


def test_delete_returns_deleted_false_when_no_image(client):
    response = client.delete("/api/projects/test-slug/reference-image")
    assert response.status_code == 200
    assert response.json()["deleted"] is False


def test_delete_returns_deleted_true_when_image_exists(client):
    jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    client.post(
        "/api/projects/test-slug/reference-image",
        files={"file": ("test.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")},
    )
    response = client.delete("/api/projects/test-slug/reference-image")
    assert response.status_code == 200
    assert response.json()["deleted"] is True


def test_unknown_project_returns_404(monkeypatch):
    """When project_root_for raises LoadError, return 404."""
    from apps.studio_api.routes import _project_helpers
    from lingwen_illustrations.exceptions import LoadError

    def mock_root_for(slug):
        raise LoadError(f"project {slug} not found")

    monkeypatch.setattr(_project_helpers, "project_root_for", mock_root_for)

    app = FastAPI()
    register_reference_image(app, RoutesContext())
    client = TestClient(app)
    response = client.get("/api/projects/missing/reference-image")
    assert response.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/projects/LingWen/.venv/bin/python -m pytest apps/studio_api/tests/test_routes_reference_image.py -v`

Expected: FAIL (`ModuleNotFoundError: No module named 'apps.studio_api.routes.reference_image'`)

- [ ] **Step 3: Write minimal implementation**

Create `apps/studio_api/routes/reference_image.py`:

```python
"""Reference image REST endpoints (Phase 97 REQ-002 v2 i2i).

Three endpoints under /api/projects/{slug}/reference-image:
- POST   — multipart upload (file field). Save to <root>/.lingwen/reference_image.{ext}
- GET    — return {exists, size_bytes, mime_type} or 404
- DELETE — idempotent remove

Errors:
- 415 invalid mime type
- 413 file too large (> 10MB)
- 404 project not found / no reference image set
"""
from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile

from lingwen_illustrations import reference_image as ref_image
from lingwen_illustrations.exceptions import LoadError

from apps.studio_api.routes._project_helpers import project_root_for
from apps.studio_api.routes.ctx import RoutesContext


def register_reference_image(app: FastAPI, ctx: RoutesContext) -> None:
    """Mount /api/projects/{slug}/reference-image routes."""
    _ = ctx

    @app.post("/api/projects/{slug}/reference-image")
    async def upload_reference_image(slug: str, file: UploadFile = File(...)) -> dict:
        try:
            root = project_root_for(slug)
        except LoadError as e:
            raise HTTPException(404, detail={"stage": "load", "error": e.message}) from e

        if file.content_type not in ("image/jpeg", "image/png"):
            raise HTTPException(415, detail="only image/jpeg or image/png accepted")

        image_bytes = await file.read()
        try:
            ref_image.save_reference_image(root, image_bytes, file.content_type)
        except ValueError as e:
            if "exceeds" in str(e):
                raise HTTPException(413, detail=str(e)) from e
            raise HTTPException(415, detail=str(e)) from e

        info = ref_image.reference_image_info(root)
        assert info is not None
        return info

    @app.get("/api/projects/{slug}/reference-image")
    def get_reference_image(slug: str) -> dict:
        try:
            root = project_root_for(slug)
        except LoadError as e:
            raise HTTPException(404, detail={"stage": "load", "error": e.message}) from e

        info = ref_image.reference_image_info(root)
        if info is None:
            raise HTTPException(404, detail=f"no reference image for project {slug}")
        return info

    @app.delete("/api/projects/{slug}/reference-image")
    def delete_reference_image(slug: str) -> dict:
        try:
            root = project_root_for(slug)
        except LoadError as e:
            raise HTTPException(404, detail={"stage": "load", "error": e.message}) from e

        deleted = ref_image.delete_reference_image(root)
        return {"deleted": deleted}


__all__ = ["register_reference_image"]
```

- [ ] **Step 4: Register in app.py**

Modify `apps/studio_api/app.py` — find where other `register_*` calls happen and add:

```python
from apps.studio_api.routes.reference_image import register_reference_image
# ...
register_reference_image(app, ctx)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/projects/LingWen/.venv/bin/python -m pytest apps/studio_api/tests/test_routes_reference_image.py -v`

Expected: 10 PASSED

- [ ] **Step 6: Run ruff + commit**

```bash
cd /home/ailearn/projects/LingWen
ruff check apps/studio_api/routes/reference_image.py
git add apps/studio_api/routes/reference_image.py apps/studio_api/tests/test_routes_reference_image.py apps/studio_api/app.py
git commit -m "feat(phase-97): routes/reference_image.py 3 endpoints"
```

---

## Task 7: Illustrations route — multipart file + use_project_reference field

**Files:**
- Modify: `apps/studio_api/routes/illustrations.py`
- Modify: `apps/studio_api/tests/test_illustrations_api.py` (extend existing)

- [ ] **Step 1: Write tests**

Append to `apps/studio_api/tests/test_illustrations_api.py`:

```python
"""i2i route extensions (Phase 97)."""
from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from apps.studio_api.routes.illustrations import register_illustrations
from apps.studio_api.routes.ctx import RoutesContext


@pytest.fixture
def mock_pipeline():
    """Patch pipeline.generate_illustration to avoid real API calls."""
    fake_meta = type("M", (), {
        "id": "fake-id", "type": "chapter", "chapter_num": 1,
        "style_preset": "ink", "scene_json": {}, "project_slug": "test-slug",
    })()
    with patch(
        "apps.studio_api.routes.illustrations.generate_illustration",
        new=AsyncMock(return_value=fake_meta),
    ) as mock:
        yield mock


@pytest.fixture
def client_with_reference(project_root_with_ref: Path):
    """Project with a reference image already saved."""
    app = FastAPI()
    register_illustrations(app, RoutesContext())
    return TestClient(app)


def test_generate_accepts_multipart_file_with_reference(client_with_reference, mock_pipeline):
    """POST with file= field should pass bytes to pipeline.generate_reference_image_ref."""
    jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    response = client_with_reference.post(
        "/api/illustrations/generate",
        data={
            "project_slug": "test-slug",
            "type": "chapter",
            "chapter_num": 1,
            "style_preset": "ink",
            "use_project_reference": "false",
        },
        files={"file": ("ref.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")},
    )
    assert response.status_code == 200


def test_generate_uses_project_reference_when_no_file(client_with_reference, mock_pipeline):
    """When file is missing but use_project_reference=True, load from disk."""
    response = client_with_reference.post(
        "/api/illustrations/generate",
        data={
            "project_slug": "test-slug",
            "type": "chapter",
            "chapter_num": 1,
            "style_preset": "ink",
            "use_project_reference": "true",
        },
    )
    assert response.status_code == 200


def test_generate_returns_422_for_openai_with_reference(client_with_reference, mock_pipeline):
    """openai + use_project_reference=true → HTTP 422 (i2i not supported)."""
    response = client_with_reference.post(
        "/api/illustrations/generate",
        data={
            "project_slug": "test-slug",
            "type": "chapter",
            "chapter_num": 1,
            "style_preset": "ink",
            "provider": "openai",
            "use_project_reference": "true",
        },
    )
    # When project has no reference image and use_project_reference=true but no file,
    # pipeline skips i2i (no bytes). So we need to either save a reference first OR
    # post with multipart file. Let's verify the openai rejection path:
    jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    response = client_with_reference.post(
        "/api/illustrations/generate",
        data={
            "project_slug": "test-slug",
            "type": "chapter",
            "chapter_num": 1,
            "style_preset": "ink",
            "provider": "openai",
            "use_project_reference": "false",
        },
        files={"file": ("ref.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")},
    )
    assert response.status_code == 422
    assert "does not support" in response.json()["detail"]["error"]
```

You'll also need to add a `project_root_with_ref` fixture that sets up a project root and patches `project_root_for`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/projects/LingWen/.venv/bin/python -m pytest apps/studio_api/tests/test_illustrations_api.py -v -k "reference or openai_with_reference"`

Expected: FAIL (current route doesn't accept file=)

- [ ] **Step 3: Update illustrations route**

Modify `apps/studio_api/routes/illustrations.py`:

Replace `register_illustrations` `generate_illustration` endpoint:

```python
    @app.post("/api/illustrations/generate", response_model=GenerateResponse)
    async def generate_illustration(
        req: GenerateRequest = Body(...),
        file: Optional[UploadFile] = File(None),
    ) -> GenerateResponse:
        try:
            project_root = project_root_for(req.project_slug)
        except LoadError as e:
            raise HTTPException(404, detail=_err_detail(e)) from e

        provider = _resolve_provider_for_request(req.project_slug, req.provider)
        api_key, api_host = _api_credentials_for(provider)

        # Phase 97: resolve reference_image_bytes from file or project default
        reference_image_bytes: bytes | None = None
        if file is not None:
            reference_image_bytes = await file.read()
        elif req.use_project_reference:
            try:
                reference_image_bytes = reference_image_module.load_reference_image(project_root)
            except Exception:
                reference_image_bytes = None

        from lingwen_illustrations import reference_image as reference_image_module

        from lingwen_illustrations.pipeline import generate_illustration as run_pipeline

        try:
            meta = await run_pipeline(
                project_root=project_root,
                project_slug=req.project_slug,
                type=req.type,  # type: ignore[arg-type]
                chapter_num=req.chapter_num,
                style_preset=req.style_preset,
                custom_prompt=req.custom_prompt,
                api_key=api_key,
                api_host=api_host,
                provider=provider,
                reference_image_bytes=reference_image_bytes,
            )
        except IllustrationError as e:
            # Phase 97: i2i not supported → 422 instead of 502
            if isinstance(e, GenerateError) and not e.retryable and "image-to-image" in e.message:
                raise HTTPException(422, detail=_err_detail(e)) from e
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

Add new imports:
```python
from fastapi import Body, FastAPI, File, HTTPException, Query, UploadFile
from lingwen_illustrations import reference_image as reference_image_module
```

Update `GenerateRequest` to add `use_project_reference`:

```python
class GenerateRequest(BaseModel):
    project_slug: str
    type: str = Field(pattern="^(cover|chapter)$")
    chapter_num: Optional[int] = None
    style_preset: str
    custom_prompt: Optional[str] = None
    provider: Optional[str] = None  # NEW (Phase 96). None → resolve via project settings yaml.
    use_project_reference: bool = True  # NEW (Phase 97). User can disable to skip.

    @model_validator(mode="after")
    def _chapter_requires_num(self) -> "GenerateRequest":
        if self.type == "chapter" and self.chapter_num is None:
            raise ValueError("chapter_num required when type='chapter'")
        return self
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/projects/LingWen/.venv/bin/python -m pytest apps/studio_api/tests/test_illustrations_api.py -v`

Expected: All tests pass (existing + new)

- [ ] **Step 5: Run all studio_api tests**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/projects/LingWen/.venv/bin/python -m pytest apps/studio_api/tests/ -v`

Expected: All pass

- [ ] **Step 6: Run ruff + commit**

```bash
cd /home/ailearn/projects/LingWen
ruff check apps/studio_api/routes/illustrations.py
git add apps/studio_api/routes/illustrations.py apps/studio_api/tests/test_illustrations_api.py
git commit -m "feat(phase-97): illustrations route accepts multipart file + 422 i2i"
```

---

## Task 8: Frontend ReferenceImageUpload.vue component

**Files:**
- Create: `apps/dashboard/src/components/illustrations/ReferenceImageUpload.vue`
- Create: `apps/dashboard/src/components/illustrations/ReferenceImageUpload.spec.ts`

- [ ] **Step 1: Write component test**

Create `apps/dashboard/src/components/illustrations/ReferenceImageUpload.spec.ts`:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ReferenceImageUpload from './ReferenceImageUpload.vue'

// Mock the store module before importing the component
const mockStore = {
  fetchReferenceImage: vi.fn(),
  fetchReferenceImageBlob: vi.fn(),
  uploadReferenceImage: vi.fn(),
  deleteReferenceImage: vi.fn(),
  referenceImage: { value: null },
}

vi.mock('@/stores/useProjectSettings.js', () => ({
  useProjectSettingsStore: () => mockStore,
}))

describe('ReferenceImageUpload', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockStore.referenceImage.value = null
  })

  it('renders upload button when no image set', async () => {
    mockStore.fetchReferenceImage.mockResolvedValue(null)
    const wrapper = mount(ReferenceImageUpload, { props: { slug: 'test' } })
    await flushPromises()
    expect(wrapper.find('[data-testid="reference-image-upload-button"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="reference-image-preview"]').exists()).toBe(false)
  })

  it('renders preview when image exists', async () => {
    mockStore.fetchReferenceImage.mockResolvedValue({
      exists: true,
      size_bytes: 1024,
      mime_type: 'image/jpeg',
    })
    mockStore.fetchReferenceImageBlob.mockResolvedValue('blob:fake-url')
    mockStore.referenceImage.value = {
      exists: true,
      size_bytes: 1024,
      mime_type: 'image/jpeg',
    }
    const wrapper = mount(ReferenceImageUpload, { props: { slug: 'test' } })
    await flushPromises()
    expect(wrapper.find('[data-testid="reference-image-preview"]').exists()).toBe(true)
  })

  it('calls uploadReferenceImage on file change', async () => {
    mockStore.fetchReferenceImage.mockResolvedValue(null)
    mockStore.uploadReferenceImage.mockResolvedValue(undefined)
    const wrapper = mount(ReferenceImageUpload, { props: { slug: 'test' } })
    await flushPromises()

    const file = new File(['fake-bytes'], 'test.jpg', { type: 'image/jpeg' })
    const input = wrapper.find('[data-testid="reference-image-upload-input"]')
    await input.setValue({ target: { files: [file] } })

    expect(mockStore.uploadReferenceImage).toHaveBeenCalledWith('test', file)
  })

  it('calls deleteReferenceImage on remove click', async () => {
    mockStore.referenceImage.value = {
      exists: true,
      size_bytes: 1024,
      mime_type: 'image/jpeg',
    }
    mockStore.deleteReferenceImage.mockResolvedValue(undefined)
    mockStore.fetchReferenceImage.mockResolvedValue(null)
    const wrapper = mount(ReferenceImageUpload, { props: { slug: 'test' } })
    await flushPromises()

    await wrapper.find('[data-testid="reference-image-remove"]').trigger('click')
    expect(mockStore.deleteReferenceImage).toHaveBeenCalledWith('test')
  })

  it('displays error message on upload failure', async () => {
    mockStore.fetchReferenceImage.mockResolvedValue(null)
    mockStore.uploadReferenceImage.mockRejectedValue({
      data: { detail: { error: 'file too large' } },
    })
    const wrapper = mount(ReferenceImageUpload, { props: { slug: 'test' } })
    await flushPromises()

    const file = new File(['fake-bytes'], 'big.jpg', { type: 'image/jpeg' })
    await wrapper.find('[data-testid="reference-image-upload-input"]').setValue({
      target: { files: [file] },
    })
    await flushPromises()
    expect(wrapper.find('[data-testid="reference-image-error"]').exists()).toBe(true)
  })

  it('renders all 6 required data-testid markers', async () => {
    mockStore.fetchReferenceImage.mockResolvedValue(null)
    const wrapper = mount(ReferenceImageUpload, { props: { slug: 'test' } })
    await flushPromises()
    const html = wrapper.html()
    expect(html).toContain('reference-image-upload')
    expect(html).toContain('reference-image-upload-input')
    expect(html).toContain('reference-image-upload-button')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/components/illustrations/ReferenceImageUpload.spec.ts`

Expected: FAIL (component doesn't exist)

- [ ] **Step 3: Write component**

Create `apps/dashboard/src/components/illustrations/ReferenceImageUpload.vue`:

```vue
<script setup>
import { ref, onMounted } from 'vue'
import { NButton } from 'naive-ui'
import { useProjectSettingsStore } from '@/stores/useProjectSettings.js'

const props = defineProps({
  slug: { type: String, required: true },
})

const store = useProjectSettingsStore()
const fileInput = ref(null)
const previewUrl = ref(null)
const uploading = ref(false)
const removing = ref(false)
const errorMessage = ref(null)

onMounted(async () => {
  await loadInfo()
})

async function loadInfo() {
  try {
    const info = await store.fetchReferenceImage(props.slug)
    if (info?.exists) {
      previewUrl.value = await store.fetchReferenceImageBlob(props.slug)
    } else {
      previewUrl.value = null
    }
  } catch (e) {
    previewUrl.value = null
  }
}

async function onFileChange(event) {
  const file = event.target.files?.[0]
  if (!file) return
  uploading.value = true
  errorMessage.value = null
  try {
    await store.uploadReferenceImage(props.slug, file)
    await loadInfo()
  } catch (e) {
    errorMessage.value = e.data?.detail?.error || e.data?.detail || e.message || '上传失败'
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

async function onRemove() {
  removing.value = true
  errorMessage.value = null
  try {
    await store.deleteReferenceImage(props.slug)
    previewUrl.value = null
  } catch (e) {
    errorMessage.value = e.data?.detail || e.message || '删除失败'
  } finally {
    removing.value = false
  }
}

function triggerFileInput() {
  fileInput.value?.click()
}

function formatSize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}
</script>

<template>
  <div
    class="field reference-image-upload-component"
    data-testid="reference-image-upload"
  >
    <p class="label">项目参考图（可选）</p>
    <p class="hint">
      上传后所有插图生成将以此图为风格基准。
      OpenAI DALL-E 3 不支持参考图，请切换至 MiniMax 或 Stability。
    </p>

    <input
      ref="fileInput"
      type="file"
      accept="image/jpeg,image/png"
      class="hidden"
      data-testid="reference-image-upload-input"
      @change="onFileChange"
    />

    <div v-if="store.referenceImage?.exists" class="current">
      <img
        v-if="previewUrl"
        :src="previewUrl"
        alt="参考图预览"
        class="preview"
        data-testid="reference-image-preview"
      />
      <div class="meta">
        <span data-testid="reference-image-size">{{ formatSize(store.referenceImage.size_bytes) }}</span>
        <span class="mime">{{ store.referenceImage.mime_type }}</span>
      </div>
      <div class="actions">
        <NButton size="small" data-testid="reference-image-replace" @click="triggerFileInput">
          替换
        </NButton>
        <NButton
          size="small"
          type="error"
          :loading="removing"
          data-testid="reference-image-remove"
          @click="onRemove"
        >
          删除
        </NButton>
      </div>
    </div>

    <NButton
      v-else
      :loading="uploading"
      data-testid="reference-image-upload-button"
      @click="triggerFileInput"
    >
      上传参考图
    </NButton>

    <p
      v-if="errorMessage"
      class="error"
      data-testid="reference-image-error"
    >
      {{ errorMessage }}
    </p>
  </div>
</template>

<style scoped>
.reference-image-upload-component {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.hidden {
  display: none;
}
.preview {
  max-width: 200px;
  max-height: 200px;
  border-radius: 4px;
  border: 1px solid var(--border-color, #e5e7eb);
}
.meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted, #4b5563);
}
.actions {
  display: flex;
  gap: 8px;
}
.error {
  font-size: 12px;
  color: #dc2626;
}
.hint {
  font-size: 12px;
  color: var(--text-muted, #4b5563);
  margin: 0;
}
</style>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/components/illustrations/ReferenceImageUpload.spec.ts`

Expected: 6 PASSED

- [ ] **Step 5: Run TypeScript check + commit**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm tsc --noEmit
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/components/illustrations/ReferenceImageUpload.vue apps/dashboard/src/components/illustrations/ReferenceImageUpload.spec.ts
git commit -m "feat(phase-97): ReferenceImageUpload.vue component"
```

---

## Task 9: Frontend useProjectSettings.js store — 4 reference image methods

**Files:**
- Modify: `apps/dashboard/src/stores/useProjectSettings.js`
- Modify: `apps/dashboard/src/stores/useProjectSettings.spec.js` (extend if exists, else create)

- [ ] **Step 1: Write tests**

Create or extend `apps/dashboard/src/stores/useProjectSettings.spec.js`:

```javascript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useProjectSettingsStore } from './useProjectSettings.js'

describe('useProjectSettings — reference image methods', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    globalThis.$fetch = vi.fn()
  })

  it('fetchReferenceImage populates state and returns info', async () => {
    const store = useProjectSettingsStore()
    globalThis.$fetch.mockResolvedValue({
      exists: true,
      size_bytes: 1024,
      mime_type: 'image/jpeg',
    })

    const result = await store.fetchReferenceImage('test-slug')
    expect(result.exists).toBe(true)
    expect(store.referenceImage.exists).toBe(true)
  })

  it('fetchReferenceImage returns null on 404', async () => {
    const store = useProjectSettingsStore()
    globalThis.$fetch.mockRejectedValue({ status: 404 })

    const result = await store.fetchReferenceImage('test-slug')
    expect(result).toBe(null)
    expect(store.referenceImage).toBe(null)
  })

  it('uploadReferenceImage posts FormData', async () => {
    const store = useProjectSettingsStore()
    globalThis.$fetch.mockResolvedValue({})

    const file = new File(['x'], 'test.jpg', { type: 'image/jpeg' })
    await store.uploadReferenceImage('test-slug', file)

    expect(globalThis.$fetch).toHaveBeenCalledWith(
      '/api/projects/test-slug/reference-image',
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('deleteReferenceImage clears state', async () => {
    const store = useProjectSettingsStore()
    store.referenceImage = { exists: true, size_bytes: 1, mime_type: 'image/jpeg' }
    globalThis.$fetch.mockResolvedValue({ deleted: true })

    await store.deleteReferenceImage('test-slug')
    expect(store.referenceImage).toBe(null)
  })

  it('fetchReferenceImageBlob returns blob', async () => {
    const store = useProjectSettingsStore()
    const fakeBlob = new Blob(['fake-bytes'], { type: 'image/jpeg' })
    globalThis.$fetch.mockResolvedValue(fakeBlob)

    const result = await store.fetchReferenceImageBlob('test-slug')
    expect(result).toBe(fakeBlob)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/stores/useProjectSettings.spec.js`

Expected: FAIL (methods don't exist)

- [ ] **Step 3: Add reference image methods to store**

Modify `apps/dashboard/src/stores/useProjectSettings.js`. Add to existing state:

```javascript
const referenceImage = ref(null)
```

Add to existing actions / returned methods:

```javascript
async function fetchReferenceImage(slug) {
  try {
    const res = await $fetch(`/api/projects/${slug}/reference-image`)
    referenceImage.value = res
    return res
  } catch (e) {
    if (e.status === 404 || e.response?.status === 404) {
      referenceImage.value = null
      return null
    }
    throw e
  }
}

async function fetchReferenceImageBlob(slug) {
  const res = await $fetch(`/api/projects/${slug}/reference-image/blob`, {
    responseType: 'blob',
  }).catch(async () => {
    // Fallback: route returns raw bytes via the same GET endpoint with Accept header
    return await $fetch(`/api/projects/${slug}/reference-image`, {
      responseType: 'blob',
    })
  })
  return URL.createObjectURL(res)
}

async function uploadReferenceImage(slug, file) {
  const formData = new FormData()
  formData.append('file', file)
  await $fetch(`/api/projects/${slug}/reference-image`, {
    method: 'POST',
    body: formData,
  })
  await fetchReferenceImage(slug)
}

async function deleteReferenceImage(slug) {
  await $fetch(`/api/projects/${slug}/reference-image`, { method: 'DELETE' })
  referenceImage.value = null
}
```

Update the returned object:

```javascript
return {
  ...existing returns,
  referenceImage,
  fetchReferenceImage,
  fetchReferenceImageBlob,
  uploadReferenceImage,
  deleteReferenceImage,
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/stores/useProjectSettings.spec.js`

Expected: 5 PASSED

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/stores/useProjectSettings.js apps/dashboard/src/stores/useProjectSettings.spec.js
git commit -m "feat(phase-97): useProjectSettings store — 4 reference image methods"
```

---

## Task 10: Frontend ProjectSettingsIllustration.vue — embed ReferenceImageUpload

**Files:**
- Modify: `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue`
- Modify: `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.spec.ts` (extend)

- [ ] **Step 1: Write test**

Append to `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.spec.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ProjectSettingsIllustration from './ProjectSettingsIllustration.vue'

vi.mock('@/stores/useProjectSettings.js', () => ({
  useProjectSettingsStore: () => ({
    settings: { default_provider: 'minimax' },
    save: vi.fn(),
  }),
}))

describe('ProjectSettingsIllustration — reference image integration', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('embeds ReferenceImageUpload component', async () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          style_preset: 'ink',
          auto_generate: false,
          max_assets: 10,
          confirm_before_generate: false,
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    expect(wrapper.find('[data-testid="reference-image-upload"]').exists()).toBe(true)
  })

  it('reference image upload is rendered before max_assets field', () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          style_preset: 'ink',
          auto_generate: false,
          max_assets: 10,
          confirm_before_generate: false,
        },
        slug: 'test-slug',
      },
    })
    const html = wrapper.html()
    const refIdx = html.indexOf('reference-image-upload')
    const maxIdx = html.indexOf('project-settings-illustration-max-assets')
    expect(refIdx).toBeGreaterThan(-1)
    expect(maxIdx).toBeGreaterThan(refIdx)
  })

  it('default_provider still works (no regression)', async () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          style_preset: 'ink',
          auto_generate: false,
          max_assets: 10,
          confirm_before_generate: false,
          default_provider: 'minimax',
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    expect(wrapper.find('[data-testid="project-settings-illustration-default-provider"]').exists()).toBe(true)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/components/illustrations/ProjectSettingsIllustration.spec.ts`

Expected: FAIL (ReferenceImageUpload not embedded)

- [ ] **Step 3: Update component**

Modify `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue`:

Add to script imports:
```javascript
import ReferenceImageUpload from './ReferenceImageUpload.vue'
```

In template, after the `auto_generate` field block and BEFORE the `default_provider` field, insert:

```vue
    <ReferenceImageUpload :slug="props.slug" />
```

(Reference image upload is independent of the v-model; it talks to its own endpoint.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/components/illustrations/ProjectSettingsIllustration.spec.ts`

Expected: 3+ PASSED

- [ ] **Step 5: Run TypeScript + commit**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm tsc --noEmit
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.spec.ts
git commit -m "feat(phase-97): ProjectSettingsIllustration embeds ReferenceImageUpload"
```

---

## Task 11: Frontend useIllustrationStore.js — multipart dispatch

**Files:**
- Modify: `apps/dashboard/src/stores/useIllustrationStore.js`
- Modify: `apps/dashboard/src/stores/useIllustrationStore.spec.js` (extend)

- [ ] **Step 1: Write tests**

Append to `apps/dashboard/src/stores/useIllustrationStore.spec.js`:

```javascript
describe('useIllustrationStore.generate — multipart dispatch', () => {
  it('uses FormData when per_call_reference is File', async () => {
    const store = useIllustrationStore()
    globalThis.$fetch = vi.fn().mockResolvedValue({ id: 'fake', type: 'chapter' })

    const file = new File(['x'], 'ref.jpg', { type: 'image/jpeg' })
    await store.generate('test-slug', {
      type: 'chapter',
      chapter_num: 1,
      style_preset: 'ink',
      custom_prompt: null,
      provider: 'minimax',
      use_project_reference: false,
      per_call_reference: file,
    })

    const callArgs = globalThis.$fetch.mock.calls[0]
    expect(callArgs[0]).toBe('/api/illustrations/generate')
    expect(callArgs[1].method).toBe('POST')
    const body = callArgs[1].body
    expect(body).toBeInstanceOf(FormData)
    expect(body.get('file')).toBe(file)
    expect(body.get('use_project_reference')).toBe('false')
  })

  it('uses JSON when no per_call_reference', async () => {
    const store = useIllustrationStore()
    globalThis.$fetch = vi.fn().mockResolvedValue({ id: 'fake', type: 'chapter' })

    await store.generate('test-slug', {
      type: 'chapter',
      chapter_num: 1,
      style_preset: 'ink',
      custom_prompt: null,
      provider: 'minimax',
      use_project_reference: true,
    })

    const callArgs = globalThis.$fetch.mock.calls[0]
    expect(typeof callArgs[1].body).toBe('object')
    expect(callArgs[1].body.use_project_reference).toBe(true)
  })

  it('strips per_call_reference from JSON path', async () => {
    const store = useIllustrationStore()
    globalThis.$fetch = vi.fn().mockResolvedValue({ id: 'fake', type: 'chapter' })

    await store.generate('test-slug', {
      type: 'chapter',
      chapter_num: 1,
      style_preset: 'ink',
      custom_prompt: null,
      provider: 'minimax',
      use_project_reference: true,
      per_call_reference: undefined,
    })

    const body = globalThis.$fetch.mock.calls[0][1].body
    expect(body.per_call_reference).toBeUndefined()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/stores/useIllustrationStore.spec.js`

Expected: FAIL (current generate doesn't dispatch to multipart)

- [ ] **Step 3: Update store generate()**

Modify `apps/dashboard/src/stores/useIllustrationStore.js`. Replace `generate` method:

```javascript
  async function generate(slug, params) {
    loading.value = true
    error.value = null
    try {
      const useMultipart = params.per_call_reference instanceof File
      let body, headers
      if (useMultipart) {
        const formData = new FormData()
        formData.append('project_slug', slug)
        formData.append('type', params.type)
        if (params.chapter_num != null) formData.append('chapter_num', String(params.chapter_num))
        formData.append('style_preset', params.style_preset)
        if (params.custom_prompt) formData.append('custom_prompt', params.custom_prompt)
        if (params.provider) formData.append('provider', params.provider)
        formData.append('use_project_reference', String(params.use_project_reference ?? true))
        formData.append('file', params.per_call_reference)
        body = formData
        headers = undefined
      } else {
        const { per_call_reference: _ignored, ...rest } = params
        body = {
          project_slug: slug,
          ...rest,
          use_project_reference: params.use_project_reference ?? true,
        }
      }

      const res = await $fetch('/api/illustrations/generate', {
        method: 'POST',
        body,
        headers,
      })
      assets.value = [res, ...assets.value]
      return res
    } catch (e) {
      error.value = e.data?.detail?.error || e.message || 'generate failed'
      throw e
    } finally {
      loading.value = false
    }
  }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/stores/useIllustrationStore.spec.js`

Expected: 3+ PASSED

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/stores/useIllustrationStore.js apps/dashboard/src/stores/useIllustrationStore.spec.js
git commit -m "feat(phase-97): useIllustrationStore.generate — multipart vs JSON dispatch"
```

---

## Task 12: Frontend GenerateIllustrationDialog.vue — toggle + per-call file

**Files:**
- Modify: `apps/dashboard/src/components/illustrations/GenerateIllustrationDialog.vue`
- Modify: `apps/dashboard/src/components/illustrations/GenerateIllustrationDialog.spec.ts` (extend)

- [ ] **Step 1: Write tests**

Append to `apps/dashboard/src/components/illustrations/GenerateIllustrationDialog.spec.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import GenerateIllustrationDialog from './GenerateIllustrationDialog.vue'

vi.mock('@/stores/useProjectSettings.js', () => ({
  useProjectSettingsStore: () => ({
    settings: { default_provider: 'minimax' },
    fetch: vi.fn().mockResolvedValue({ default_provider: 'minimax' }),
  }),
}))

describe('GenerateIllustrationDialog — reference image toggle', () => {
  beforeEach(() => {
    // Mock $fetch for globalThis
    globalThis.$fetch = vi.fn().mockResolvedValue({ default_provider: 'minimax' })
  })

  it('renders use-project-reference checkbox', () => {
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    expect(wrapper.find('[data-testid="dialog-use-project-reference"]').exists()).toBe(true)
  })

  it('renders per-call file input', () => {
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    expect(wrapper.find('[data-testid="dialog-per-call-reference"]').exists()).toBe(true)
  })

  it('emits generate event with use_project_reference=true by default', async () => {
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    await flushPromises()
    await wrapper.find('[data-testid="generate-submit"]').trigger('click')
    const events = wrapper.emitted('generate')
    expect(events).toBeTruthy()
    expect(events[0][0].use_project_reference).toBe(true)
  })

  it('emits generate with per_call_reference when file selected', async () => {
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    const file = new File(['x'], 'ref.jpg', { type: 'image/jpeg' })
    await wrapper.find('[data-testid="dialog-per-call-reference"]').setValue({
      target: { files: [file] },
    })
    await wrapper.find('[data-testid="generate-submit"]').trigger('click')
    const payload = wrapper.emitted('generate')[0][0]
    expect(payload.per_call_reference).toBe(file)
  })

  it('emits openai rejection warning when openai + reference', async () => {
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    await flushPromises()
    // Switch to openai
    await wrapper.find('[data-testid="illustration-provider-openai"]').trigger('click')
    await flushPromises()
    // Warning text should appear
    expect(wrapper.html()).toContain('OpenAI')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/components/illustrations/GenerateIllustrationDialog.spec.ts`

Expected: FAIL (toggle + file input don't exist)

- [ ] **Step 3: Update dialog component**

Modify `apps/dashboard/src/components/illustrations/GenerateIllustrationDialog.vue`:

Add to script:
```javascript
import { ref, computed, onMounted, watch } from 'vue'
// ...existing imports...

const useProjectReference = ref(true)
const perCallFile = ref(null)

const supportsI2iForProvider = (provider) => provider === 'minimax' || provider === 'stability'

watch(selectedProvider, (newVal) => {
  if (newVal === 'openai' && useProjectReference.value) {
    useProjectReference.value = false
  }
})

function onPerCallFileChange(event) {
  perCallFile.value = event.target.files?.[0] || null
  if (perCallFile.value) {
    useProjectReference.value = false
  }
}
```

Update `submit()`:
```javascript
function submit() {
  if (!isValid.value) return
  emit('generate', {
    type: props.type,
    chapter_num: props.chapterNum,
    style_preset: selectedPreset.value,
    custom_prompt: customPrompt.value || null,
    provider: selectedProvider.value,
    use_project_reference: useProjectReference.value,
    per_call_reference: perCallFile.value,
  })
  close()
}
```

In template, after the `providers` block, add:
```vue
      <p class="label">参考图（可选）</p>
      <div class="reference-options">
        <label class="reference-option-label">
          <input
            type="checkbox"
            :disabled="selectedProvider === 'openai'"
            :checked="useProjectReference"
            data-testid="dialog-use-project-reference"
            @change="useProjectReference = $event.target.checked"
          />
          使用项目默认参考图
        </label>
        <input
          type="file"
          accept="image/jpeg,image/png"
          data-testid="dialog-per-call-reference"
          @change="onPerCallFileChange"
        />
        <p
          v-if="selectedProvider === 'openai' && (useProjectReference || perCallFile)"
          class="warning"
          data-testid="dialog-openai-warning"
        >
          OpenAI DALL-E 3 不支持参考图，已自动取消
        </p>
      </div>
```

Add scoped CSS:
```css
.reference-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.reference-option-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
.warning {
  font-size: 12px;
  color: #dc2626;
  margin: 0;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/components/illustrations/GenerateIllustrationDialog.spec.ts`

Expected: 5+ PASSED

- [ ] **Step 5: Run TypeScript + commit**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm tsc --noEmit
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/components/illustrations/GenerateIllustrationDialog.vue apps/dashboard/src/components/illustrations/GenerateIllustrationDialog.spec.ts
git commit -m "feat(phase-97): GenerateIllustrationDialog reference image toggle + per-call"
```

---

## Task 13: Frontend typed wrappers (api/illustrations.ts)

**Files:**
- Modify: `apps/dashboard/src/api/illustrations.ts`
- Modify: `apps/dashboard/src/api/illustrations.spec.ts` (extend if exists)

- [ ] **Step 1: Add typed wrappers**

Append to `apps/dashboard/src/api/illustrations.ts`:

```typescript
// Phase 97: reference image wrappers
export interface ReferenceImageInfo {
  exists: true
  size_bytes: number
  mime_type: 'image/jpeg' | 'image/png'
}
export interface ReferenceImageNotFound {
  exists: false
}

export function fetchReferenceImageInfo(
  slug: string
): Promise<ReferenceImageInfo | ReferenceImageNotFound> {
  return $fetch(`/api/projects/${slug}/reference-image`)
}

export function fetchReferenceImageBlob(slug: string): Promise<Blob> {
  return $fetch(`/api/projects/${slug}/reference-image`, { responseType: 'blob' })
}

export function uploadReferenceImage(slug: string, file: File): Promise<void> {
  const formData = new FormData()
  formData.append('file', file)
  return $fetch(`/api/projects/${slug}/reference-image`, {
    method: 'POST',
    body: formData,
  })
}

export function deleteReferenceImage(slug: string): Promise<void> {
  return $fetch(`/api/projects/${slug}/reference-image`, { method: 'DELETE' })
}

// Extend GenerateRequest
declare module './illustrations' {
  interface GenerateRequest {
    use_project_reference?: boolean
    per_call_reference?: File
  }
}
```

- [ ] **Step 2: Run TypeScript check**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm tsc --noEmit`

Expected: 0 new errors

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/api/illustrations.ts
git commit -m "feat(phase-97): api/illustrations.ts typed wrappers for reference image"
```

---

## Task 14: Regression guards G1-G12

**Files:**
- Create: `packages/lingwen-illustrations/tests/test_phase97_reference_image_i2i.py`

- [ ] **Step 1: Write guards**

Create `packages/lingwen-illustrations/tests/test_phase97_reference_image_i2i.py`:

```python
"""Phase 97 reference image i2i regression guards (G1-G12).

Source-only checks. Verifies that all Phase 97 architectural invariants
remain in place even after future edits.
"""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _strip_docstrings(src: str) -> str:
    import re
    return re.sub(r'""".*?""""', "", src, flags=re.DOTALL)


# G1: get_provider returns ProviderAdapter with 4 fields
def test_g1_get_provider_returns_adapter_with_4_fields():
    src = _read(
        "packages/lingwen-illustrations/src/lingwen_illustrations/providers/__init__.py"
    )
    assert "ProviderAdapter" in src
    assert "name:" in src
    assert "generate:" in src
    assert "generate_with_reference:" in src
    assert "supports_i2i:" in src
    assert "importlib.import_module" in src  # dynamic lookup for monkeypatch


# G2: provider SUPPORTS_I2I constants
@pytest.mark.parametrize("provider,expected", [
    ("minimax", "True"),
    ("openai", "False"),
    ("stability", "True"),
])
def test_g2_provider_supports_i2i_constants(provider, expected):
    src = _read(f"packages/lingwen-illustrations/src/lingwen_illustrations/providers/{provider}.py")
    assert f"SUPPORTS_I2I = {expected}" in _strip_docstrings(src)


# G3: providers have generate_with_reference function
@pytest.mark.parametrize("provider", ["minimax", "openai", "stability"])
def test_g3_providers_have_generate_with_reference(provider):
    src = _read(f"packages/lingwen-illustrations/src/lingwen_illustrations/providers/{provider}.py")
    assert "async def generate_with_reference" in _strip_docstrings(src)


# G4: openai.generate_with_reference raises with retryable=False
def test_g4_openai_generate_with_reference_raises():
    src = _read("packages/lingwen-illustrations/src/lingwen_illustrations/providers/openai.py")
    cleaned = _strip_docstrings(src)
    # The function must raise GenerateError with retryable=False
    assert "GenerateError" in cleaned
    assert "retryable=False" in cleaned
    assert "does not support" in cleaned


# G5: reference_image module exists with 4 functions
def test_g5_reference_image_module_exists_with_4_functions():
    src = _read(
        "packages/lingwen-illustrations/src/lingwen_illustrations/reference_image.py"
    )
    for fn in ("save_reference_image", "load_reference_image", "delete_reference_image", "reference_image_info"):
        assert f"def {fn}" in src, f"missing {fn}"


# G6: pipeline has reference_image_bytes param + adapter call
def test_g6_pipeline_dispatches_to_generate_with_reference_when_bytes_provided():
    src = _read("packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py")
    cleaned = _strip_docstrings(src)
    assert "reference_image_bytes" in cleaned
    assert "generate_with_reference" in cleaned
    assert "adapter.supports_i2i" in cleaned


# G7: pipeline raises GenerateError for openai + reference
def test_g7_pipeline_raises_generate_error_for_openai_with_reference():
    src = _read("packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py")
    cleaned = _strip_docstrings(src)
    assert 'f"provider' in cleaned
    assert "image-to-image" in cleaned
    assert "retryable=False" in cleaned


# G8: IllustrationMetadata has used_reference_image field
def test_g8_illustration_metadata_has_used_reference_image_field():
    src = _read("packages/lingwen-illustrations/src/lingwen_illustrations/metadata.py")
    assert "used_reference_image: bool = False" in _strip_docstrings(src)


# G9: routes/reference_image.py 3 endpoints registered
def test_g9_routes_reference_image_three_endpoints_registered():
    src = _read("apps/studio_api/routes/reference_image.py")
    assert '"/api/projects/{slug}/reference-image"' in src
    methods = ['POST', 'GET', 'DELETE']
    for method in methods:
        assert f"@app.{method.lower()}" in src or f'async def {method.lower()}' in src or method in src


# G10: illustrations route accepts multipart file field
def test_g10_generate_request_supports_multipart_file_field():
    src = _read("apps/studio_api/routes/illustrations.py")
    assert "UploadFile" in src
    assert "file: Optional[UploadFile]" in src or "file: UploadFile | None" in src
    assert "use_project_reference" in src


# G11: frontend ReferenceImageUpload component exists with testids
def test_g11_frontend_reference_image_upload_component_exists():
    src = _read("apps/dashboard/src/components/illustrations/ReferenceImageUpload.vue")
    for testid in [
        "reference-image-upload",
        "reference-image-upload-input",
        "reference-image-preview",
        "reference-image-replace",
        "reference-image-remove",
        "reference-image-error",
    ]:
        assert testid in src, f"missing data-testid={testid}"


# G12: useProjectSettings store has reference image methods
def test_g12_frontend_project_settings_store_has_reference_image_methods():
    src = _read("apps/dashboard/src/stores/useProjectSettings.js")
    for method in ("fetchReferenceImage", "fetchReferenceImageBlob", "uploadReferenceImage", "deleteReferenceImage"):
        assert method in src, f"missing {method}"
```

- [ ] **Step 2: Run guards**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/projects/LingWen/.venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_phase97_reference_image_i2i.py -v --rootdir=packages/lingwen-illustrations`

Expected: 17-22 PASSED (G1 + G2 (×3) + G3 (×3) + G4-G12 = ~17)

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/tests/test_phase97_reference_image_i2i.py
git commit -m "test(phase-97): 12 regression guards G1-G12"
```

---

## Task 15: Documentation — CLAUDE.md v56.1 + I089 invariant + BACKLOG/CURRENT_STATUS updates

**Files:**
- Modify: `CLAUDE.md`
- Modify: `collaboration/BACKLOG.md`
- Modify: `collaboration/CURRENT_STATUS.md`
- Modify: `.lingwen/architecture.yml`
- Create: `docs/superpowers/handoffs/2026-09-18-phase-97-reference-image-i2i-handoff.md`

- [ ] **Step 1: Update CLAUDE.md**

Find the current version block (v56.0) and prepend v56.1:

```markdown
> **版本**: v56.1 (Phase 97 REQ-002 v2: Reference image i2i — second REQ-002 v2 sub-project delivered; ProviderAdapter dataclass + SUPPORTS_I2I capability declaration + generate_with_reference per provider (minimax/stability support, openai raises) + reference_image.py storage + POST/GET/DELETE `/api/projects/{slug}/reference-image` + GenerateRequest multipart file + use_project_reference bool + ReferenceImageUpload.vue + ProjectSettingsIllustration embeds it + GenerateIllustrationDialog toggle + per-call multipart upload + 4 useProjectSettings store methods + useIllustrationStore multipart dispatch + api/illustrations.ts typed wrappers + 12 regression guards G1-G12 + I089 NEW invariant + 14 atomic commits + ~85 new tests. v56.0 → v56.1)
```

Add I089 to invariants:

```markdown
| I089 | `packages/lingwen-illustrations/src/lingwen_illustrations/providers/` 是 image generation provider 抽象（registry-based dispatch: `KNOWN_PROVIDERS = ('minimax', 'openai', 'stability')` + `get_provider(name) → ProviderAdapter` dataclass (4 fields: name/generate/generate_with_reference/supports_i2i) + `SUPPORTS_I2I` capability constant per provider + 3 adapter modules + i2i dispatch via `generate_with_reference`; `adapter.generate(...)` 与 `adapter.generate_with_reference(...)` 是 adapter 唯一入口，pipeline / image_generator / route 层不直接调具体 API；`infra.providers.*` / `infra.image_provider.*` 路径非法 (Phase 97 REQ-002 v2 i2i extension, extends I088 for i2i capability) |
```

- [ ] **Step 2: Update .lingwen/architecture.yml**

Add I089 invariant to architecture.yml (mirror the CLAUDE.md entry).

- [ ] **Step 3: Update BACKLOG.md**

Mark Phase 97 done + remaining v2 sub-projects:

```markdown
| 2026-09-18 | 协调者 | **v56.1 Phase 97 REQ-002 v2: Reference image i2i (second REQ-002 v2 sub-project delivered)**: master direct commits (per 2026-09-15 simplified workflow): 14 atomic commits = spec + plan + reference_image.py storage (save/load/delete/info + MAX_REFERENCE_BYTES=10MB + JPG/PNG only) + 3 providers (minimax i2i endpoint + openai hard error + stability multipart) + ProviderAdapter dataclass (replaces function-based registry) + SUPPORTS_I2I constants + generate_with_reference per provider + pipeline.reference_image_bytes dispatch + IllustrationMetadata.used_reference_image field + routes/reference_image.py 3 endpoints + illustrations route use_project_reference field + multipart file + 422 i2i unsupported + ReferenceImageUpload.vue + useProjectSettings 4 methods + ProjectSettingsIllustration embeds + useIllustrationStore multipart dispatch + GenerateIllustrationDialog toggle + per-call file + api/illustrations.ts typed wrappers + 12 regression guards G1-G12 + CLAUDE.md v56.0 → v56.1 + I089 NEW invariant. **Validation**: pytest lingwen-illustrations ~194/194 (was 132, +62) + studio_api ~121/121 (was 113, +8) + phase90+96+97 guards 26+29=55 preserved; vitest apps/dashboard ~2060/2060 (was 2036, +24); pnpm tsc 0 new errors; ruff clean on introduced. **3 lessons**: (1) ProviderAdapter dataclass via dynamic `importlib.import_module` preserves Phase 96 monkeypatch compat — `monkeypatch.setattr("lingwen_illustrations.providers.minimax.generate", fake)` still works because adapter reads `module.generate` at call time; (2) `use_project_reference` bool is necessary UX intent flag — distinguishes 'user wants default' from 'user explicitly doesn't want'; (3) Single-file `.lingwen/reference_image.{ext}` storage avoids yaml bloat + keeps reference lifecycle independent of settings schema. **REQ-002 v2 second sub-project delivered**. Remaining: LRU archive + notification center + multi-model + atomic provider fallback + ProjectSettings extension (auto_generate/max_assets/confirm_before_generate). 详见 `docs/superpowers/handoffs/2026-09-18-phase-97-reference-image-i2i-handoff.md` + spec `2026-09-18-phase-97-reference-image-i2i-design.md` + plan `2026-09-18-phase-97-reference-image-i2i.md` |
```

- [ ] **Step 4: Update CURRENT_STATUS.md**

Add Phase 97 row to the "已完成（近期）" section.

- [ ] **Step 5: Write handoff doc**

Create `docs/superpowers/handoffs/2026-09-18-phase-97-reference-image-i2i-handoff.md` with sections:

- Summary: what was built
- Commits: list of all 14 atomic commits with hashes
- Validation: pytest + vitest + ruff + tsc results
- Lessons: 3 key lessons
- Carryover closure: N/A (no carryovers)
- Next: REQ-002 v2 remaining (LRU archive + notification center)

- [ ] **Step 6: Run all validation gates**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/projects/LingWen/.venv/bin/python -m pytest packages/lingwen-illustrations/tests/ -v --rootdir=packages/lingwen-illustrations
/home/ailearn/projects/LingWen/.venv/bin/python -m pytest apps/studio_api/tests/ -v
ruff check packages/lingwen-illustrations/src/lingwen_illustrations/ apps/studio_api/routes/illustrations.py apps/studio_api/routes/reference_image.py
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm vitest run
pnpm tsc --noEmit
```

Expected: All green.

- [ ] **Step 7: Commit documentation**

```bash
cd /home/ailearn/projects/LingWen
git add CLAUDE.md .lingwen/architecture.yml collaboration/BACKLOG.md collaboration/CURRENT_STATUS.md docs/superpowers/handoffs/2026-09-18-phase-97-reference-image-i2i-handoff.md
git commit -m "docs(phase-97): CLAUDE.md v56.1 + I089 invariant + BACKLOG/CURRENT_STATUS + handoff"
```

---

## Self-Review (after plan written)

**1. Spec coverage:** Each spec section maps to one or more tasks:
- §2 Decision table → enforced by Task 1-13 implementations
- §3.1 ProviderAdapter → Task 4
- §3.2 Provider modules → Task 3
- §3.3 reference_image.py → Task 1-2
- §3.4 Pipeline dispatch → Task 5
- §3.5 IllustrationMetadata → Task 5
- §3.6 routes/reference_image.py → Task 6
- §3.7 illustrations route → Task 7
- §4.1-4.6 Frontend → Tasks 8-13
- §6 Testing → Tasks 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14
- §7 Risk → Task 7 (422 error mapping) + Task 12 (openai warning UX)

**2. Placeholder scan:** No "TBD" / "TODO" / "fill in details" markers. All test code is real Python/Vue, not pseudocode. All commands have exact paths.

**3. Type consistency:** `ProviderAdapter.name/generate/generate_with_reference/supports_i2i` consistently named. `reference_image_bytes` consistently typed `bytes | None`. `use_project_reference: bool` consistent across GenerateRequest, frontend payload, store.

**4. Plan produces:** ~14 atomic commits + 12 regression guards + ~85 new tests + handoff doc. Final Phase 97 state matches §10 DoD.

---

## Execution Handoff

Plan complete. 15 tasks total. Each task produces 1 atomic commit on master (per 2026-09-15 simplified workflow).

Two execution options:

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?