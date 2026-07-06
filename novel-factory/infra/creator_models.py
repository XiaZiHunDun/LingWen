"""Available LLM models for creator preferences UI."""
from __future__ import annotations

import os
from typing import Any

# Curated catalog; `available` reflects configured API keys when possible.
_CATALOG: list[dict[str, Any]] = [
    {"id": "minimax-abab6.5", "label": "MiniMax abab6.5", "provider": "minimax"},
    {"id": "MiniMax-M2.7", "label": "MiniMax M2.7", "provider": "minimax"},
    {"id": "claude-sonnet", "label": "Claude Sonnet", "provider": "anthropic"},
    {"id": "claude-3-5-sonnet-20241022", "label": "Claude 3.5 Sonnet", "provider": "anthropic"},
    {"id": "gpt-4o", "label": "GPT-4o", "provider": "openai"},
    {"id": "gpt-4o-mini", "label": "GPT-4o Mini", "provider": "openai"},
    {"id": "local-mock", "label": "本地 Mock（开发）", "provider": "mock"},
]

_PROVIDER_ENV = {
    "minimax": "MINIMAX_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "mock": None,
}


def _provider_available(provider: str) -> bool:
    if provider == "mock":
        return True
    env_var = _PROVIDER_ENV.get(provider)
    if not env_var:
        return False
    return bool(os.getenv(env_var, "").strip())


def list_creator_models() -> list[dict[str, Any]]:
    """Return model options with availability flags for the dashboard."""
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in _CATALOG:
        mid = row["id"]
        if mid in seen:
            continue
        seen.add(mid)
        provider = str(row["provider"])
        out.append(
            {
                "id": mid,
                "label": row["label"],
                "provider": provider,
                "available": _provider_available(provider),
            },
        )
    return out


def list_creator_models_payload() -> dict[str, Any]:
    models = list_creator_models()
    return {
        "models": models,
        "default_model": models[0]["id"] if models else "local-mock",
    }
