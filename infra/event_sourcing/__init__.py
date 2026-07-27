"""事件溯源模块

提供领域事件模型、事件存储和快照机制。

核心功能：
1. 领域事件定义（DomainEvent）
2. 事件存储（EventStore）— 支持序列号管理、冲突检测、重放验证、聚合拥有者
3. 快照机制（Snapshot）
4. 事件重放（replay_events）— 支持外部事件重放验证

参考 opencode 的事件溯源系统设计：
- 序列号冲突检测（SequenceConflictError）
- 重放数据分歧检测（ReplayDivergedError）
- 聚合拥有者机制（OwnerMismatchError）
- 事务性事件提交
"""

from .models import (
    DomainEvent,
    EventSerializer,
    EventStream,
    EventType,
    Snapshot,
    versioned_type,
)
from .store import (
    EventExistsError,
    EventStore,
    EventStoreError,
    OwnerMismatchError,
    ReplayDivergedError,
    SequenceConflictError,
    create_event,
    create_snapshot,
)

__all__ = [
    "DomainEvent",
    "EventSerializer",
    "EventStream",
    "EventType",
    "Snapshot",
    "EventStore",
    "EventStoreError",
    "SequenceConflictError",
    "ReplayDivergedError",
    "EventExistsError",
    "OwnerMismatchError",
    "create_event",
    "create_snapshot",
    "versioned_type",
]
