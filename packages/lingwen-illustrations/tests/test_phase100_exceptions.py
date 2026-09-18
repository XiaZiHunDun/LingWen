"""Phase 100: UnknownModelError exception class tests.

Validates the new exception raised when explicit model is not in
provider's KNOWN_MODELS catalog.
"""
from __future__ import annotations


def test_unknown_model_error_is_value_error():
    """UnknownModelError must subclass ValueError so routes/illustrations.py can map it to HTTP 422 (Phase 100 spec §3)."""
    from lingwen_illustrations.exceptions import UnknownModelError

    err = UnknownModelError("openai", "gpt-image-9", ("dall-e-3", "dall-e-2"))
    assert isinstance(err, ValueError)


def test_unknown_model_error_carries_provider_model_known():
    """Exception must expose provider/model/known attributes for debugging."""
    from lingwen_illustrations.exceptions import UnknownModelError

    err = UnknownModelError(
        provider="stability",
        model="sd99-bogus",
        known=("sd3-medium", "sd3-large"),
    )
    assert err.provider == "stability"
    assert err.model == "sd99-bogus"
    assert err.known == ("sd3-medium", "sd3-large")


def test_unknown_model_error_message_lists_known_models():
    """Error message must include the provider name + invalid model + valid options."""
    from lingwen_illustrations.exceptions import UnknownModelError

    err = UnknownModelError("openai", "dall-e-99", ("dall-e-3", "gpt-image-1"))
    msg = str(err)
    assert "openai" in msg
    assert "dall-e-99" in msg
    assert "dall-e-3" in msg
    assert "gpt-image-1" in msg
