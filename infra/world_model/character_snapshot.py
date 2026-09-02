"""人物状态快照

捕获当前卷的人物属性变更记录，支持查询人物状态演变历史。

使用方式:
    from infra.world_model.character_snapshot import (
        CharacterSnapshot,
        CharacterState,
        CharacterAttributeChange,
        capture_character_state,
        get_character_changes,
    )

    states = [
        CharacterState(id="char_001", name="张三", chapter=3, attributes={"age": 25, "mood": "平静"}),
        CharacterState(id="char_001", name="张三", chapter=5, attributes={"age": 25, "mood": "愤怒"}),
    ]
    snapshot = capture_character_state(range(1, 10), states)
    changes = snapshot.get_changes_for("char_001")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable

from infra.errors import SnapshotError, ValidationError

logger = logging.getLogger(__name__)

# ── 自定义异常 ──


class CharacterSnapshotError(SnapshotError):
    """人物快照操作错误"""


# ── 数据模型 ──


@dataclass
class CharacterAttributeChange:
    """单个人物属性变更记录

    Attributes:
        attribute: 属性名
        old_value: 旧值
        new_value: 新值
        chapter: 发生变更的章节编号
    """

    attribute: str
    old_value: Any
    new_value: Any
    chapter: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "attribute": self.attribute,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "chapter": self.chapter,
        }


@dataclass
class CharacterState:
    """人物在某一章节的状态快照

    Attributes:
        id: 人物唯一标识
        name: 人物名称
        chapter: 章节编号
        attributes: 人物属性字典（如 age、mood、location、status 等）
        relationships: 当前章节的人物关系快照（可选）
    """

    id: str
    name: str
    chapter: int
    attributes: dict[str, Any] = field(default_factory=dict)
    relationships: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValidationError(
                "人物 ID 不能为空",
                suggestion="请为每个人物提供唯一标识",
            )
        if not self.name or not self.name.strip():
            raise ValidationError(
                f"人物 {self.id!r} 的名称不能为空",
                suggestion="请提供人物名称",
            )
        if self.chapter <= 0:
            raise ValidationError(
                f"人物 {self.id!r} 的 chapter 必须为正整数",
                suggestion="请检查章节编号",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "chapter": self.chapter,
            "attributes": self.attributes,
            "relationships": self.relationships,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CharacterState:
        return cls(
            id=d["id"],
            name=d["name"],
            chapter=d["chapter"],
            attributes=d.get("attributes", {}),
            relationships=d.get("relationships", {}),
        )


# ── 核心类 ──


class CharacterSnapshot:
    """人物状态快照 — 捕获当前卷的人物属性变更

    提供按人物 ID 或章节查询属性变更历史的功能。
    """

    def __init__(
        self,
        chapter_range: Iterable[int],
        character_states: Iterable[CharacterState],
        snapshot_time: datetime | None = None,
    ) -> None:
        """创建人物状态快照

        Args:
            chapter_range: 快照覆盖的章节范围
            character_states: 所有人物状态列表（按章节排列）
            snapshot_time: 快照时间

        Raises:
            CharacterSnapshotError: chapter_range 为空时
        """
        chapter_list = list(chapter_range)
        if not chapter_list:
            raise CharacterSnapshotError(
                "章节范围不能为空",
                suggestion="请提供有效的章节范围",
            )

        self._chapter_range: tuple[int, ...] = tuple(chapter_list)
        self._snapshot_time: datetime = snapshot_time or datetime.now()

        # 按人物 ID 分组，按章节排序
        self._by_character: dict[str, list[CharacterState]] = {}
        for state in character_states:
            self._by_character.setdefault(state.id, []).append(state)

        for char_id in self._by_character:
            self._by_character[char_id].sort(key=lambda s: s.chapter)

        # 计算变更
        self._changes: dict[str, list[CharacterAttributeChange]] = {}
        self._compute_changes()

        logger.info(
            "人物状态快照已创建: 章节范围 %d-%d, %d 个人物, %d 条状态记录",
            self.min_chapter,
            self.max_chapter,
            len(self._by_character),
            sum(len(v) for v in self._by_character.values()),
        )

    # ── 属性 ──

    @property
    def min_chapter(self) -> int:
        return self._chapter_range[0]

    @property
    def max_chapter(self) -> int:
        return self._chapter_range[-1]

    @property
    def snapshot_time(self) -> datetime:
        return self._snapshot_time

    @property
    def character_ids(self) -> tuple[str, ...]:
        return tuple(self._by_character.keys())

    # ── 查询方法 ──

    def get_state(self, character_id: str, chapter: int) -> CharacterState | None:
        """获取指定人物在指定章节的状态

        Args:
            character_id: 人物 ID
            chapter: 章节编号

        Returns:
            CharacterState 或 None（不存在时）
        """
        states = self._by_character.get(character_id, [])
        for state in states:
            if state.chapter == chapter:
                return state
        # 返回最近的状态
        latest = None
        for state in states:
            if state.chapter <= chapter:
                latest = state
        return latest

    def get_latest_state(self, character_id: str) -> CharacterState | None:
        """获取指定人物的最新状态

        Args:
            character_id: 人物 ID

        Returns:
            最新的 CharacterState 或 None
        """
        states = self._by_character.get(character_id, [])
        return states[-1] if states else None

    def get_changes_for(self, character_id: str) -> tuple[CharacterAttributeChange, ...]:
        """获取指定人物的所有属性变更

        Args:
            character_id: 人物 ID

        Returns:
            属性变更元组
        """
        return tuple(self._changes.get(character_id, []))

    def get_all_changes_in_chapter(self, chapter: int) -> dict[str, tuple[CharacterAttributeChange, ...]]:
        """获取指定章节所有人物的属性变更

        Args:
            chapter: 章节编号

        Returns:
            {character_id: 变更元组, ...}
        """
        result: dict[str, tuple[CharacterAttributeChange, ...]] = {}
        for char_id, changes in self._changes.items():
            chapter_changes = tuple(c for c in changes if c.chapter == chapter)
            if chapter_changes:
                result[char_id] = chapter_changes
        return result

    def get_all_changes(self) -> dict[str, tuple[CharacterAttributeChange, ...]]:
        """获取所有人物的属性变更

        Returns:
            {character_id: 变更元组, ...}
        """
        return {cid: tuple(changes) for cid, changes in self._changes.items()}

    # ── 统计 ──

    def get_stats(self) -> dict[str, Any]:
        """获取人物状态统计"""
        total_changes = sum(len(v) for v in self._changes.values())
        chars_with_changes = len(self._changes)

        return {
            "total_characters": len(self._by_character),
            "total_state_records": sum(len(v) for v in self._by_character.values()),
            "total_changes": total_changes,
            "characters_with_changes": chars_with_changes,
            "chapter_range": [self.min_chapter, self.max_chapter],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "chapter_range": list(self._chapter_range),
            "snapshot_time": self._snapshot_time.isoformat(),
            "characters": {cid: [s.to_dict() for s in states] for cid, states in self._by_character.items()},
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CharacterSnapshot:
        states: list[CharacterState] = []
        for char_states in d.get("characters", {}).values():
            for sd in char_states:
                states.append(CharacterState.from_dict(sd))

        snapshot_time = None
        if "snapshot_time" in d:
            try:
                snapshot_time = datetime.fromisoformat(d["snapshot_time"])
            except ValueError:
                snapshot_time = datetime.now()

        return cls(
            chapter_range=d.get("chapter_range", []),
            character_states=states,
            snapshot_time=snapshot_time,
        )

    # ── 内部方法 ──

    def _compute_changes(self) -> None:
        """计算人物属性变更"""
        for char_id, states in self._by_character.items():
            if len(states) < 2:
                continue

            changes: list[CharacterAttributeChange] = []
            prev_state = states[0]

            for curr_state in states[1:]:
                # 比较 attributes
                all_keys = set(prev_state.attributes.keys()) | set(curr_state.attributes.keys())
                for key in sorted(all_keys):
                    old_val = prev_state.attributes.get(key)
                    new_val = curr_state.attributes.get(key)
                    if old_val != new_val:
                        changes.append(
                            CharacterAttributeChange(
                                attribute=key,
                                old_value=old_val,
                                new_value=new_val,
                                chapter=curr_state.chapter,
                            )
                        )

                # 比较 relationships
                all_rel_keys = set(prev_state.relationships.keys()) | set(curr_state.relationships.keys())
                for key in sorted(all_rel_keys):
                    old_val = prev_state.relationships.get(key)
                    new_val = curr_state.relationships.get(key)
                    if old_val != new_val:
                        changes.append(
                            CharacterAttributeChange(
                                attribute=f"relationship:{key}",
                                old_value=old_val,
                                new_value=new_val,
                                chapter=curr_state.chapter,
                            )
                        )

                prev_state = curr_state

            if changes:
                self._changes[char_id] = changes


# ── 模块级便捷函数 ──


def capture_character_state(
    chapter_range: Iterable[int],
    character_states: Iterable[CharacterState],
) -> CharacterSnapshot:
    """捕获当前卷的人物状态（便捷函数）

    Args:
        chapter_range: 章节范围
        character_states: 所有人物状态列表

    Returns:
        CharacterSnapshot 实例
    """
    return CharacterSnapshot(chapter_range, character_states)


def get_character_changes(
    character_id: str,
    snapshot: CharacterSnapshot | None = None,
    character_states: Iterable[CharacterState] | None = None,
    chapter_range: Iterable[int] | None = None,
) -> tuple[CharacterAttributeChange, ...]:
    """获取指定人物的属性变更（便捷函数）

    Args:
        character_id: 人物 ID
        snapshot: 已有的快照（可选）
        character_states: 人物状态列表（仅在没有 snapshot 时使用）
        chapter_range: 章节范围（仅在没有 snapshot 时使用）

    Returns:
        属性变更元组
    """
    if snapshot is not None:
        return snapshot.get_changes_for(character_id)

    if character_states is None or chapter_range is None:
        raise CharacterSnapshotError(
            "必须提供 snapshot 或 (character_states + chapter_range) 参数",
            suggestion="请传入已有的 CharacterSnapshot 或状态列表和章节范围",
        )

    temp = CharacterSnapshot(chapter_range, character_states)
    return temp.get_changes_for(character_id)


__all__ = [
    "CharacterSnapshot",
    "CharacterState",
    "CharacterAttributeChange",
    "CharacterSnapshotError",
    "capture_character_state",
    "get_character_changes",
]
