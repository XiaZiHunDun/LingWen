"""Image generation provider registry (Phase 96).

Exposes KNOWN_PROVIDERS tuple + get_provider(name) lookup function.
Each provider module (minimax/openai/stability) exports `generate(...)`
with uniform signature: `async def generate(*, prompt, api_key, api_host, timeout=60) -> bytes`.

`get_provider` does a dynamic lookup of the named module's `generate`
attribute, so callers that monkeypatch the module attribute
(e.g. `monkeypatch.setattr("lingwen_illustrations.providers.minimax.generate", fake)`)
get the patched function rather than the one captured at registry import time.
"""
import importlib
from typing import Any

from lingwen_illustrations.providers import minimax, openai, stability  # noqa: F401

KNOWN_PROVIDERS: tuple[str, ...] = ("minimax", "openai", "stability")
DEFAULT_PROVIDER: str = "minimax"


class UnknownProviderError(ValueError):
    """Raised when get_provider(name) gets a name not in KNOWN_PROVIDERS."""


def get_provider(name: str) -> Any:
    """Return the adapter generate() callable for the named provider.

    Args:
        name: Provider name (must be one of KNOWN_PROVIDERS).

    Returns:
        Async function with signature (*, prompt, api_key, api_host, timeout=60) -> bytes.

    Raises:
        UnknownProviderError: If name is not in KNOWN_PROVIDERS.

    Dynamic lookup: re-reads the provider module's `generate` attribute on
    each call. This lets tests monkeypatch the module attribute and have
    the change take effect on subsequent `get_provider(name)` calls —
    matching the established pattern in `test_image_generator.py`.
    """
    if name not in KNOWN_PROVIDERS:
        raise UnknownProviderError(
            f"unknown provider '{name}', expected one of {KNOWN_PROVIDERS}"
        )
    module = importlib.import_module(f"lingwen_illustrations.providers.{name}")
    return module.generate


__all__ = [
    "KNOWN_PROVIDERS",
    "DEFAULT_PROVIDER",
    "UnknownProviderError",
    "get_provider",
]
