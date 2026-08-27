"""灵文核心 · LLM Ports

Phase 18.0 — 大语言模型与嵌入接口契约。
"""
from __future__ import annotations

import hashlib
from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMPort(Protocol):
    """大语言模型接口（同步版本）。

    tier 参数用于路由到不同模型/不同成本档位：
    - "fast" — 便宜快速（gpt-4o-mini / claude-haiku）
    - "balanced" — 默认（gpt-4o / claude-sonnet）
    - "deep" — 深度推理（o1 / claude-opus）
    """

    def complete(self, prompt: str, *, tier: str = "balanced") -> str: ...


@runtime_checkable
class EmbeddingPort(Protocol):
    """嵌入向量接口。"""

    def embed(self, text: str) -> list[float]: ...


class EchoLLM:
    """LLMPort 的最简实现 — 直接回显输入。

    用于测试和开发场景，避免真实 API 调用成本。
    """

    def complete(self, prompt: str, *, tier: str = "balanced") -> str:
        return prompt


class HashEmbedding:
    """EmbeddingPort 的最简实现 — 基于 SHA-256 派生确定性向量。

    同一文本永远产生相同向量；不同文本产生不同向量。
    默认 16 维。
    """

    def __init__(self, dim: int = 16) -> None:
        self._dim = dim

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        # 扩展到所需维度：循环使用 digest 字节
        raw = (digest * ((self._dim // len(digest)) + 1))[: self._dim]
        # 归一化到 [0, 1)
        return [b / 256.0 for b in raw]
