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
