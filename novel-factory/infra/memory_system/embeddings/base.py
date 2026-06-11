"""Embedding provider abstraction for Memory RAG (F89)."""
from __future__ import annotations

from typing import Literal, Protocol, runtime_checkable

EmbeddingPurpose = Literal["query", "document"]


class EmbeddingProviderError(RuntimeError):
    """Embedding backend initialization or API failure."""


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Text embedding backend used by MemoryGateway / Qdrant."""

    provider_name: str
    model: str
    dimension: int

    def embed_texts(
        self,
        texts: list[str],
        *,
        purpose: EmbeddingPurpose = "document",
    ) -> list[list[float]]:
        """Return one vector per input text, in order."""

    def health_check(self) -> tuple[bool, str]:
        """Lightweight probe (may call remote API when live)."""
