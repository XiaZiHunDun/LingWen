"""灵文核心 · Domain — 通用实体

Phase 18.1 — 从 infra/world_model/data_structures.py 迁移。

包含跨 domain 子模块共享的基础实体:
- NodeType — 节点类型枚举
- NodeId — (type, name) 复合主键
- KeyPoint — 世界关键点
- Relation — 关键点之间的关系
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    """关键点类型"""

    LOCATION = "location"
    CHARACTER = "character"
    FACTION = "faction"
    ARTIFACT = "artifact"
    CONCEPT = "concept"


@dataclass(frozen=True)
class NodeId:
    """关键点 ID = (type, name) 复合键"""

    type: NodeType
    name: str

    def __str__(self) -> str:
        return f"{self.type.value}:{self.name}"

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("NodeId.name must be non-empty")

    @classmethod
    def from_string(cls, s: str) -> "NodeId":
        """从 "type:name" 字符串还原"""
        if ":" not in s:
            raise ValueError(f"NodeId string must contain ':' — got {s!r}")
        type_str, name = s.split(":", 1)
        return cls(NodeType(type_str), name)


@dataclass
class KeyPoint:
    """关键点 = 世界中一个稳定存在的对象"""

    id: NodeId
    attrs: dict[str, Any] = field(default_factory=dict)
    status: str = "active"
    first_ch: int = 0
    last_ch: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "type": self.id.type.value,
            "name": self.id.name,
            "attrs": self.attrs,
            "status": self.status,
            "first_ch": self.first_ch,
            "last_ch": self.last_ch,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "KeyPoint":
        nid = NodeId.from_string(d["id"])
        return cls(
            id=nid,
            attrs=d.get("attrs", {}),
            status=d.get("status", "active"),
            first_ch=d.get("first_ch", 0),
            last_ch=d.get("last_ch", 0),
        )


@dataclass(frozen=True)
class Relation:
    """关系 = 关键点之间的边"""

    src: NodeId
    dst: NodeId
    type: str  # knows/owns/located_in/allied_to/opposed_to/...
    weight: float = 1.0
    first_ch: int = 0
    last_ch: int = 0

    def __post_init__(self) -> None:
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"Relation.weight must be in [0, 1] — got {self.weight}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "src": str(self.src),
            "dst": str(self.dst),
            "type": self.type,
            "weight": self.weight,
            "first_ch": self.first_ch,
            "last_ch": self.last_ch,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Relation":
        return cls(
            src=NodeId.from_string(d["src"]),
            dst=NodeId.from_string(d["dst"]),
            type=d["type"],
            weight=d.get("weight", 1.0),
            first_ch=d.get("first_ch", 0),
            last_ch=d.get("last_ch", 0),
        )