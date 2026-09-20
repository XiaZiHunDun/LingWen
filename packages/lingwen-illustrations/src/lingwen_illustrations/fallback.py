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
from typing import Callable

from lingwen_illustrations.exceptions import (
    GenerateError,
    ProviderExhaustedError,
)
from lingwen_illustrations.providers import KNOWN_PROVIDERS, UnknownProviderError, get_provider
# NOTE: resolve_model is imported inside dispatch_with_fallback to avoid circular import
# (pipeline.py imports dispatch_with_fallback; resolve_model is defined in pipeline.py)


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
    provider_factory: Callable[[str], object] | None = None,
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
    from lingwen_illustrations.pipeline import resolve_model  # lazy import to avoid cycle

    import logging
    logger = logging.getLogger(__name__)

    # Build deduped chain of valid providers. Empty chain = primary-only.
    valid_chain = _filter_known_providers(_dedupe_preserve_order(chain))
    if not valid_chain:
        raise UnknownProviderError(
            f"fallback chain empty after filtering: {chain}"
        )

    # Phase 101: allow caller to pass a provider_factory for testability
    # (so tests patching lingwen_illustrations.pipeline.get_provider take effect).
    # Default to module-level get_provider.
    _get_provider = provider_factory if provider_factory is not None else get_provider

    attempts: list[Attempt] = []

    for idx, provider in enumerate(valid_chain):
        adapter = _get_provider(provider)
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
