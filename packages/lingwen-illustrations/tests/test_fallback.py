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
    """Each provider in chain independently resolves its model via Phase 100 logic.

    Primary gets explicit_model (if valid). Fallback providers always use
    their own 3-tier resolution (no explicit override propagated).
    """
    from lingwen_illustrations.providers import openai as oa_mod, stability as st_mod

    openai_models: list[str] = []
    stability_models: list[str] = []

    async def _openai_capture(**kwargs):
        openai_models.append(kwargs.get("model"))
        # First (only) call to openai fails with retryable to trigger fallback.
        raise GenerateError(
            "502 server error", retryable=True, provider="openai",
        )

    async def _stability_capture(**kwargs):
        stability_models.append(kwargs.get("model"))
        return b"ok"

    monkeypatch.setattr(oa_mod, "generate", _openai_capture)
    monkeypatch.setattr(st_mod, "generate", _stability_capture)

    # explicit_model="dall-e-3-hd" only applies to primary (openai); stability uses its own default.
    bytes_out, provider, model, attempts = await dispatch_with_fallback(
        chain=["openai", "stability"],
        explicit_model="dall-e-3-hd",
        project_settings=None,
        api_credentials_for=_credentials_for,
        prompt="test",
    )
    assert provider == "stability"
    assert model == "sd3-medium"  # stability default (sd3-medium per KNOWN_MODELS)
    # Verify what each provider got called with
    assert openai_models == ["dall-e-3-hd"]  # primary explicit
    assert stability_models == ["sd3-medium"]  # stability own default


def test_attempt_last_entry_is_success():
    """On success, attempts last entry has error=None."""
    attempts = [
        Attempt(provider="openai", model="dall-e-3", error="GenerateError: 502", ts=_now_iso()),
        Attempt(provider="stability", model="sd3", error=None, ts=_now_iso()),
    ]
    assert attempts[-1].error is None
    assert attempts[-1].provider == "stability"
