#!/usr/bin/env python3
"""
事件溯源模型定义

支持：
1. 领域事件模型
2. 事件存储表定义
3. 快照模型
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Type, TypeVar

T = TypeVar('T')


class EventType(Enum):
    """事件类型枚举"""
    # 创作相关
    CHAPTER_CREATED = "chapter_created"
    CHAPTER_UPDATED = "chapter_updated"
    CHAPTER_DELETED = "chapter_deleted"
    CHAPTER_PUBLISHED = "chapter_published"

    # 工作流相关
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_PAUSED = "workflow_paused"

    # 审核相关
    AUDIT_CREATED = "audit_created"
    AUDIT_APPROVED = "audit_approved"
    AUDIT_REJECTED = "audit_rejected"

    # 项目相关
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"

    # 用户相关
    USER_ACTION = "user_action"

    # 系统相关
    SYSTEM_EVENT = "system_event"


def versioned_type(event_type: str, version: int) -> str:
    """生成版本化事件类型名"""
    return f"{event_type}.{version}"


@dataclass
class DomainEvent:
    """领域事件基类"""
    event_id: str
    event_type: EventType
    aggregate_id: str
    aggregate_type: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    seq: int = 0
    owner_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "payload": self.payload,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "seq": self.seq,
            "owner_id": self.owner_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEvent":
        """从字典创建"""
        return cls(
            event_id=data["event_id"],
            event_type=EventType(data["event_type"]),
            aggregate_id=data["aggregate_id"],
            aggregate_type=data["aggregate_type"],
            payload=data["payload"],
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            version=data.get("version", 1),
            seq=data.get("seq", 0),
            owner_id=data.get("owner_id"),
        )


@dataclass
class Snapshot:
    """状态快照"""
    snapshot_id: str
    aggregate_id: str
    aggregate_type: str
    state: Dict[str, Any]
    version: int
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "snapshot_id": self.snapshot_id,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "state": self.state,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Snapshot":
        """从字典创建"""
        return cls(
            snapshot_id=data["snapshot_id"],
            aggregate_id=data["aggregate_id"],
            aggregate_type=data["aggregate_type"],
            state=data["state"],
            version=data["version"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


@dataclass
class EventStream:
    """事件流"""
    aggregate_id: str
    events: list[DomainEvent] = field(default_factory=list)

    @property
    def version(self) -> int:
        """当前版本"""
        return len(self.events)

    def append(self, event: DomainEvent) -> None:
        """追加事件"""
        event.version = self.version + 1
        self.events.append(event)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "aggregate_id": self.aggregate_id,
            "version": self.version,
            "events": [e.to_dict() for e in self.events],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventStream":
        """从字典创建"""
        stream = cls(aggregate_id=data["aggregate_id"])
        for event_data in data.get("events", []):
            stream.append(DomainEvent.from_dict(event_data))
        return stream


class EventSerializer:
    """事件序列化器"""

    @staticmethod
    def serialize(event: DomainEvent) -> str:
        """序列化事件"""
        return json.dumps(event.to_dict(), ensure_ascii=False)

    @staticmethod
    def deserialize(data: str) -> DomainEvent:
        """反序列化事件"""
        return DomainEvent.from_dict(json.loads(data))

    @staticmethod
    def serialize_snapshot(snapshot: Snapshot) -> str:
        """序列化快照"""
        return json.dumps(snapshot.to_dict(), ensure_ascii=False)

    @staticmethod
    def deserialize_snapshot(data: str) -> Snapshot:
        """反序列化快照"""
        return Snapshot.from_dict(json.loads(data))
