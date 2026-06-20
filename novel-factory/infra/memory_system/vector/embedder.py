"""嵌入模型管理 — facade over pluggable embedding providers (F89)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from infra.memory_system.embeddings.base import EmbeddingProvider, EmbeddingPurpose
from infra.memory_system.embeddings.factory import create_embedding_provider

if TYPE_CHECKING:
    from openai import OpenAI


class Embedder:
    """嵌入模型管理类

    配置从 memory_config.yaml 的 embedding 部分读取；
    具体 backend 由 ``create_embedding_provider()`` 解析。
    """

    MEMORY_CONFIG_PATH = "config/memory_config.yaml"

    def __init__(self, provider: EmbeddingProvider | None = None):
        """初始化嵌入模型

        Args:
            provider: 可选注入（测试 / CI）；默认从 config + env 创建。

        Raises:
            RuntimeError: 配置或 provider 初始化失败
        """
        try:
            self._provider: EmbeddingProvider = provider or create_embedding_provider()
        except Exception as exc:
            raise RuntimeError(f"Failed to initialize Embedder: {exc}") from exc

        self.model = self._provider.model
        self.dimension = self._provider.dimension

    @property
    def provider_name(self) -> str:
        return self._provider.provider_name

    @property
    def client(self) -> OpenAI:
        """OpenAI 客户端（仅 provider=openai 时可用，兼容旧测试）。"""
        if hasattr(self._provider, "client"):
            return self._provider.client  # type: ignore[no-any-return]
        raise AttributeError(
            f"Embedder.client unavailable for provider={self.provider_name}"
        )

    def health_check(self) -> tuple[bool, str]:
        return self._provider.health_check()

    def embed_texts(
        self,
        texts: list[str],
        *,
        purpose: EmbeddingPurpose = "document",
    ) -> list[list[float]]:
        """将文本列表转换为嵌入向量列表"""
        if not texts:
            return []
        return self._provider.embed_texts(texts, purpose=purpose)

    def embed_query(self, query: str) -> list[float]:
        """单条检索 query 嵌入（MiniMax 使用 type=query）。"""
        vectors = self.embed_texts([query], purpose="query")
        return vectors[0] if vectors else []
