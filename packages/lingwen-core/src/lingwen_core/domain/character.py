"""灵文核心 · Domain — Character 实体

Phase 18.1 — 角色域实体。

Character 是 NodeType.CHARACTER 的特化,带人物弧光追踪。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CharacterStatus(str, Enum):
    """角色状态"""

    ALIVE = "alive"
    DEAD = "dead"
    UNKNOWN = "unknown"
    TRANSFORMED = "transformed"


@dataclass(frozen=True)
class Character:
    """角色实体 — 人物弧光追踪

    Invariants:
    - name 非空
    - status 合法枚举值
    """

    name: str
    status: CharacterStatus = CharacterStatus.ALIVE
    faction: str = ""
    role: str = ""  # 主角/配角/反派/路人
    arc_milestones: tuple[str, ...] = ()
    first_ch: int = 0
    last_ch: int = 0
    attrs: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Character.name must be non-empty")