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
