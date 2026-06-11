"""Embedding provider resolution and factory (F89)."""
from __future__ import annotations

import os
from typing import Any

from infra.memory_system.config import load_yaml
from infra.memory_system.embeddings.base import EmbeddingProvider, EmbeddingProviderError
from infra.memory_system.embeddings.minimax_provider import MiniMaxEmbeddingProvider
from infra.memory_system.embeddings.openai_provider import OpenAIEmbeddingProvider

MEMORY_CONFIG_PATH = "config/memory_config.yaml"
_VALID_PROVIDERS = frozenset({"auto", "openai", "minimax"})


def _embedding_section(config: dict[str, Any]) -> dict[str, Any]:
    section = config.get("embedding")
    if not isinstance(section, dict):
        raise EmbeddingProviderError(f"Missing embedding section in {MEMORY_CONFIG_PATH}")
    return section


def resolve_embedding_provider_name(
    config: dict[str, Any] | None = None,
) -> str:
    """Resolve provider name without instantiating backends."""
    env_override = os.environ.get("LINGWEN_EMBEDDING_PROVIDER", "").strip().lower()
    if env_override:
        if env_override not in _VALID_PROVIDERS - {"auto"}:
            raise EmbeddingProviderError(
                f"Invalid LINGWEN_EMBEDDING_PROVIDER={env_override!r} "
                f"(expected openai|minimax)"
            )
        return env_override

    section = _embedding_section(config or load_yaml(MEMORY_CONFIG_PATH))
    configured = str(section.get("provider", "auto")).strip().lower()
    if configured != "auto":
        if configured not in _VALID_PROVIDERS - {"auto"}:
            raise EmbeddingProviderError(
                f"Invalid embedding.provider={configured!r} in {MEMORY_CONFIG_PATH}"
            )
        return configured

    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("MINIMAX_API_KEY"):
        return "minimax"

    raise EmbeddingProviderError(
        "No embedding API key found. Set OPENAI_API_KEY or MINIMAX_API_KEY, "
        "or set LINGWEN_EMBEDDING_PROVIDER explicitly."
    )


def embedding_keys_available(provider_name: str) -> tuple[bool, str]:
    """Check env keys for a resolved provider (no network)."""
    if provider_name == "openai":
        if os.environ.get("OPENAI_API_KEY"):
            return True, "embedding: OPENAI_API_KEY set (provider=openai)"
        return False, "embedding: OPENAI_API_KEY required (provider=openai)"

    if provider_name == "minimax":
        if not os.environ.get("MINIMAX_API_KEY"):
            return False, "embedding: MINIMAX_API_KEY required (provider=minimax)"
        group = os.environ.get("MINIMAX_GROUP_ID", "")
        if group:
            return True, "embedding: MINIMAX_API_KEY + MINIMAX_GROUP_ID set (provider=minimax)"
        return True, (
            "embedding: MINIMAX_API_KEY set (provider=minimax; "
            "MINIMAX_GROUP_ID recommended for CN endpoint)"
        )

    return False, f"embedding: unknown provider {provider_name!r}"


def describe_embedding_requirements() -> tuple[bool, str]:
    """Resolve provider and verify keys are present (preflight helper)."""
    try:
        name = resolve_embedding_provider_name()
    except EmbeddingProviderError as exc:
        return False, str(exc)
    return embedding_keys_available(name)


def _model_for_provider(section: dict[str, Any], provider_name: str) -> str:
    nested = section.get(provider_name)
    if isinstance(nested, dict) and nested.get("model"):
        return str(nested["model"])
    legacy = section.get("model")
    if legacy:
        return str(legacy)
    if provider_name == "minimax":
        return "embo-01"
    return "text-embedding-3-small"


def create_embedding_provider(
    config: dict[str, Any] | None = None,
) -> EmbeddingProvider:
    """Build a live embedding provider from config + environment."""
    cfg = config or load_yaml(MEMORY_CONFIG_PATH)
    section = _embedding_section(cfg)
    provider_name = resolve_embedding_provider_name(cfg)
    dimension = int(section.get("dimension", 1536))
    model = _model_for_provider(section, provider_name)

    if provider_name == "openai":
        return OpenAIEmbeddingProvider(model=model, dimension=dimension)

    if provider_name == "minimax":
        minimax_cfg = section.get("minimax") if isinstance(section.get("minimax"), dict) else {}
        base_url = minimax_cfg.get("base_url")
        return MiniMaxEmbeddingProvider(
            model=model,
            dimension=dimension,
            base_url=str(base_url) if base_url else None,
        )

    raise EmbeddingProviderError(f"Unsupported embedding provider: {provider_name}")
