"""Legacy thin wrapper for backwards compat (Phase 96).

Phase 90-95 callers used `image_generator.generate(prompt, api_key, api_host)`.
Phase 96 redirects this to the MiniMax provider adapter via the registry.
New code should call `lingwen_illustrations.providers.get_provider(name).generate(...)`
directly, or use `pipeline.generate_illustration(..., provider=name)`.

Phase 93 b64_json real decode logic is now in providers/_b64_decode.py —
this module exists only for backwards compatibility with existing test mocks
that patch `lingwen_illustrations.image_generator.httpx.AsyncClient`.
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
    """Backwards-compatible wrapper. Delegates to MiniMax provider.

    Equivalent to:
        from lingwen_illustrations.providers import get_provider
        return await get_provider("minimax").generate(
            prompt=prompt, api_key=api_key, api_host=api_host, timeout=timeout
        )

    All Phase 93 behavior (b64_json decoding, error mapping) is preserved
    via the providers/minimax.py adapter.
    """
    fn = get_provider("minimax")
    return await fn(
        prompt=prompt, api_key=api_key, api_host=api_host, timeout=timeout
    )


__all__ = ["generate"]
