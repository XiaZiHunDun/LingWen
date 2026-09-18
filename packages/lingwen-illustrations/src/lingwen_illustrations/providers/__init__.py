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
from typing import Awaitable, Callable

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
