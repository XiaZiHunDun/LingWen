"""MiniMax embo-01 embedding provider (beta, non-OpenAI API shape)."""
from __future__ import annotations

import os
from typing import Any

import httpx

from infra.memory_system.embeddings.base import EmbeddingProviderError, EmbeddingPurpose


class MiniMaxEmbeddingProvider:
    """MiniMax ``/v1/embeddings`` with ``type=db|query`` (beta)."""

    provider_name = "minimax"

    def __init__(
        self,
        *,
        model: str,
        dimension: int,
        api_key: str | None = None,
        base_url: str | None = None,
        group_id: str | None = None,
        timeout: float = 60.0,
    ):
        key = api_key or os.environ.get("MINIMAX_API_KEY", "")
        if not key:
            raise EmbeddingProviderError(
                "MINIMAX_API_KEY required for embedding provider=minimax"
            )
        self.model = model
        self.dimension = dimension
        self._api_key = key
        self._base_url = (
            base_url
            or os.environ.get("MINIMAX_API_HOST", "https://api.minimaxi.com")
        ).rstrip("/")
        self._group_id = group_id or os.environ.get("MINIMAX_GROUP_ID", "")
        self._timeout = timeout

    def _embed_type(self, purpose: EmbeddingPurpose) -> str:
        return "query" if purpose == "query" else "db"

    def _parse_vectors(self, data: dict[str, Any]) -> list[list[float]]:
        base = data.get("base_resp") or {}
        status = base.get("status_code")
        if status is not None and status != 0:
            msg = base.get("status_msg") or base.get("message") or f"status_code={status}"
            raise EmbeddingProviderError(f"MiniMax embedding API error: {msg}")

        vectors = data.get("vectors")
        if vectors is not None:
            return vectors

        # OpenAI-shaped fallback (some gateways)
        items = data.get("data")
        if items:
            ordered = sorted(items, key=lambda item: item.get("index", 0))
            return [item["embedding"] for item in ordered]

        raise EmbeddingProviderError("MiniMax embedding response missing vectors")

    def embed_texts(
        self,
        texts: list[str],
        *,
        purpose: EmbeddingPurpose = "document",
    ) -> list[list[float]]:
        if not texts:
            return []

        url = f"{self._base_url}/v1/embeddings"
        params: dict[str, str] = {}
        if self._group_id:
            params["GroupId"] = self._group_id

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "texts": texts,
            "type": self._embed_type(purpose),
        }

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(url, params=params or None, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise EmbeddingProviderError(f"MiniMax embedding HTTP error: {exc}") from exc
        except Exception as exc:
            raise EmbeddingProviderError(f"MiniMax embedding failed: {exc}") from exc

        vectors = self._parse_vectors(data)
        if len(vectors) != len(texts):
            raise EmbeddingProviderError(
                f"MiniMax returned {len(vectors)} vectors for {len(texts)} texts"
            )
        return vectors

    def health_check(self) -> tuple[bool, str]:
        try:
            self.embed_texts(["ping"], purpose="query")
            group_hint = " group_id=set" if self._group_id else " group_id=unset(CN may need MINIMAX_GROUP_ID)"
            return True, f"minimax/{self.model} ok{group_hint}"
        except Exception as exc:  # noqa: BLE001
            hint = (
                " (beta — API may be unavailable; try LINGWEN_EMBEDDING_PROVIDER=openai "
                "or LINGWEN_MEMORY_RAG=stub)"
            )
            return False, f"minimax/{self.model} failed: {exc}{hint}"
