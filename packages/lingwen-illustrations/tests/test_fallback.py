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
