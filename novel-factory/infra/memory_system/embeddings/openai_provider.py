"""OpenAI embeddings provider (default / backward compatible)."""
from __future__ import annotations

import os

from openai import OpenAI

from infra.memory_system.embeddings.base import EmbeddingPurpose, EmbeddingProviderError


class OpenAIEmbeddingProvider:
    """OpenAI ``embeddings.create`` backend."""

    provider_name = "openai"

    def __init__(self, *, model: str, dimension: int, api_key: str | None = None):
        key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not key:
            raise EmbeddingProviderError(
                "OPENAI_API_KEY required for embedding provider=openai"
            )
        self.model = model
        self.dimension = dimension
        self._client = OpenAI(api_key=key)

    @property
    def client(self) -> OpenAI:
        return self._client

    def embed_texts(
        self,
        texts: list[str],
        *,
        purpose: EmbeddingPurpose = "document",
    ) -> list[list[float]]:
        del purpose  # OpenAI uses the same endpoint for index and query
        if not texts:
            return []

        response = self._client.embeddings.create(input=texts, model=self.model)
        embeddings = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in embeddings]

    def health_check(self) -> tuple[bool, str]:
        try:
            self.embed_texts(["ping"], purpose="query")
            return True, f"openai/{self.model} ok"
        except Exception as exc:  # noqa: BLE001 — surface provider errors to preflight
            return False, f"openai/{self.model} failed: {exc}"
