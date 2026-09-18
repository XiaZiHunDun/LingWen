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
