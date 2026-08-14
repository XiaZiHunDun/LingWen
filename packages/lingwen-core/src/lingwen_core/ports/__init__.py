"""灵文核心 · Ports 接口包

Phase 18.0 — 包对外接口契约集合。

业务侧（use-case / studio_api）只依赖本包的 Protocol，
不直接 import 底层实现（SQLite / OpenAI / 具体 checker）。

导出:
- StoragePort / EventStorePort / DomainEvent — 持久化与事件溯源
- LLMPort / EmbeddingPort — LLM 与嵌入
- CheckerPort — 一致性检查器
- Mock 实现（InMemory* / EchoLLM / HashEmbedding / AlwaysPassChecker）
"""
from __future__ import annotations

from lingwen_core.ports.checker import AlwaysPassChecker, CheckerPort
from lingwen_core.ports.llm import EchoLLM, EmbeddingPort, HashEmbedding, LLMPort
from lingwen_core.ports.storage import (
    DomainEvent,
    EventStorePort,
    InMemoryEventStore,
    InMemoryStoragePort,
    StoragePort,
)

__all__ = [
    # Protocol types
    "StoragePort",
    "EventStorePort",
    "LLMPort",
    "EmbeddingPort",
    "CheckerPort",
    "DomainEvent",
    # Mock implementations
    "InMemoryStoragePort",
    "InMemoryEventStore",
    "EchoLLM",
    "HashEmbedding",
    "AlwaysPassChecker",
]