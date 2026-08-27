"""灵文核心 · Storage Ports

Phase 18.0 — 持久化与事件溯源接口契约。

设计原则:
- Protocol 而非 ABC（运行时 duck typing，便于依赖注入）
- 业务侧只依赖本模块，不依赖具体存储后端（SQLite/JSON/内存）
- Mock 实现位于同模块，便于测试
"""
from __future__ import annotations

import time
import uuid
from typing import Any, Iterator, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """领域事件基类 — 事件溯源的事件载体。

    所有业务事件都应继承此类。事件不可变（frozen=True），
    追加到 EventStore 后不允许修改。
    """

    event_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    occurred_at: float = Field(default_factory=time.time)
    type: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}


@runtime_checkable
class StoragePort(Protocol):
    """键值存储接口。

    用于配置、缓存、临时状态。use-case 不应直接读写 SQLite，
    应通过此接口与底层存储解耦。
    """

    def save(self, key: str, value: Any) -> None: ...
    def load(self, key: str) -> Any | None: ...
    def delete(self, key: str) -> None: ...


@runtime_checkable
class EventStorePort(Protocol):
    """事件溯源存储接口。

    所有业务状态变更通过 append(events) 持久化，通过 replay(since) 重放。
    """

    def append(self, event: DomainEvent) -> None: ...
    def replay(self, since: int = 0) -> Iterator[DomainEvent]: ...


class InMemoryStoragePort:
    """StoragePort 的内存实现 — 用于测试和开发环境。"""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def save(self, key: str, value: Any) -> None:
        self._data[key] = value

    def load(self, key: str) -> Any | None:
        return self._data.get(key)

    def delete(self, key: str) -> None:
        self._data.pop(key, None)


class InMemoryEventStore:
    """EventStorePort 的内存实现 — 顺序追加，索引式重放。"""

    def __init__(self) -> None:
        self._events: list[DomainEvent] = []

    def append(self, event: DomainEvent) -> None:
        self._events.append(event)

    def replay(self, since: int = 0) -> Iterator[DomainEvent]:
        for event in self._events[since:]:
            yield event
