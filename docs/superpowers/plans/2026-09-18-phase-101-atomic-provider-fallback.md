# Phase 101 — Atomic Provider Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add cross-provider fallback chain to illustration generation pipeline — when primary provider's image API fails with transient error, automatically try next provider in chain.

**Architecture:** New `lingwen_illustrations.fallback` module encapsulates chain iteration logic. Pipeline's text-only Stage 4 calls `dispatch_with_fallback(chain, ...)` which iterates providers, calling `resolve_model` per provider and recording each attempt. Single audit event captures all attempts in `extra.attempts`. i2i path unchanged (no fallback). Backward compatible: empty chain = no behavior change from Phase 100.

**Tech Stack:** Python 3.12+ / FastAPI / Pydantic v2 / Vue 3 + Naive UI / uv workspace / pytest / vitest

**Workflow note:** Per 2026-09-15 simplified workflow, **direct commits on master** — no worktree, no branch, no ff-merge step. Each task's commit goes straight to `master`.

---

## File structure

| File | Action | Purpose |
|------|--------|---------|
| `packages/lingwen-illustrations/src/lingwen_illustrations/exceptions.py` | modify | Add `ProviderExhaustedError` class |
| `packages/lingwen-illustrations/src/lingwen_illustrations/fallback.py` | create | Attempt dataclass + dispatch_with_fallback async fn |
| `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py` | modify | Replace Stage 4 text-only dispatch with dispatch_with_fallback |
| `apps/studio_api/routes/project_settings.py` | modify | Add `fallback_chain: list[str] = []` to ProjectSettings |
| `apps/studio_api/routes/illustrations.py` | modify | GenerateRequest.fallback_chain + _resolve_provider_for_request returns tuple + STAGE_HTTP_CODES mapping |
| `apps/studio_api/routes/_project_helpers.py` | (no change) | Existing API |
| `apps/dashboard/src/api/illustrations.ts` | modify | Add fallback_chain param to fetchGenerateIllustration / fetchRegenerateIllustration |
| `apps/dashboard/src/stores/useProjectSettings.js` | modify | Add fallback_chain field |
| `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue` | modify | Add n-select multi picker |
| `.lingwen/architecture.yml` | modify | Add I093 invariant |
| `CLAUDE.md` | modify | v58.0 → v59.0 + I093 + handoff ref |
| `packages/lingwen-illustrations/tests/test_fallback.py` | create | Unit tests for fallback module (~16 tests) |
| `packages/lingwen-illustrations/tests/test_pipeline.py` | modify | Add ~9 fallback integration tests |
| `apps/studio_api/tests/test_illustrations_api.py` | modify | Add ~9 route integration tests |
| `apps/dashboard/src/components/illustrations/__tests__/ProjectSettingsIllustration.spec.ts` | modify | Add ~4 frontend tests |
| `tests/test_phase101_atomic_provider_fallback.py` | create | 10 regression guards G1-G10 |

**Test environment:**
- Backend pytest: prefer `uv run pytest` from repo root OR `/home/ailearn/miniconda3/bin/python -m pytest` fallback (per MEMORY.md warnings)
- Frontend vitest: `cd apps/dashboard && pnpm vitest run` (after `pnpm install` if fresh)
- Type check: `cd apps/dashboard && pnpm tsc --noEmit`
- Lint: `ruff check <files>` for Python

---

## Task 1: ProviderExhaustedError exception class

**Files:**
- Modify: `packages/lingwen-illustrations/src/lingwen_illustrations/exceptions.py:54-73` (after GenerateError)
- Test: `packages/lingwen-illustrations/tests/test_exceptions.py` (create if not exists, or add to test_fallback.py in Task 2)

- [ ] **Step 1: Write failing test for ProviderExhaustedError**

Create `packages/lingwen-illustrations/tests/test_exceptions_phase101.py`:

```python
"""Phase 101: ProviderExhaustedError exception class."""
from __future__ import annotations

import pytest

from lingwen_illustrations.exceptions import GenerateError, ProviderExhaustedError, Stage


def test_provider_exhausted_is_generate_error_subclass():
    """ProviderExhaustedError must be a GenerateError (catchable as such)."""
    err = ProviderExhaustedError(
        "all 3 providers failed",
        attempts=[],
        provider="stability",
    )
    assert isinstance(err, GenerateError)
    assert err.stage == Stage.GENERATE
    assert err.retryable is False
    assert err.provider == "stability"
    assert err.attempts == []
    assert "all 3 providers failed" in str(err)


def test_provider_exhausted_carries_attempts():
    """attempts list passed through to exception attribute."""
    attempts = [
        {"provider": "openai", "model": "dall-e-3", "error": "timeout", "ts": "2026-09-18T10:30:00Z"},
        {"provider": "stability", "model": "sd3", "error": None, "ts": "2026-09-18T10:30:03Z"},
    ]
    err = ProviderExhaustedError(
        "all providers failed",
        attempts=attempts,
        provider="stability",
    )
    assert err.attempts == attempts
    assert len(err.attempts) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/lingwen-illustrations && uv run pytest tests/test_exceptions_phase101.py -v`
Expected: FAIL with `ImportError: cannot import name 'ProviderExhaustedError'`

- [ ] **Step 3: Add ProviderExhaustedError to exceptions.py**

In `packages/lingwen-illustrations/src/lingwen_illustrations/exceptions.py`, after the `GenerateError` class (line 73) and before `StoreError` (line 76), add:

```python
class ProviderExhaustedError(GenerateError):
    """Phase 101: All providers in fallback chain failed with retryable errors.

    Subclass of GenerateError so existing catch blocks continue to work.
    retryable=False because the chain is exhausted (no point retrying the
    same chain without intervention). Carries .attempts for HTTP 502 detail.
    """

    def __init__(
        self,
        message: str,
        *,
        attempts: list[dict],
        provider: str,
    ) -> None:
        super().__init__(message, provider=provider, retryable=False)
        self.attempts = attempts
```

Also add `ProviderExhaustedError` to `__all__` at line 104-113:

```python
__all__ = [
    "Stage",
    "IllustrationError",
    "LoadError",
    "ExtractError",
    "ComposeError",
    "GenerateError",
    "ProviderExhaustedError",  # NEW (Phase 101)
    "StoreError",
    "UnknownModelError",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/lingwen-illustrations && uv run pytest tests/test_exceptions_phase101.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/src/lingwen_illustrations/exceptions.py packages/lingwen-illustrations/tests/test_exceptions_phase101.py
git commit -m "feat(phase-101): ProviderExhaustedError exception class + 2 tests"
```

---

## Task 2: fallback module — Attempt dataclass + dispatch_with_fallback skeleton

**Files:**
- Create: `packages/lingwen-illustrations/src/lingwen_illustrations/fallback.py`
- Modify: `packages/lingwen-illustrations/src/lingwen_illustrations/__init__.py` (add export)

- [ ] **Step 1: Write failing test for Attempt dataclass**

Create `packages/lingwen-illustrations/tests/test_fallback.py`:

```python
"""Phase 101: Atomic provider fallback chain dispatch."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from lingwen_illustrations.exceptions import (
    GenerateError,
    ProviderExhaustedError,
    UnknownModelError,
)
from lingwen_illustrations.fallback import Attempt, dispatch_with_fallback


# ---- helpers ----

async def _ok_generate(**kwargs):
    """Mock adapter.generate that returns b'ok-bytes'."""
    return b"ok-bytes"


async def _fail_generate(**kwargs):
    """Mock adapter.generate that raises retryable GenerateError."""
    raise GenerateError("502 server error", retryable=True, provider=kwargs.get("_test_provider", "openai"))


async def _fail_nonretryable(**kwargs):
    raise GenerateError("401 unauthorized", retryable=False, provider="openai")


async def _raise_unknown_model(**kwargs):
    raise UnknownModelError("openai", "nonexistent-model", ("dall-e-3",))


def _credentials_for(provider: str) -> tuple[str, str]:
    return ("test-key", "https://test.host")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---- A. Attempt dataclass ----

def test_attempt_dataclass_round_trip():
    """Attempt fields preserved; success/error cases both work."""
    a = Attempt(provider="openai", model="dall-e-3", error=None, ts=_now_iso())
    assert a.provider == "openai"
    assert a.model == "dall-e-3"
    assert a.error is None
    assert "T" in a.ts  # ISO format with T separator


def test_attempt_with_error():
    a = Attempt(provider="openai", model="dall-e-3", error="GenerateError: 502", ts=_now_iso())
    assert a.error == "GenerateError: 502"


# ---- B. Single-provider (no fallback) ----

@pytest.mark.asyncio
async def test_dispatch_single_provider_success(monkeypatch):
    """Chain=[primary], success → 1 attempt (the success one)."""
    from lingwen_illustrations import fallback
    from lingwen_illustrations.providers import minimax as mm_mod

    monkeypatch.setattr(mm_mod, "generate", _ok_generate)

    bytes_out, provider, model, attempts = await dispatch_with_fallback(
        chain=["minimax"],
        explicit_model=None,
        project_settings=None,
        api_credentials_for=_credentials_for,
        prompt="test prompt",
    )
    assert bytes_out == b"ok-bytes"
    assert provider == "minimax"
    assert len(attempts) == 1
    assert attempts[0].provider == "minimax"
    assert attempts[0].error is None  # success
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/lingwen-illustrations && uv run pytest tests/test_fallback.py -v`
Expected: FAIL with `ImportError: cannot import name 'Attempt' from 'lingwen_illustrations.fallback'`

- [ ] **Step 3: Create fallback.py with Attempt + dispatch_with_fallback skeleton**

Create `packages/lingwen-illustrations/src/lingwen_illustrations/fallback.py`:

```python
"""Cross-provider fallback chain dispatch (Phase 101).

Iterates a chain of provider names, calling each provider's image API.
Records every attempt; returns first success. On chain exhaustion with
all retryable failures, raises ProviderExhaustedError with full attempts list.

I093 invariant: dispatch_with_fallback is the only entry point for
cross-provider fallback iteration. pipeline.generate_illustration and
pipeline.regenerate_illustration text-only paths call this helper; i2i
paths bypass it.

Model resolution: each provider independently resolves its model via
Phase 100 resolve_model() 3-tier order. The primary's explicit_model is
honored; fallback providers use project default or provider default.

Audit: caller records attempts in `extra.attempts` of audit_log.record_event
(success attempt has error=None, failed attempts have error="<Class>: <msg>").
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Awaitable, Callable

from lingwen_illustrations.exceptions import (
    GenerateError,
    ProviderExhaustedError,
)
from lingwen_illustrations.providers import KNOWN_PROVIDERS, UnknownProviderError, get_provider
from lingwen_illustrations.pipeline import resolve_model  # local import to avoid cycle


@dataclass(frozen=True)
class Attempt:
    """One provider try in the fallback chain.

    error=None means success; error="<ExceptionClass>: <message>" on failure.
    """
    provider: str
    model: str
    error: str | None
    ts: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    """Remove duplicates while preserving first-occurrence order."""
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _filter_known_providers(chain: list[str]) -> list[str]:
    """Keep only KNOWN_PROVIDERS; warn + skip the rest."""
    import logging
    logger = logging.getLogger(__name__)
    out: list[str] = []
    for provider in chain:
        if provider in KNOWN_PROVIDERS:
            out.append(provider)
        else:
            logger.warning(
                "fallback chain contains unknown provider '%s'; skipping", provider,
            )
    return out


async def dispatch_with_fallback(
    *,
    chain: list[str],
    explicit_model: str | None,
    project_settings: dict | None,
    api_credentials_for: Callable[[str], tuple[str, str]],
    prompt: str,
    i2i: bool = False,
    reference_image_bytes: bytes | None = None,
) -> tuple[bytes, str, str, list[Attempt]]:
    """Iterate chain. Return (bytes, success_provider, success_model, attempts).

    Args:
        chain: Ordered provider names. First is primary; rest are fallbacks.
            Items not in KNOWN_PROVIDERS are silently skipped (logged).
        explicit_model: Model override for the PRIMARY provider only. None means
            use Phase 100 3-tier resolution. Fallback providers always use
            their own project default or provider default (no explicit override).
        project_settings: Loaded illustration_settings.yaml dict (or None).
        api_credentials_for: Callable provider_name -> (api_key, api_host).
        prompt: Final composed prompt.
        i2i: True for image-to-image path. Bypasses fallback (single attempt).
        reference_image_bytes: Required when i2i=True.

    Returns:
        Tuple of (image_bytes, successful_provider, successful_model, attempts).
        attempts always has at least one entry; successful one is last with error=None.

    Raises:
        GenerateError(retryable=False): Non-retryable error (e.g. 4xx user error).
            Propagates immediately without trying fallback.
        UnknownProviderError: Provider not in KNOWN_PROVIDERS at adapter lookup.
        UnknownModelError: Resolved model not in adapter.models.
        ProviderExhaustedError: All retryable failures (chain exhausted).
    """
    import logging
    logger = logging.getLogger(__name__)

    # Build deduped chain of valid providers. Empty chain = primary-only.
    valid_chain = _filter_known_providers(_dedupe_preserve_order(chain))
    if not valid_chain:
        raise UnknownProviderError(
            f"fallback chain empty after filtering: {chain}"
        )

    attempts: list[Attempt] = []

    for idx, provider in enumerate(valid_chain):
        adapter = get_provider(provider)
        # Primary (first) gets explicit_model; fallbacks always None (per-provider default).
        explicit = explicit_model if idx == 0 else None
        model = resolve_model(
            provider=provider,
            explicit=explicit,
            project_settings=project_settings,
            adapter=adapter,
        )

        # i2i: pre-flight check (Phase 97 semantics).
        if i2i:
            if not adapter.supports_i2i:
                # No fallback for i2i path. GenerateError(retryable=False).
                raise GenerateError(
                    f"provider '{provider}' does not support image-to-image generation",
                    provider=provider,
                    retryable=False,
                )
            generate_fn = adapter.generate_with_reference
            call_kwargs = dict(
                prompt=prompt,
                reference_image_bytes=reference_image_bytes,
            )
        else:
            generate_fn = adapter.generate
            call_kwargs = dict(prompt=prompt)

        api_key, api_host = api_credentials_for(provider)
        call_kwargs.update(api_key=api_key, api_host=api_host, model=model)

        try:
            image_bytes = await generate_fn(**call_kwargs)
            attempts.append(Attempt(provider=provider, model=model, error=None, ts=_now_iso()))
            return image_bytes, provider, model, attempts
        except GenerateError as e:
            if not e.retryable:
                # 4xx / i2i unsupported: propagate immediately. Don't record attempt
                # for fallback decision (this is a user/config error, not a try).
                raise
            attempts.append(Attempt(
                provider=provider, model=model,
                error=f"GenerateError: {e.message}",
                ts=_now_iso(),
            ))
            logger.info(
                "fallback: provider '%s' failed retryable (%s); trying next",
                provider, e.message,
            )
            continue
        # UnknownProviderError and UnknownModelError propagate (config bugs).

    # Chain exhausted.
    raise ProviderExhaustedError(
        f"all {len(valid_chain)} providers failed: "
        + ", ".join(f"{a.provider}({a.error})" for a in attempts),
        attempts=[a.__dict__ for a in attempts],
        provider=valid_chain[-1],
    )


__all__ = ["Attempt", "dispatch_with_fallback"]
```

Note: `Attempt.__dict__` returns a dict with all 4 fields. This matches the
audit extra schema.

- [ ] **Step 4: Add fallback to package exports**

In `packages/lingwen-illustrations/src/lingwen_illustrations/__init__.py`, add to imports (if there's a re-export list) — check file first. If no explicit re-exports, no change needed. The dispatch_with_fallback can be imported as `from lingwen_illustrations.fallback import dispatch_with_fallback`.

- [ ] **Step 5: Run test to verify Attempt + single-provider pass**

Run: `cd packages/lingwen-illustrations && uv run pytest tests/test_fallback.py -v -k "Attempt or single_provider_success"`
Expected: 3 tests PASS (test_attempt_dataclass_round_trip, test_attempt_with_error, test_dispatch_single_provider_success)

- [ ] **Step 6: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/src/lingwen_illustrations/fallback.py packages/lingwen-illustrations/tests/test_fallback.py
git commit -m "feat(phase-101): fallback module — Attempt + dispatch_with_fallback skeleton"
```

---

## Task 3: fallback module — chain retry, exhaustion, errors

**Files:**
- Modify: `packages/lingwen-illustrations/tests/test_fallback.py` (add tests)

- [ ] **Step 1: Add remaining unit tests to test_fallback.py**

Append the following tests to `packages/lingwen-illustrations/tests/test_fallback.py`:

```python
# ---- C. Fallback chain behavior ----

@pytest.mark.asyncio
async def test_dispatch_primary_success_ignores_chain(monkeypatch):
    """Primary success → fallback not tried; only 1 attempt."""
    from lingwen_illustrations.providers import openai as oa_mod, stability as st_mod

    monkeypatch.setattr(oa_mod, "generate", _ok_generate)
    monkeypatch.setattr(st_mod, "generate", _fail_generate)  # would fail if called

    bytes_out, provider, model, attempts = await dispatch_with_fallback(
        chain=["openai", "stability"],
        explicit_model=None,
        project_settings=None,
        api_credentials_for=_credentials_for,
        prompt="test",
    )
    assert bytes_out == b"ok-bytes"
    assert provider == "openai"
    assert len(attempts) == 1
    assert attempts[0].provider == "openai"


@pytest.mark.asyncio
async def test_dispatch_primary_retryable_triggers_next(monkeypatch):
    """Primary retryable → fallback tried; 2 attempts total."""
    from lingwen_illustrations.providers import openai as oa_mod, stability as st_mod

    monkeypatch.setattr(oa_mod, "generate", _fail_generate)
    monkeypatch.setattr(st_mod, "generate", _ok_generate)

    bytes_out, provider, model, attempts = await dispatch_with_fallback(
        chain=["openai", "stability"],
        explicit_model=None,
        project_settings=None,
        api_credentials_for=_credentials_for,
        prompt="test",
    )
    assert bytes_out == b"ok-bytes"
    assert provider == "stability"
    assert len(attempts) == 2
    assert attempts[0].provider == "openai"
    assert attempts[0].error is not None
    assert attempts[1].provider == "stability"
    assert attempts[1].error is None


@pytest.mark.asyncio
async def test_dispatch_non_retryable_does_not_fallback(monkeypatch):
    """Primary non-retryable → immediate raise; fallback NOT tried."""
    from lingwen_illustrations.providers import openai as oa_mod, stability as st_mod

    monkeypatch.setattr(oa_mod, "generate", _fail_nonretryable)
    monkeypatch.setattr(st_mod, "generate", _ok_generate)  # should NOT be called

    with pytest.raises(GenerateError) as exc_info:
        await dispatch_with_fallback(
            chain=["openai", "stability"],
            explicit_model=None,
            project_settings=None,
            api_credentials_for=_credentials_for,
            prompt="test",
        )
    assert exc_info.value.retryable is False
    assert exc_info.value.provider == "openai"


@pytest.mark.asyncio
async def test_dispatch_unknown_model_does_not_fallback(monkeypatch):
    """UnknownModelError propagates immediately (config bug, not transient)."""
    from lingwen_illustrations.providers import openai as oa_mod, stability as st_mod

    monkeypatch.setattr(oa_mod, "generate", _raise_unknown_model)
    monkeypatch.setattr(st_mod, "generate", _ok_generate)

    with pytest.raises(UnknownModelError):
        await dispatch_with_fallback(
            chain=["openai", "stability"],
            explicit_model=None,
            project_settings=None,
            api_credentials_for=_credentials_for,
            prompt="test",
        )


@pytest.mark.asyncio
async def test_dispatch_all_exhausted_raises_provider_exhausted(monkeypatch):
    """All retryable → ProviderExhaustedError with attempts list."""
    from lingwen_illustrations.providers import openai as oa_mod, stability as st_mod, minimax as mm_mod

    monkeypatch.setattr(oa_mod, "generate", _fail_generate)
    monkeypatch.setattr(st_mod, "generate", _fail_generate)
    monkeypatch.setattr(mm_mod, "generate", _fail_generate)

    with pytest.raises(ProviderExhaustedError) as exc_info:
        await dispatch_with_fallback(
            chain=["openai", "stability", "minimax"],
            explicit_model=None,
            project_settings=None,
            api_credentials_for=_credentials_for,
            prompt="test",
        )
    err = exc_info.value
    assert err.retryable is False
    assert err.provider == "minimax"  # last tried
    assert len(err.attempts) == 3
    assert all(a["error"] is not None for a in err.attempts)
    assert "openai" in err.attempts[0]["provider"]


@pytest.mark.asyncio
async def test_dispatch_chain_skips_unknown_provider(monkeypatch, caplog):
    """Unknown provider in chain → warning + skip; known providers still tried."""
    import logging
    from lingwen_illustrations.providers import openai as oa_mod

    monkeypatch.setattr(oa_mod, "generate", _ok_generate)

    with caplog.at_level(logging.WARNING):
        bytes_out, provider, model, attempts = await dispatch_with_fallback(
            chain=["unknown-provider", "openai"],
            explicit_model=None,
            project_settings=None,
            api_credentials_for=_credentials_for,
            prompt="test",
        )
    assert provider == "openai"
    assert len(attempts) == 1
    assert "unknown provider" in caplog.text.lower()


@pytest.mark.asyncio
async def test_dispatch_chain_dedupes_preserving_order(monkeypatch):
    """[a, b, a, c] → [a, b, c] (dedup, first-occurrence order)."""
    from lingwen_illustrations.providers import (
        openai as oa_mod,
        stability as st_mod,
        minimax as mm_mod,
    )

    monkeypatch.setattr(oa_mod, "generate", _fail_generate)
    monkeypatch.setattr(st_mod, "generate", _ok_generate)
    monkeypatch.setattr(mm_mod, "generate", _fail_generate)

    bytes_out, provider, model, attempts = await dispatch_with_fallback(
        chain=["openai", "stability", "openai", "minimax"],
        explicit_model=None,
        project_settings=None,
        api_credentials_for=_credentials_for,
        prompt="test",
    )
    assert provider == "stability"
    # Attempts: openai (fail), stability (success) — openai and minimax skipped due to dedup
    assert [a.provider for a in attempts] == ["openai", "stability"]


@pytest.mark.asyncio
async def test_dispatch_i2i_path_skips_fallback(monkeypatch):
    """i2i=True + adapter supports_i2i → single attempt, no fallback."""
    from lingwen_illustrations.providers import openai as oa_mod, stability as st_mod

    # Note: openai does NOT support i2i (Phase 97). Use stability for this test.
    monkeypatch.setattr(st_mod, "generate_with_reference", _ok_generate)

    bytes_out, provider, model, attempts = await dispatch_with_fallback(
        chain=["stability", "openai"],  # openai fallback should NOT be tried
        explicit_model=None,
        project_settings=None,
        api_credentials_for=_credentials_for,
        prompt="test",
        i2i=True,
        reference_image_bytes=b"reference-image-bytes",
    )
    assert bytes_out == b"ok-bytes"
    assert provider == "stability"
    assert len(attempts) == 1  # fallback NOT tried


@pytest.mark.asyncio
async def test_dispatch_i2i_unsupported_provider_raises(monkeypatch):
    """i2i=True + adapter.supports_i2i=False → GenerateError(retryable=False)."""
    from lingwen_illustrations.providers import openai as oa_mod

    monkeypatch.setattr(oa_mod, "generate_with_reference", _ok_generate)  # would succeed if called

    with pytest.raises(GenerateError) as exc_info:
        await dispatch_with_fallback(
            chain=["openai", "stability"],
            explicit_model=None,
            project_settings=None,
            api_credentials_for=_credentials_for,
            prompt="test",
            i2i=True,
            reference_image_bytes=b"reference-image-bytes",
        )
    assert "image-to-image" in exc_info.value.message
    assert exc_info.value.retryable is False


@pytest.mark.asyncio
async def test_dispatch_resolves_model_per_provider(monkeypatch):
    """Each provider in chain independently resolves its model via Phase 100 logic."""
    from lingwen_illustrations.providers import openai as oa_mod, stability as st_mod

    captured_models: list[str] = []

    async def _capture_model(**kwargs):
        captured_models.append(kwargs.get("model"))
        return b"ok"

    monkeypatch.setattr(oa_mod, "generate", _capture_model)
    monkeypatch.setattr(st_mod, "generate", _capture_model)

    # explicit_model="dall-e-3-hd" only applies to primary (openai); stability uses its own default.
    await dispatch_with_fallback(
        chain=["openai", "stability"],
        explicit_model="dall-e-3-hd",
        project_settings=None,
        api_credentials_for=_credentials_for,
        prompt="test",
    )
    assert captured_models[0] == "dall-e-3-hd"  # primary explicit
    # stability default (sd3-medium per KNOWN_MODELS)
    assert captured_models[1] == "sd3-medium"


def test_attempt_last_entry_is_success():
    """On success, attempts last entry has error=None."""
    attempts = [
        Attempt(provider="openai", model="dall-e-3", error="GenerateError: 502", ts=_now_iso()),
        Attempt(provider="stability", model="sd3", error=None, ts=_now_iso()),
    ]
    assert attempts[-1].error is None
    assert attempts[-1].provider == "stability"
```

- [ ] **Step 2: Run tests to verify all pass**

Run: `cd packages/lingwen-illustrations && uv run pytest tests/test_fallback.py -v`
Expected: 14 tests PASS (3 from Task 2 + 11 new)

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/tests/test_fallback.py
git commit -m "test(phase-101): fallback dispatch — chain retry + exhaustion + i2i no-fallback"
```

---

## Task 4: pipeline.generate_illustration — integrate fallback

**Files:**
- Modify: `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py:147-311`

- [ ] **Step 1: Add failing pipeline integration test for fallback**

Add to `packages/lingwen-illustrations/tests/test_pipeline.py` (create file if not exists, or add to existing):

```python
"""Phase 101: pipeline integration tests for fallback chain."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml


@pytest.fixture
def project_with_settings(tmp_path: Path) -> Path:
    """Project root with illustration_settings.yaml containing fallback_chain."""
    lingwen_dir = tmp_path / ".lingwen"
    lingwen_dir.mkdir()
    (lingwen_dir / "illustration_settings.yaml").write_text(
        yaml.safe_dump({
            "default_provider": "openai",
            "fallback_chain": ["stability", "minimax"],
        }),
        encoding="utf-8",
    )
    return tmp_path


@pytest.mark.asyncio
async def test_generate_fallback_records_attempts_in_audit(
    project_with_settings: Path, monkeypatch,
):
    """When primary fails and fallback succeeds, audit extra.attempts has 2 entries."""
    from lingwen_illustrations import audit_log, pipeline
    from lingwen_illustrations.providers import openai as oa_mod, stability as st_mod

    # Mock extract + compose to skip real LLM
    monkeypatch.setattr(pipeline, "extract_scene", lambda **kw: {"scene": "test"})
    monkeypatch.setattr(pipeline, "compose_prompt", lambda *a, **kw: "test prompt")

    # Primary (openai) fails retryable; fallback (stability) succeeds
    monkeypatch.setattr(oa_mod, "generate", AsyncMock(side_effect=Exception("boom 502")))
    monkeypatch.setattr(st_mod, "generate", AsyncMock(return_value=b"fake-jpeg-bytes"))

    # Patch audit to capture the call
    captured_events: list[dict] = []

    def _capture_record(project_root, *, event, asset_meta=None, confirmed=None,
                       bypassed=False, extra=None, id=None):
        if event == "generation":
            captured_events.append({"event": event, "extra": extra or {}})

    monkeypatch.setattr(audit_log, "record_event", _capture_record)

    meta = await pipeline.generate_illustration(
        project_root=project_with_settings,
        project_slug="test-slug",
        type="cover",
        chapter_num=None,
        style_preset="test-preset",
        custom_prompt=None,
        api_key="fake-key",
        api_host="https://fake.host",
        provider="openai",
        model=None,
        reference_image_bytes=None,
        fallback_chain=["stability", "minimax"],  # explicit override
    )

    assert meta.provider == "stability"  # successful one
    assert len(captured_events) == 1
    attempts = captured_events[0]["extra"].get("attempts", [])
    assert len(attempts) == 2
    assert attempts[0]["provider"] == "openai"
    assert attempts[0]["error"] is not None
    assert attempts[1]["provider"] == "stability"
    assert attempts[1]["error"] is None


@pytest.mark.asyncio
async def test_generate_no_fallback_when_chain_empty(monkeypatch, tmp_path: Path):
    """Empty fallback_chain → only primary tried (Phase 100 compat)."""
    from lingwen_illustrations import audit_log, pipeline
    from lingwen_illustrations.providers import openai as oa_mod, stability as st_mod

    monkeypatch.setattr(pipeline, "extract_scene", lambda **kw: {"scene": "test"})
    monkeypatch.setattr(pipeline, "compose_prompt", lambda *a, **kw: "test prompt")

    primary_called = []
    fallback_called = []

    async def _primary_ok(**kwargs):
        primary_called.append(kwargs.get("model"))
        return b"primary-jpeg"

    async def _fallback_should_not_run(**kwargs):
        fallback_called.append(kwargs.get("model"))
        return b"fallback-jpeg"

    monkeypatch.setattr(oa_mod, "generate", _primary_ok)
    monkeypatch.setattr(st_mod, "generate", _fallback_should_not_run)

    captured_events: list[dict] = []

    def _capture(project_root, *, event, **kwargs):
        if event == "generation":
            captured_events.append({"extra": kwargs.get("extra") or {}})

    monkeypatch.setattr(audit_log, "record_event", _capture)

    meta = await pipeline.generate_illustration(
        project_root=tmp_path,
        project_slug="test",
        type="cover",
        chapter_num=None,
        style_preset="test-preset",
        custom_prompt=None,
        api_key="fake",
        api_host="https://fake.host",
        provider="openai",
        model=None,
        reference_image_bytes=None,
        fallback_chain=[],  # empty = no fallback
    )

    assert meta.provider == "openai"
    assert len(primary_called) == 1
    assert len(fallback_called) == 0  # never tried
    assert len(captured_events[0]["extra"].get("attempts", [])) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/lingwen-illustrations && uv run pytest tests/test_pipeline.py -v -k "fallback"`
Expected: FAIL with `TypeError: generate_illustration() got an unexpected keyword argument 'fallback_chain'`

- [ ] **Step 3: Modify pipeline.py to accept fallback_chain + integrate dispatch**

In `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py`, modify `generate_illustration`:

Change signature (after line 159):

```python
    reference_image_bytes: bytes | None = None,  # NEW (Phase 97)
    fallback_chain: list[str] | None = None,    # NEW (Phase 101). None → load from settings.
) -> IllustrationMetadata:
```

Update docstring (lines 175-183) to mention Phase 101:

```python
    Raises:
        LoadError: Project / chapter / character bible missing or malformed.
        ExtractError: Stage 1 LLM failed.
        ComposeError: Stage 2 template failed (invalid preset).
        GenerateError: Stage 3 image API failed.
        StoreError: Stage 4 file write failed.
        UnknownProviderError: provider name not in providers.KNOWN_PROVIDERS.
        UnknownModelError: explicit model not in provider's KNOWN_MODELS.
        ProviderExhaustedError: NEW (Phase 101). All providers in chain failed retryably.
```

Replace Stage 4 block (lines 202-233) with:

```python
    # Stage 4: provider dispatch. Phase 97: route to i2i vs text based on reference_image_bytes.
    # Phase 100: resolve model via 3-tier order (explicit > project > provider default).
    # Phase 101: fallback chain for text-only path; i2i path bypasses fallback.
    from lingwen_illustrations.fallback import Attempt, dispatch_with_fallback
    settings = _load_illustration_settings(project_root)

    # Resolve effective fallback_chain: explicit param > settings > [].
    effective_chain: list[str] = list(fallback_chain or settings.get("fallback_chain") or [])

    if reference_image_bytes is not None:
        # i2i path: NO fallback (Phase 101). Single provider call.
        adapter = get_provider(provider)
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
            # NOTE: model NOT threaded to i2i path (Phase 100 v1 limitation).
        )
        # i2i attempts: single success entry (no fallback).
        # Resolve model via Phase 100 3-tier for the metadata record.
        effective_model = resolve_model(
            provider=provider,
            explicit=model,
            project_settings=settings,
            adapter=adapter,
        )
        attempts: list[Attempt] = [
            Attempt(provider=provider, model=effective_model, error=None, ts=_iso_utc_now()),
        ]
    else:
        # Text-only path: fallback chain dispatch (Phase 101).
        def _credentials_for(p: str) -> tuple[str, str]:
            """Local credentials dispatcher for fallback chain providers.

            Reuses the existing api_key/api_host passed for the primary.
            In v1, all providers in a chain share the same primary credentials
            (per-project API keys are not yet distinguished); v2 may split.
            """
            return (api_key, api_host)

        chain = [provider] + effective_chain
        image_bytes, success_provider, success_model, attempts = await dispatch_with_fallback(
            chain=chain,
            explicit_model=model,
            project_settings=settings,
            api_credentials_for=_credentials_for,
            prompt=final_prompt,
        )
        # Update effective_provider/model for metadata + audit.
        provider = success_provider
        effective_model = success_model
```

Replace the meta builder lines 239-253 (which builds meta with provider/model):

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
        model=effective_model,  # Phase 100/101: resolved model from successful provider
        provider=provider,      # NEW (Phase 101): successful provider (may differ from requested)
        used_reference_image=reference_image_bytes is not None,  # NEW (Phase 97)
        created_at=_iso_utc_now(),
    )
```

Update the audit `extra` (lines 286-294) to include attempts:

```python
        audit_log.record_event(
            project_root,
            event="generation",
            asset_meta=meta,
            confirmed=None,  # generation from generate_illustration is API-driven (no user confirm dialog at this layer)
            bypassed=False,
            extra={
                "auto_generate": _auto_generate,
                "confirm_required": _confirm_required,
                "attempts": [a.__dict__ for a in attempts],  # NEW (Phase 101)
            },
            id=_event_id,
        )
        notifications.publish(notifications.NotificationEvent(
            id=_event_id,
            project_slug=project_slug,
            event_type="generation",
            asset_id=meta.id,
            asset_type=meta.type,
            chapter_num=meta.chapter_num,
            style_preset=meta.style_preset,
            provider=provider,  # NEW (Phase 101): successful provider
            ts=notifications.now_iso(),
            extra={
                "auto_generate": _auto_generate,
                "confirm_required": _confirm_required,
                "attempts": [a.__dict__ for a in attempts],  # NEW (Phase 101)
            },
        ))
```

- [ ] **Step 4: Run pipeline tests to verify pass**

Run: `cd packages/lingwen-illustrations && uv run pytest tests/test_pipeline.py -v -k "fallback"`
Expected: 2 PASS (test_generate_fallback_records_attempts_in_audit + test_generate_no_fallback_when_chain_empty)

- [ ] **Step 5: Run all pipeline tests to verify no regression**

Run: `cd packages/lingwen-illustrations && uv run pytest tests/ -v`
Expected: All existing tests still pass; new tests added.

- [ ] **Step 6: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py packages/lingwen-illustrations/tests/test_pipeline.py
git commit -m "feat(phase-101): pipeline.generate_illustration — fallback chain dispatch + audit attempts"
```

---

## Task 5: pipeline.regenerate_illustration — integrate fallback

**Files:**
- Modify: `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py:314-462`

- [ ] **Step 1: Add failing pipeline test for regenerate fallback**

Append to `packages/lingwen-illustrations/tests/test_pipeline.py`:

```python
@pytest.mark.asyncio
async def test_regenerate_fallback_chain_uses_existing_provider(monkeypatch, tmp_path: Path):
    """regenerate with body.provider=None uses existing_meta.provider + chain."""
    from lingwen_illustrations import audit_log, pipeline
    from lingwen_illustrations.metadata import IllustrationMetadata
    from lingwen_illustrations.providers import openai as oa_mod, stability as st_mod

    monkeypatch.setattr(pipeline, "extract_scene", lambda **kw: {"scene": "regen"})
    monkeypatch.setattr(pipeline, "compose_prompt", lambda *a, **kw: "regen prompt")

    monkeypatch.setattr(oa_mod, "generate", AsyncMock(side_effect=Exception("boom 502")))
    monkeypatch.setattr(st_mod, "generate", AsyncMock(return_value=b"regen-jpeg"))

    # Mock storage.replace_asset to be a no-op
    from lingwen_illustrations import storage
    monkeypatch.setattr(storage, "replace_asset", lambda *a, **kw: None)

    captured_events: list[dict] = []

    def _capture(project_root, *, event, **kwargs):
        if event == "regeneration":
            captured_events.append({"extra": kwargs.get("extra") or {}})

    monkeypatch.setattr(audit_log, "record_event", _capture)

    existing_meta = IllustrationMetadata(
        id="old-id",
        type="cover",
        project_slug="test",
        chapter_num=None,
        style_preset="test",
        custom_prompt=None,
        scene_json={},
        final_prompt="orig",
        prompt_hash="sha256:abc",
        model="dall-e-3",
        provider="openai",
        used_reference_image=False,
        created_at="2026-09-18T00:00:00Z",
    )

    new_meta = await pipeline.regenerate_illustration(
        project_root=tmp_path,
        existing_meta=existing_meta,
        api_key="fake",
        api_host="https://fake.host",
        provider=None,  # → use existing_meta.provider (= openai)
        model=None,
        reference_image_bytes=None,
        fallback_chain=["stability"],
    )

    assert new_meta.provider == "stability"  # fallback succeeded
    assert new_meta.id == "old-id"  # preserved
    attempts = captured_events[0]["extra"].get("attempts", [])
    assert len(attempts) == 2
    assert attempts[0]["provider"] == "openai"  # primary first
    assert attempts[1]["provider"] == "stability"


@pytest.mark.asyncio
async def test_regenerate_fallback_preserves_asset_id(monkeypatch, tmp_path: Path):
    """On fallback success, atomic replace_asset is called (asset_id preserved)."""
    from lingwen_illustrations import pipeline, storage
    from lingwen_illustrations.metadata import IllustrationMetadata
    from lingwen_illustrations.providers import openai as oa_mod, stability as st_mod

    monkeypatch.setattr(pipeline, "extract_scene", lambda **kw: {"scene": "test"})
    monkeypatch.setattr(pipeline, "compose_prompt", lambda *a, **kw: "test")

    monkeypatch.setattr(oa_mod, "generate", AsyncMock(side_effect=Exception("boom")))
    monkeypatch.setattr(st_mod, "generate", AsyncMock(return_value=b"new-jpeg"))

    replace_calls: list[dict] = []

    def _capture_replace(project_root, image_bytes, meta):
        replace_calls.append({"asset_id": meta.id, "provider": meta.provider})

    monkeypatch.setattr(storage, "replace_asset", _capture_replace)

    existing_meta = IllustrationMetadata(
        id="preserved-id",
        type="cover",
        project_slug="test",
        chapter_num=None,
        style_preset="test",
        custom_prompt=None,
        scene_json={},
        final_prompt="orig",
        prompt_hash="sha256:abc",
        model="dall-e-3",
        provider="openai",
        used_reference_image=False,
        created_at="2026-09-18T00:00:00Z",
    )

    new_meta = await pipeline.regenerate_illustration(
        project_root=tmp_path,
        existing_meta=existing_meta,
        api_key="fake",
        api_host="https://fake.host",
        provider=None,
        model=None,
        reference_image_bytes=None,
        fallback_chain=["stability"],
    )

    assert new_meta.id == "preserved-id"  # Phase 94 invariant preserved
    assert len(replace_calls) == 1
    assert replace_calls[0]["asset_id"] == "preserved-id"
    assert replace_calls[0]["provider"] == "stability"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/lingwen-illustrations && uv run pytest tests/test_pipeline.py -v -k "regenerate_fallback"`
Expected: FAIL with `TypeError: regenerate_illustration() got an unexpected keyword argument 'fallback_chain'`

- [ ] **Step 3: Modify pipeline.regenerate_illustration**

In `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py`, modify `regenerate_illustration`:

Change signature (after line 322):

```python
    reference_image_bytes: bytes | None = None,  # NEW (Phase 97)
    fallback_chain: list[str] | None = None,    # NEW (Phase 101). None → load from settings.
) -> IllustrationMetadata:
```

Update docstring (after line 340) to mention Phase 101:

```python
    Phase 101: when `fallback_chain` is provided (or settings has it),
    iterates through [effective_provider, *fallback_chain] and tries
    each on retryable GenerateError. Successful provider recorded on
    IllustrationMetadata.provider; all attempts in audit extra.
    i2i path does NOT use fallback (Phase 101).
```

Replace Stage 4 block (lines 382-412) with:

```python
    # Stage 4: regenerate image bytes via provider. Phase 97: route to i2i vs text.
    # Phase 100: resolve model via 3-tier order (explicit > project > provider default).
    # Phase 101: fallback chain for text-only path; i2i path bypasses fallback.
    from lingwen_illustrations.fallback import Attempt, dispatch_with_fallback
    settings = _load_illustration_settings(project_root)

    effective_chain: list[str] = list(fallback_chain or settings.get("fallback_chain") or [])

    if reference_image_bytes is not None:
        # i2i path: NO fallback (Phase 101). Single provider call.
        adapter = get_provider(effective_provider)
        if not adapter.supports_i2i:
            raise GenerateError(
                f"provider '{effective_provider}' does not support image-to-image generation",
                provider=effective_provider,
                retryable=False,
            )
        image_bytes = await adapter.generate_with_reference(
            prompt=final_prompt,
            reference_image_bytes=reference_image_bytes,
            api_key=api_key,
            api_host=api_host,
        )
        effective_model = resolve_model(
            provider=effective_provider,
            explicit=model,
            project_settings=settings,
            adapter=adapter,
        )
        attempts: list[Attempt] = [
            Attempt(provider=effective_provider, model=effective_model, error=None, ts=_iso_utc_now()),
        ]
    else:
        # Text-only path: fallback chain dispatch (Phase 101).
        def _credentials_for(p: str) -> tuple[str, str]:
            return (api_key, api_host)

        chain = [effective_provider] + effective_chain
        image_bytes, success_provider, success_model, attempts = await dispatch_with_fallback(
            chain=chain,
            explicit_model=model,
            project_settings=settings,
            api_credentials_for=_credentials_for,
            prompt=final_prompt,
        )
        effective_provider = success_provider
        effective_model = success_model
```

Update the new_meta builder (lines 414-430):

```python
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
        model=effective_model,
        provider=effective_provider,  # NEW (Phase 101): successful provider
        used_reference_image=reference_image_bytes is not None,
        created_at=_iso_utc_now(),
    )
```

Update the audit `extra` (lines 436-460) to include attempts:

```python
    try:
        from lingwen_illustrations import audit_log
        _event_id = notifications.new_event_id()
        audit_log.record_event(
            project_root,
            event="regeneration",
            asset_meta=new_meta,
            extra={"attempts": [a.__dict__ for a in attempts]},  # NEW (Phase 101)
            id=_event_id,
        )
        notifications.publish(notifications.NotificationEvent(
            id=_event_id,
            project_slug=existing_meta.project_slug,
            event_type="regeneration",
            asset_id=new_meta.id,
            asset_type=new_meta.type,
            chapter_num=new_meta.chapter_num,
            style_preset=new_meta.style_preset,
            provider=effective_provider,  # NEW (Phase 101): successful provider
            ts=notifications.now_iso(),
            extra={"attempts": [a.__dict__ for a in attempts]},  # NEW (Phase 101)
        ))
    except Exception:
        pass
```

- [ ] **Step 4: Run tests to verify pass**

Run: `cd packages/lingwen-illustrations && uv run pytest tests/test_pipeline.py -v -k "regenerate_fallback"`
Expected: 2 PASS

- [ ] **Step 5: Run full pipeline test suite**

Run: `cd packages/lingwen-illustrations && uv run pytest tests/ -v`
Expected: All pass (existing tests + 4 new fallback tests)

- [ ] **Step 6: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py packages/lingwen-illustrations/tests/test_pipeline.py
git commit -m "feat(phase-101): pipeline.regenerate_illustration — fallback chain dispatch + audit attempts"
```

---

## Task 6: ProjectSettings — add fallback_chain field

**Files:**
- Modify: `apps/studio_api/routes/project_settings.py:26-35`

- [ ] **Step 1: Write failing test for ProjectSettings.fallback_chain**

Add to `apps/studio_api/tests/test_project_settings_api.py` (or create if not exists):

```python
"""Phase 101: ProjectSettings.fallback_chain field."""
from __future__ import annotations

import pytest
import yaml


def test_settings_pydantic_accepts_fallback_chain():
    """Pydantic v2 default fill: fallback_chain defaults to []."""
    from apps.studio_api.routes.project_settings import ProjectSettings

    settings = ProjectSettings(fallback_chain=["openai", "stability"])
    assert settings.fallback_chain == ["openai", "stability"]


def test_settings_pydantic_default_empty_list():
    settings = ProjectSettings()
    assert settings.fallback_chain == []


def test_settings_yaml_round_trip_with_fallback_chain(tmp_path):
    """YAML serialization preserves fallback_chain."""
    from apps.studio_api.routes.project_settings import (
        ProjectSettings,
        _load_settings,
        _save_settings,
    )

    settings = ProjectSettings(
        default_provider="openai",
        fallback_chain=["stability", "minimax"],
    )
    _save_settings(tmp_path, settings)
    loaded = _load_settings(tmp_path)
    assert loaded.fallback_chain == ["stability", "minimax"]


def test_settings_yaml_missing_field_defaults_empty(tmp_path):
    """Old yaml (Phase 100 baseline, no fallback_chain key) loads with empty list."""
    (tmp_path / ".lingwen").mkdir()
    (tmp_path / ".lingwen" / "illustration_settings.yaml").write_text(
        yaml.safe_dump({"default_provider": "openai"}),
        encoding="utf-8",
    )
    from apps.studio_api.routes.project_settings import _load_settings

    loaded = _load_settings(tmp_path)
    assert loaded.default_provider == "openai"
    assert loaded.fallback_chain == []  # Phase 100 back-compat preserved
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_project_settings_api.py -v -k "fallback_chain"`
Expected: FAIL with `TypeError: ProjectSettings() got an unexpected keyword argument 'fallback_chain'`

- [ ] **Step 3: Add fallback_chain to ProjectSettings**

In `apps/studio_api/routes/project_settings.py`, modify ProjectSettings class (lines 26-35):

```python
class ProjectSettings(BaseModel):
    """Phase 101: extended with fallback_chain.

    Schema migration is back-compat: Pydantic v2 fills missing fields with defaults.
    Old yaml files from Phase 100 (without fallback_chain) still load successfully.
    """
    default_provider: Literal["minimax", "openai", "stability"] = "minimax"
    default_models: dict[str, str] = {}                  # Phase 100
    auto_generate: bool = False                          # Phase 98
    max_assets: int = 20                                # Phase 98
    confirm_before_generate: bool = False               # Phase 98
    fallback_chain: list[str] = []                      # NEW (Phase 101)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_project_settings_api.py -v -k "fallback_chain"`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/studio_api/routes/project_settings.py apps/studio_api/tests/test_project_settings_api.py
git commit -m "feat(phase-101): ProjectSettings.fallback_chain field + back-compat"
```

---

## Task 7: GenerateRequest.fallback_chain + _resolve_provider_for_request tuple

**Files:**
- Modify: `apps/studio_api/routes/illustrations.py:44-66` (GenerateRequest)
- Modify: `apps/studio_api/routes/illustrations.py:112-135` (_resolve_provider_for_request)
- Modify: `apps/studio_api/routes/illustrations.py:35-41` (STAGE_HTTP_CODES mapping)

- [ ] **Step 1: Write failing route test for GenerateRequest.fallback_chain**

Add to `apps/studio_api/tests/test_illustrations_api.py`:

```python
"""Phase 101: GenerateRequest.fallback_chain + route integration."""
from __future__ import annotations

import pytest


def test_generate_request_accepts_fallback_chain():
    """Pydantic accepts fallback_chain as optional list[str]."""
    from apps.studio_api.routes.illustrations import GenerateRequest

    req = GenerateRequest(
        project_slug="test",
        type="cover",
        style_preset="preset",
        fallback_chain=["openai", "stability"],
    )
    assert req.fallback_chain == ["openai", "stability"]


def test_generate_request_fallback_chain_defaults_none():
    """When not provided, fallback_chain is None (let pipeline resolve from settings)."""
    from apps.studio_api.routes.illustrations import GenerateRequest

    req = GenerateRequest(
        project_slug="test",
        type="cover",
        style_preset="preset",
    )
    assert req.fallback_chain is None


def test_resolve_provider_returns_tuple_with_fallback_chain(monkeypatch, tmp_path):
    """_resolve_provider_for_request returns (provider, fallback_chain)."""
    import yaml
    from apps.studio_api.routes import illustrations as illust_mod

    # Mock project_root_for to return tmp_path
    monkeypatch.setattr(
        "apps.studio_api.routes._project_helpers.project_root_for",
        lambda slug: tmp_path,
    )

    # Set up settings.yaml with fallback_chain
    (tmp_path / ".lingwen").mkdir()
    (tmp_path / ".lingwen" / "illustration_settings.yaml").write_text(
        yaml.safe_dump({
            "default_provider": "openai",
            "fallback_chain": ["stability", "minimax"],
        }),
        encoding="utf-8",
    )

    provider, fallback_chain = illust_mod._resolve_provider_for_request(
        "test-slug",
        body_provider=None,
        body_fallback_chain=None,
    )
    assert provider == "openai"
    assert fallback_chain == ["stability", "minimax"]


def test_resolve_provider_body_fallback_overrides_settings(monkeypatch, tmp_path):
    """body.fallback_chain > settings.fallback_chain."""
    import yaml
    from apps.studio_api.routes import illustrations as illust_mod

    monkeypatch.setattr(
        "apps.studio_api.routes._project_helpers.project_root_for",
        lambda slug: tmp_path,
    )

    (tmp_path / ".lingwen").mkdir()
    (tmp_path / ".lingwen" / "illustration_settings.yaml").write_text(
        yaml.safe_dump({
            "default_provider": "openai",
            "fallback_chain": ["stability"],
        }),
        encoding="utf-8",
    )

    provider, fallback_chain = illust_mod._resolve_provider_for_request(
        "test-slug",
        body_provider=None,
        body_fallback_chain=["minimax"],  # body override
    )
    assert provider == "openai"
    assert fallback_chain == ["minimax"]  # body wins


def test_resolve_provider_no_settings_returns_empty_chain(monkeypatch, tmp_path):
    """No settings.yaml + no body.fallback_chain → empty chain (no fallback)."""
    from apps.studio_api.routes import illustrations as illust_mod

    monkeypatch.setattr(
        "apps.studio_api.routes._project_helpers.project_root_for",
        lambda slug: tmp_path,
    )

    # No settings file
    provider, fallback_chain = illust_mod._resolve_provider_for_request(
        "test-slug",
        body_provider=None,
        body_fallback_chain=None,
    )
    assert provider == "minimax"  # default
    assert fallback_chain == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_illustrations_api.py -v -k "fallback_chain or resolve_provider_returns or resolve_provider_body or resolve_provider_no_settings"`
Expected: FAIL with `TypeError: unexpected keyword argument` or signature mismatch

- [ ] **Step 3: Add fallback_chain to GenerateRequest**

In `apps/studio_api/routes/illustrations.py`, modify GenerateRequest class (lines 47-65):

```python
class GenerateRequest(BaseModel):
    project_slug: str
    type: str = Field(pattern="^(cover|chapter)$")
    chapter_num: Optional[int] = None
    style_preset: str
    custom_prompt: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    use_project_reference: bool = True
    fallback_chain: Optional[list[str]] = None    # NEW (Phase 101). None → resolve from settings.

    @model_validator(mode="after")
    def _chapter_requires_num(self) -> "GenerateRequest":
        if self.type == "chapter" and self.chapter_num is None:
            raise ValueError("chapter_num required when type='chapter'")
        return self
```

- [ ] **Step 4: Modify _resolve_provider_for_request to return tuple**

Replace `_resolve_provider_for_request` (lines 112-135) with:

```python
def _resolve_provider_for_request(
    req_project_slug: str,
    body_provider: Optional[str],
    body_fallback_chain: Optional[list[str]],
) -> tuple[str, list[str]]:
    """Phase 101: return (provider, fallback_chain).

    Priority:
        provider: body > settings.default_provider > 'minimax'
        fallback_chain: body > settings.fallback_chain > []

    If body_provider is provided but not in KNOWN_PROVIDERS, raise HTTPException(400).
    If project settings cannot be loaded, fall back to 'minimax' + [].
    """
    from lingwen_illustrations.providers import KNOWN_PROVIDERS

    from apps.studio_api.routes.project_settings import ProjectSettings, _load_settings

    if body_provider is not None:
        if body_provider not in KNOWN_PROVIDERS:
            raise HTTPException(
                status_code=400,
                detail=f"unknown provider '{body_provider}', expected one of {KNOWN_PROVIDERS}",
            )
        # body.provider wins; body.fallback_chain wins over settings.
        try:
            root = project_root_for(req_project_slug)
            settings = _load_settings(root)
        except LoadError:
            settings = ProjectSettings()
        fallback_chain = list(body_fallback_chain if body_fallback_chain is not None
                              else settings.fallback_chain)
        return body_provider, fallback_chain

    # No body.provider; use settings (or defaults).
    try:
        root = project_root_for(req_project_slug)
        settings = _load_settings(root)
    except LoadError:
        return "minimax", []
    return settings.default_provider, list(settings.fallback_chain)
```

Note: This signature is breaking for existing callers, but the only caller is the generate route within the same file (Task 7 Step 5 updates it). The regenerate route has its own resolution (uses existing_meta.provider); it only needs `body.fallback_chain` threaded through.

- [ ] **Step 5: Update generate route to use new signature**

In `apps/studio_api/routes/illustrations.py`, modify `generate_illustration` route (around lines 211-247):

Replace (lines 216):
```python
        provider = _resolve_provider_for_request(req.project_slug, req.provider)
        api_key, api_host = _api_credentials_for(provider)
```

With:
```python
        provider, fallback_chain = _resolve_provider_for_request(
            req.project_slug, req.provider, req.fallback_chain,
        )
        api_key, api_host = _api_credentials_for(provider)
```

In the `run_pipeline` call (around line 233-245), add `fallback_chain=fallback_chain`:

```python
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
            model=req.model,
            reference_image_bytes=reference_image_bytes,
            fallback_chain=fallback_chain,  # NEW (Phase 101)
        )
```

- [ ] **Step 6: Update regenerate route to thread fallback_chain**

In the `regenerate_illustration` route signature (around line 313-319), add:

```python
    ) -> GenerateResponse:
        ...
        try:
            new_meta = await run_regen(
                project_root=project_root,
                existing_meta=meta,
                api_key=api_key,
                api_host=api_host,
                provider=provider,  # None → pipeline reads existing_meta.provider
                model=model,
                fallback_chain=req.fallback_chain,  # NEW (Phase 101) — wait, req is not available here
            )
```

Note: The regenerate endpoint takes `fallback_chain` as a Query param, not in body. Update the function signature:

```python
    async def regenerate_illustration(
        asset_id: str,
        project_slug: str = Query(...),
        provider: Optional[str] = Query(None),
        model: Optional[str] = Query(None),
        fallback_chain: Optional[list[str]] = Query(None),  # NEW (Phase 101)
    ) -> GenerateResponse:
```

Note: FastAPI doesn't natively support list[str] Query without parsing. Use:

```python
        fallback_chain_raw: Optional[list[str]] = Query(None),  # comma-separated or repeated
```

Then parse:
```python
        # FastAPI accepts fallback_chain as repeated query param (?fallback_chain=a&fallback_chain=b)
        # or as single comma-separated string. Handle both:
        if isinstance(fallback_chain_raw, str):
            fallback_chain = [s.strip() for s in fallback_chain_raw.split(",") if s.strip()]
        else:
            fallback_chain = fallback_chain_raw
```

Add the parameter to the run_regen call:
```python
            new_meta = await run_regen(
                project_root=project_root,
                existing_meta=meta,
                api_key=api_key,
                api_host=api_host,
                provider=provider,
                model=model,
                fallback_chain=fallback_chain,  # NEW (Phase 101)
            )
```

- [ ] **Step 7: Run route tests to verify pass**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_illustrations_api.py -v`
Expected: All tests pass

- [ ] **Step 8: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/studio_api/routes/illustrations.py apps/studio_api/tests/test_illustrations_api.py
git commit -m "feat(phase-101): route layer — fallback_chain in GenerateRequest/RegenerateRequest + resolve tuple"
```

---

## Task 8: STAGE_HTTP_CODES mapping for ProviderExhaustedError

**Files:**
- Modify: `apps/studio_api/routes/illustrations.py:35-41`
- Modify: `apps/studio_api/routes/illustrations.py:138-151` (_err_detail, _raise_stage_error)

- [ ] **Step 1: Write failing route test for ProviderExhaustedError → 502**

Add to `apps/studio_api/tests/test_illustrations_api.py`:

```python
def test_provider_exhausted_maps_to_502_with_attempts_detail():
    """ProviderExhaustedError → 502 with detail.attempts."""
    from apps.studio_api.routes.illustrations import (
        ProviderExhaustedError,  # re-export from lingwen_illustrations.exceptions
        STAGE_HTTP_CODES,
    )
    from lingwen_illustrations.exceptions import ProviderExhaustedError as RealExhausted

    # STAGE_HTTP_CODES should have an entry for ProviderExhaustedError
    assert ProviderExhaustedError in STAGE_HTTP_CODES
    assert STAGE_HTTP_CODES[ProviderExhaustedError] == 502

    # Same class as the source (re-exported or aliased)
    assert ProviderExhaustedError is RealExhausted


def test_err_detail_provider_exhausted_includes_attempts():
    """When _err_detail sees ProviderExhaustedError, payload includes attempts."""
    from apps.studio_api.routes.illustrations import _err_detail
    from lingwen_illustrations.exceptions import ProviderExhaustedError

    err = ProviderExhaustedError(
        "all 2 providers failed",
        attempts=[
            {"provider": "openai", "model": "dall-e-3", "error": "GenerateError: 502", "ts": "2026-09-18T10:30:00Z"},
            {"provider": "stability", "model": "sd3", "error": None, "ts": "2026-09-18T10:30:03Z"},
        ],
        provider="stability",
    )
    payload = _err_detail(err)
    assert payload["stage"] == "generate"
    assert payload["retryable"] is False
    assert payload["provider"] == "stability"
    assert "attempts" in payload
    assert len(payload["attempts"]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_illustrations_api.py -v -k "provider_exhausted or err_detail_provider"`
Expected: FAIL with `KeyError: ProviderExhaustedError` or `ImportError`

- [ ] **Step 3: Update imports and STAGE_HTTP_CODES**

In `apps/studio_api/routes/illustrations.py`:

Update imports (lines 20-28):

```python
from lingwen_illustrations.exceptions import (
    ComposeError,
    ExtractError,
    GenerateError,
    IllustrationError,
    LoadError,
    ProviderExhaustedError,  # NEW (Phase 101)
    StoreError,
    UnknownModelError,
)
```

Update STAGE_HTTP_CODES (lines 35-41):

```python
STAGE_HTTP_CODES: dict[type[IllustrationError], int] = {
    LoadError: 404,
    ExtractError: 502,
    ComposeError: 400,
    GenerateError: 502,
    ProviderExhaustedError: 502,  # NEW (Phase 101): terminal fallback exhaustion
    StoreError: 500,
}
```

Update `_err_detail` (lines 138-145):

```python
def _err_detail(exc: IllustrationError) -> dict:
    """Build the standard error detail payload.

    Phase 101: ProviderExhaustedError includes attempts list in payload.
    """
    payload = {"stage": exc.stage.value, "error": exc.message, "retryable": exc.retryable}
    if isinstance(exc, GenerateError):
        if exc.retry_after is not None:
            payload["retry_after"] = exc.retry_after
        payload["provider"] = exc.provider
    if isinstance(exc, ProviderExhaustedError):
        payload["provider"] = exc.provider
        payload["attempts"] = exc.attempts  # NEW (Phase 101)
    return payload
```

- [ ] **Step 4: Run route tests to verify pass**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_illustrations_api.py -v`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/studio_api/routes/illustrations.py apps/studio_api/tests/test_illustrations_api.py
git commit -m "feat(phase-101): route STAGE_HTTP_CODES mapping for ProviderExhaustedError + detail.attempts"
```

---

## Task 9: Frontend api/illustrations.ts — fallback_chain param

**Files:**
- Modify: `apps/dashboard/src/api/illustrations.ts`

- [ ] **Step 1: Read current api/illustrations.ts to understand structure**

Run: `cat apps/dashboard/src/api/illustrations.ts`

Expected: shows `fetchGenerateIllustration` and `fetchRegenerateIllustration` typed wrappers, with `model?: string` param (Phase 100).

- [ ] **Step 2: Write failing type test for fallback_chain param**

Add to `apps/dashboard/src/api/__tests__/illustrations.spec.ts` (or create if not exists):

```typescript
import { describe, expectTypeOf, it } from 'vitest';
import type { GenerateRequest, RegenerateRequest } from '@/api/illustrations';

describe('illustrations api types — Phase 101 fallback_chain', () => {
  it('GenerateRequest accepts fallback_chain', () => {
    expectTypeOf<GenerateRequest['fallback_chain']>().toEqualTypeOf<string[] | undefined>();
  });

  it('RegenerateRequest accepts fallback_chain', () => {
    expectTypeOf<RegenerateRequest['fallback_chain']>().toEqualTypeOf<string[] | undefined>();
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd apps/dashboard && pnpm vitest run api/__tests__/illustrations.spec.ts`
Expected: FAIL with type error on `fallback_chain`

- [ ] **Step 4: Add fallback_chain to api/illustrations.ts**

In `apps/dashboard/src/api/illustrations.ts`:

For `GenerateRequest` interface (and equivalent for `RegenerateRequest`):

```typescript
export interface GenerateRequest {
  project_slug: string;
  type: 'cover' | 'chapter';
  chapter_num?: number;
  style_preset: string;
  custom_prompt?: string;
  provider?: string;
  model?: string;
  use_project_reference?: boolean;
  fallback_chain?: string[];  // NEW (Phase 101)
}
```

For `RegenerateRequest` interface:

```typescript
export interface RegenerateRequest {
  provider?: string;
  model?: string;
  fallback_chain?: string[];  // NEW (Phase 101)
}
```

Update `fetchGenerateIllustration` signature to accept and pass `fallback_chain`:

```typescript
export async function fetchGenerateIllustration(
  payload: GenerateRequest,
  options?: { referenceImage?: Blob },
): Promise<GenerateResponse> {
  // ... existing logic ...
  if (options?.referenceImage) {
    // multipart path: include fallback_chain in form fields
    form.append('fallback_chain', JSON.stringify(payload.fallback_chain ?? []));
  } else {
    // JSON path: include fallback_chain in body
    jsonBody.fallback_chain = payload.fallback_chain;
  }
  // ...
}
```

Update `fetchRegenerateIllustration` signature:

```typescript
export async function fetchRegenerateIllustration(
  projectSlug: string,
  assetId: string,
  options?: {
    provider?: string;
    model?: string;
    fallback_chain?: string[];  // NEW (Phase 101)
  },
): Promise<GenerateResponse> {
  const params = new URLSearchParams();
  if (options?.provider) params.set('provider', options.provider);
  if (options?.model) params.set('model', options.model);
  if (options?.fallback_chain) {
    // FastAPI accepts repeated query param for list
    for (const provider of options.fallback_chain) {
      params.append('fallback_chain', provider);
    }
  }
  // ...
}
```

- [ ] **Step 5: Run test to verify pass**

Run: `cd apps/dashboard && pnpm vitest run api/__tests__/illustrations.spec.ts`
Expected: PASS

- [ ] **Step 6: Type check**

Run: `cd apps/dashboard && pnpm tsc --noEmit`
Expected: 0 new errors (pre-existing 48 baseline unchanged)

- [ ] **Step 7: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/api/illustrations.ts apps/dashboard/src/api/__tests__/illustrations.spec.ts
git commit -m "feat(phase-101): api/illustrations.ts — fallback_chain param threading"
```

---

## Task 10: useProjectSettings store — fallback_chain field

**Files:**
- Modify: `apps/dashboard/src/stores/useProjectSettings.js`

- [ ] **Step 1: Read current store**

Run: `cat apps/dashboard/src/stores/useProjectSettings.js`

Expected: shows Pinia store with `default_provider`, `default_models`, `auto_generate`, `max_assets`, `confirm_before_generate` fields.

- [ ] **Step 2: Write failing test for store fallback_chain**

Add to `apps/dashboard/src/stores/__tests__/useProjectSettings.spec.js` (create if not exists):

```javascript
import { describe, it, expect, beforeEach } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useProjectSettingsStore } from '@/stores/useProjectSettings';

describe('useProjectSettings store — Phase 101 fallback_chain', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('initializes fallback_chain as empty array', () => {
    const store = useProjectSettingsStore();
    expect(store.settings.fallback_chain).toEqual([]);
  });

  it('preserves fallback_chain when updating', async () => {
    const store = useProjectSettingsStore();
    store.settings = {
      default_provider: 'openai',
      fallback_chain: ['stability', 'minimax'],
    };
    await store.update({
      default_provider: 'openai',
      fallback_chain: ['stability', 'minimax'],
    });
    expect(store.settings.fallback_chain).toEqual(['stability', 'minimax']);
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd apps/dashboard && pnpm vitest run stores/__tests__/useProjectSettings.spec.js`
Expected: FAIL (fallback_chain undefined)

- [ ] **Step 4: Add fallback_chain to store**

In `apps/dashboard/src/stores/useProjectSettings.js`, in the state initialization:

```javascript
state: () => ({
  settings: {
    default_provider: 'minimax',
    default_models: {},
    auto_generate: false,
    max_assets: 20,
    confirm_before_generate: false,
    fallback_chain: [],  // NEW (Phase 101)
  },
  // ...
}),
```

Update the `update` action to send and receive `fallback_chain` (it should already flow through if the action does `...settings` spread).

- [ ] **Step 5: Run test to verify pass**

Run: `cd apps/dashboard && pnpm vitest run stores/__tests__/useProjectSettings.spec.js`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/stores/useProjectSettings.js apps/dashboard/src/stores/__tests__/useProjectSettings.spec.js
git commit -m "feat(phase-101): useProjectSettings store — fallback_chain field"
```

---

## Task 11: ProjectSettingsIllustration.vue — multi-select picker

**Files:**
- Modify: `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue`

- [ ] **Step 1: Read current component**

Run: `cat apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue`

Expected: shows existing provider dropdown + per-provider model dropdowns (Phase 100).

- [ ] **Step 2: Write failing component test**

Add to `apps/dashboard/src/components/illustrations/__tests__/ProjectSettingsIllustration.spec.ts`:

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import ProjectSettingsIllustration from '@/components/illustrations/ProjectSettingsIllustration.vue';

describe('ProjectSettingsIllustration — Phase 101 fallback_chain', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('renders fallback_chain multi-select with known providers', () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: { projectSlug: 'test' },
    });
    // Should have a multi-select element for fallback_chain
    const multiSelect = wrapper.find('[data-testid="fallback-chain-select"]');
    expect(multiSelect.exists()).toBe(true);
  });

  it('persists fallback_chain to settings update', async () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: { projectSlug: 'test' },
    });
    // Find the multi-select and update it
    const multiSelect = wrapper.find('[data-testid="fallback-chain-select"]');
    await multiSelect.setValue(['stability', 'minimax']);
    // Trigger update (depends on component structure — may need .trigger('update:modelValue'))
    // Verify store is updated
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd apps/dashboard && pnpm vitest run components/illustrations/__tests__/ProjectSettingsIllustration.spec.ts`
Expected: FAIL (data-testid not found)

- [ ] **Step 4: Add multi-select picker to component**

In `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue`, after the existing per-provider model dropdowns, add:

```vue
<n-form-item label="Fallback Chain" data-testid="fallback-chain-form-item">
  <n-select
    v-model:value="settings.fallback_chain"
    multiple
    :options="KNOWN_PROVIDERS.map(p => ({ label: p, value: p }))"
    placeholder="(no fallback — primary only)"
    data-testid="fallback-chain-select"
  />
  <template #feedback>
    <n-text depth="3" style="font-size: 12px;">
      If the primary provider fails with a transient error (5xx, timeout, rate limit),
      the pipeline will try these providers in order.
    </n-text>
  </template>
</n-form-item>
```

Add to component's `<script setup>`:
```typescript
import { KNOWN_PROVIDERS } from '@/api/illustrations'; // or define locally
```

Define `settings` ref bound to the store:
```typescript
const settingsStore = useProjectSettingsStore();
const settings = computed({
  get: () => settingsStore.settings,
  set: (val) => { settingsStore.settings = { ...settingsStore.settings, ...val }; },
});
```

Note: exact bindings depend on existing component structure; adjust as needed to match Phase 100 pattern.

- [ ] **Step 5: Run test to verify pass**

Run: `cd apps/dashboard && pnpm vitest run components/illustrations/__tests__/ProjectSettingsIllustration.spec.ts`
Expected: PASS

- [ ] **Step 6: Type check + lint**

Run: `cd apps/dashboard && pnpm tsc --noEmit && pnpm eslint components/illustrations/ProjectSettingsIllustration.vue`
Expected: 0 errors / 0 lint warnings (or pre-existing)

- [ ] **Step 7: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue apps/dashboard/src/components/illustrations/__tests__/ProjectSettingsIllustration.spec.ts
git commit -m "feat(phase-101): ProjectSettingsIllustration — fallback_chain multi-select picker"
```

---

## Task 12: I093 invariant + architecture.yml

**Files:**
- Modify: `.lingwen/architecture.yml`

- [ ] **Step 1: Read current architecture.yml invariants section**

Run: `grep -n "I092\|I093" .lingwen/architecture.yml`

Expected: I092 invariant from Phase 100 (multi-model per provider). I093 not yet present.

- [ ] **Step 2: Write failing test for I093 invariant**

Create `tests/test_phase101_atomic_provider_fallback.py` (regression guards will all be in this file, but only G7 for now):

```python
"""Phase 101: I093 invariant — fallback chain is fallback module's only entry."""
from __future__ import annotations

import pytest
import yaml


@pytest.fixture
def architecture_yml() -> dict:
    with open(".lingwen/architecture.yml") as f:
        return yaml.safe_load(f)


def test_i093_invariant_exists(architecture_yml: dict):
    """I093 NEW: fallback chain dispatch invariants in architecture.yml."""
    invariants = architecture_yml.get("invariants", {})
    assert "I093" in invariants, "I093 invariant missing"


def test_i093_describes_fallback_dispatch_entry_point(architecture_yml: dict):
    """I093 must mention dispatch_with_fallback as the only entry point."""
    i093 = architecture_yml["invariants"]["I093"]
    rule = i093.get("rule", "")
    assert "dispatch_with_fallback" in rule
    assert "fallback.py" in rule or "lingwen_illustrations.fallback" in rule


def test_i093_severity_is_error(architecture_yml: dict):
    """Phase invariants are enforcement-level (severity=error)."""
    i093 = architecture_yml["invariants"]["I093"]
    assert i093.get("severity") == "error"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/test_phase101_atomic_provider_fallback.py -v`
Expected: FAIL with `KeyError: 'I093'`

- [ ] **Step 4: Add I093 to architecture.yml**

In `.lingwen/architecture.yml`, find the invariants section (after I092 from Phase 100), add:

```yaml
    I093: |
      packages/lingwen-illustrations/src/lingwen_illustrations/fallback.py:dispatch_with_fallback
      is the only entry point for cross-provider fallback iteration in REQ-002
      illustration generation. pipeline.generate_illustration and
      pipeline.regenerate_illustration text-only paths call this helper; i2i
      paths bypass it (provider-specific i2i models are not interchangeable).
      Attempt is the only attempt-tracking dataclass. ProviderExhaustedError
      is the only terminal exhaustion exception. infra.fallback.* and
      infra.image_provider.* paths are illegal (Phase 101 REQ-002 v2 #6).
    severity: error
```

- [ ] **Step 5: Run test to verify pass**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/test_phase101_atomic_provider_fallback.py -v`
Expected: 3 PASS

- [ ] **Step 6: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add .lingwen/architecture.yml tests/test_phase101_atomic_provider_fallback.py
git commit -m "feat(phase-101): I093 invariant + 3 architecture guards"
```

---

## Task 13: 10 regression guards G1-G10

**Files:**
- Modify: `tests/test_phase101_atomic_provider_fallback.py` (add G1-G6, G8-G10; G7 already added in Task 12)

- [ ] **Step 1: Write G1-G6, G8-G10 tests**

Add the following tests to `tests/test_phase101_atomic_provider_fallback.py`:

```python
"""Phase 101: 10 regression guards for Atomic Provider Fallback."""
from __future__ import annotations

import re
import yaml
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


# ---- G1: settings.yaml fallback_chain default ----

def test_g1_settings_yaml_fallback_chain_default():
    """ProjectSettings.fallback_chain defaults to []."""
    from apps.studio_api.routes.project_settings import ProjectSettings
    s = ProjectSettings()
    assert s.fallback_chain == []


# ---- G2: GenerateRequest has fallback_chain field ----

def test_g2_generate_request_has_fallback_chain():
    """GenerateRequest must have fallback_chain optional field."""
    from apps.studio_api.routes.illustrations import GenerateRequest
    fields = GenerateRequest.model_fields.keys()
    assert "fallback_chain" in fields
    # Field is Optional[list[str]]
    field_info = GenerateRequest.model_fields["fallback_chain"]
    assert field_info.default is None


# ---- G3: pipeline.generate_illustration uses fallback ----

def test_g3_pipeline_generate_uses_fallback():
    """pipeline.generate_illustration must call dispatch_with_fallback."""
    pipeline_src = (ROOT / "packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py").read_text()
    assert "dispatch_with_fallback" in pipeline_src
    # In generate_illustration function
    gen_section = pipeline_src.split("async def generate_illustration")[1].split("async def regenerate_illustration")[0]
    assert "dispatch_with_fallback" in gen_section


# ---- G4: pipeline.regenerate_illustration uses fallback ----

def test_g4_pipeline_regenerate_uses_fallback():
    """pipeline.regenerate_illustration must call dispatch_with_fallback."""
    pipeline_src = (ROOT / "packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py").read_text()
    regen_section = pipeline_src.split("async def regenerate_illustration")[1]
    assert "dispatch_with_fallback" in regen_section


# ---- G5: ProviderExhaustedError exists in fallback module ----

def test_g5_provider_exhausted_error_in_exceptions():
    """ProviderExhaustedError must be importable from lingwen_illustrations.exceptions."""
    from lingwen_illustrations.exceptions import ProviderExhaustedError
    assert issubclass(ProviderExhaustedError, Exception)
    # Carries attempts attribute
    err = ProviderExhaustedError(
        "test",
        attempts=[{"provider": "a", "model": "b", "error": "c", "ts": "d"}],
        provider="a",
    )
    assert hasattr(err, "attempts")
    assert len(err.attempts) == 1


# ---- G6: audit_log.record_event receives attempts in extra ----

def test_g6_audit_extra_includes_attempts():
    """pipeline.generate_illustration record_event call must include attempts in extra."""
    pipeline_src = (ROOT / "packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py").read_text()
    gen_section = pipeline_src.split("async def generate_illustration")[1].split("async def regenerate_illustration")[0]
    # Look for the record_event call block
    assert re.search(r'attempts.*=.*\[.*__dict__', gen_section, re.DOTALL), \
        "record_event extra must include attempts list"


# ---- G8: Phase 100 G1-G9 guards preserved (no regression) ----

def test_g8_phase_100_guards_present():
    """Phase 100 regression guard file must still exist."""
    phase100_guard = ROOT / "tests" / "test_phase100_multi_model.py"
    assert phase100_guard.exists(), "Phase 100 guard file missing"


def test_g8b_phase_100_i092_invariant_present():
    """Phase 100 I092 invariant must still be in architecture.yml."""
    with open(".lingwen/architecture.yml") as f:
        arch = yaml.safe_load(f)
    assert "I092" in arch.get("invariants", {})


# ---- G9: i2i path does NOT enter fallback ----

def test_g9_i2i_path_does_not_call_fallback():
    """In pipeline.generate_illustration, the i2i branch (reference_image_bytes) must not call dispatch_with_fallback."""
    pipeline_src = (ROOT / "packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py").read_text()
    gen_section = pipeline_src.split("async def generate_illustration")[1].split("async def regenerate_illustration")[0]
    # The i2i if-block should contain generate_with_reference but NOT dispatch_with_fallback
    i2i_block_match = re.search(
        r'if reference_image_bytes is not None:.*?(?=\n    else:)',
        gen_section, re.DOTALL,
    )
    assert i2i_block_match is not None, "i2i branch not found in generate_illustration"
    i2i_block = i2i_block_match.group(0)
    assert "generate_with_reference" in i2i_block
    assert "dispatch_with_fallback" not in i2i_block, \
        "i2i branch must NOT use dispatch_with_fallback (provider-specific models)"


# ---- G10: route maps ProviderExhaustedError → 502 ----

def test_g10_route_maps_provider_exhausted_to_502():
    """STAGE_HTTP_CODES must have ProviderExhaustedError → 502."""
    from apps.studio_api.routes.illustrations import STAGE_HTTP_CODES
    from lingwen_illustrations.exceptions import ProviderExhaustedError
    assert STAGE_HTTP_CODES.get(ProviderExhaustedError) == 502
```

- [ ] **Step 2: Run all 13 guards**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/test_phase101_atomic_provider_fallback.py -v`
Expected: 13 PASS (3 from Task 12 + 10 new)

- [ ] **Step 3: Run full backend test suite to verify no regression**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/ packages/lingwen-illustrations/tests/ tests/test_phase100_multi_model.py -v`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add tests/test_phase101_atomic_provider_fallback.py
git commit -m "test(phase-101): 10 regression guards G1-G10 + I093 invariant"
```

---

## Task 14: doc sync — CLAUDE.md v58.0 → v59.0 + handoff

**Files:**
- Create: `docs/superpowers/handoffs/2026-09-18-phase-101-atomic-provider-fallback-handoff.md`
- Modify: `CLAUDE.md` (version line + I093 invariant entry)
- Modify: `collaboration/BACKLOG.md` (REQ-002 v2 status row)
- Modify: `collaboration/CURRENT_STATUS.md` (Phase 101 row)

- [ ] **Step 1: Create handoff doc**

Create `docs/superpowers/handoffs/2026-09-18-phase-101-atomic-provider-fallback-handoff.md` following the Phase 100 handoff template:

```markdown
# Phase 101 — Atomic Provider Fallback — Handoff

> **Date**: 2026-09-18
> **Phase**: v58.0 → v59.0
> **Cluster**: REQ-002 v2 #6 (sixth sub-project delivered; 1/7 remaining)

## Summary

[2-3 paragraph summary of what was delivered]

## Validation gates

| Gate | Result |
|------|--------|
| Backend pytest | lingwen-illustrations .../... + studio_api .../... |
| Phase 101 guards | 13/13 PASS |
| vitest | ... |
| pnpm tsc | 0 new errors |
| ruff | clean |

## Sub-projects delivered

- New `lingwen_illustrations.fallback` module
- ProviderExhaustedError exception
- Attempt dataclass
- dispatch_with_fallback async fn
- ProjectSettings.fallback_chain field
- GenerateRequest.fallback_chain optional override
- RegenerateRequest fallback_chain query param
- Route _resolve_provider_for_request returns tuple
- STAGE_HTTP_CODES mapping for ProviderExhaustedError → 502
- Frontend api/illustrations.ts wrapper updates
- useProjectSettings store fallback_chain field
- ProjectSettingsIllustration multi-select picker
- I093 NEW invariant

## Commits

| SHA | Task | Description |
|-----|------|-------------|
| `TBD` | T1 | ProviderExhaustedError + 2 tests |
| ... | ... | ... |

## Lessons learned

[5-7 bullet points]

## Future work

- REQ-002 v2 #7: v2 settings persistence extension
- REQ-004: 团队协作 brainstorm
```

Fill in actual SHAs from `git log --oneline -14` after Tasks 1-13 are complete.

- [ ] **Step 2: Update CLAUDE.md version line + I093 entry**

In `CLAUDE.md` line 1 (version), change v58.0 → v59.0 and add Phase 101 description.

In the I001-I092 invariants section, add I093 entry matching the one in architecture.yml.

- [ ] **Step 3: Update BACKLOG.md**

In `collaboration/BACKLOG.md`, find the "REQ-002 v2 remaining" row and update: 1 of 7 remaining (atomic provider fallback done, v2 settings persistence extension remaining).

- [ ] **Step 4: Update CURRENT_STATUS.md**

In `collaboration/CURRENT_STATUS.md`, add a Phase 101 row in the "已完成" section summarizing what was delivered.

- [ ] **Step 5: Run all tests + quality gates one final time**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-illustrations/tests/ apps/studio_api/tests/ tests/test_phase101_atomic_provider_fallback.py tests/test_phase100_multi_model.py -v
cd apps/dashboard && pnpm vitest run
cd apps/dashboard && pnpm tsc --noEmit
cd apps/dashboard && pnpm exec knip
```

Expected: All pass.

- [ ] **Step 6: Push to origin**

```bash
cd /home/ailearn/projects/LingWen
git push origin master
```

- [ ] **Step 7: Commit doc sync**

```bash
cd /home/ailearn/projects/LingWen
git add CLAUDE.md collaboration/BACKLOG.md collaboration/CURRENT_STATUS.md docs/superpowers/handoffs/2026-09-18-phase-101-atomic-provider-fallback-handoff.md
git commit -m "docs(phase-101): CLAUDE.md v58.0 -> v59.0 + I093 + handoff + sync"
```

---

## Self-review

After all 14 tasks are complete, run the self-review checklist:

**1. Spec coverage:**
- New `fallback.py` module → Tasks 2, 3 ✓
- `ProviderExhaustedError` → Task 1 ✓
- Pipeline integration (generate + regenerate) → Tasks 4, 5 ✓
- ProjectSettings extension → Task 6 ✓
- GenerateRequest/RegenerateRequest override → Task 7 ✓
- Route STAGE_HTTP_CODES mapping → Task 8 ✓
- Frontend api/illustrations.ts → Task 9 ✓
- useProjectSettings store → Task 10 ✓
- ProjectSettingsIllustration picker → Task 11 ✓
- I093 invariant + architecture.yml → Task 12 ✓
- 10 regression guards → Task 13 ✓
- Doc sync → Task 14 ✓

**2. Placeholder scan:** No TBD/TODO/"implement later" in plan.

**3. Type consistency:**
- `Attempt(provider, model, error, ts)` consistent across all tasks ✓
- `dispatch_with_fallback(...)` signature consistent ✓
- `ProviderExhaustedError(message, *, attempts, provider)` consistent ✓
- `ProjectSettings.fallback_chain: list[str] = []` consistent ✓
- `GenerateRequest.fallback_chain: Optional[list[str]] = None` consistent ✓

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-18-phase-101-atomic-provider-fallback.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — Dispatch a fresh subagent per task with two-stage review between tasks
2. **Inline Execution** — Execute tasks in this session with checkpoints

Which approach?
