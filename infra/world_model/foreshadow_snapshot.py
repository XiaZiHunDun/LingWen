"""记忆系统快照增强

伏笔快照（Foreshadow Snapshot）—— 捕获当前卷的伏笔状态，
支持查询已解决、未解决和已放弃的伏笔。

使用方式:
    from infra.world_model.foreshadow_snapshot import (
        ForeshadowSnapshot,
        ForeshadowState,
        capture_foreshadow_state,
        get_unresolved_foreshadows,
        get_resolved_foreshadows,
    )

    all_foreshadows = [
        ForeshadowState(id="fs_001", description="神秘钥匙", planted_chapter=3),
        ForeshadowState(id="fs_002", description="失踪的师兄", planted_chapter=5, resolved_chapter=12),
    ]
    snapshot = capture_foreshadow_state(range(1, 15), all_foreshadows)
    unresolved = snapshot.get_unresolved(14)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Iterable

from infra.errors import ValidationError, SnapshotError

logger = logging.getLogger(__name__)

# ── 自定义异常 ──


class ForeshadowSnapshotError(SnapshotError):
    """伏笔快照操作错误"""


# ── 枚举 ──


class ForeshadowStatus(str, Enum):
    """伏笔状态"""

    PLANTED = "planted"       # 已埋下，尚未回收
    RESOLVED = "resolved"     # 已回收
    ABANDONED = "abandoned"   # 已放弃（剧情需要，不再回收）


# ── 数据模型 ──


@dataclass
class ForeshadowState:
    """伏笔状态数据类

    Attributes:
        id: 伏笔唯一标识
        description: 伏笔描述
        planted_chapter: 埋下伏笔的章节编号
        resolved_chapter: 回收伏笔的章节编号（None 表示未回收）
        status: 伏笔当前状态
    """

    id: str
    description: str
    planted_chapter: int
    resolved_chapter: int | None = None
    status: ForeshadowStatus = ForeshadowStatus.PLANTED

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValidationError(
                "伏笔 ID 不能为空",
                suggestion="请为每个伏笔提供唯一标识",
            )
        if not self.description or not self.description.strip():
            raise ValidationError(
                f"伏笔 {self.id!r} 的描述不能为空",
                suggestion="请提供伏笔的具体描述",
            )
        if self.planted_chapter <= 0:
            raise ValidationError(
                f"伏笔 {self.id!r} 的 planted_chapter 必须为正整数",
                suggestion="请检查伏笔的埋设章节编号",
            )
        if self.resolved_chapter is not None and self.resolved_chapter <= 0:
            raise ValidationError(
                f"伏笔 {self.id!r} 的 resolved_chapter 必须为正整数",
                suggestion="请检查伏笔的回收章节编号",
            )
        # 自动推断状态
        if self.resolved_chapter is not None and self.status == ForeshadowStatus.PLANTED:
            object.__setattr__(self, "status", ForeshadowStatus.RESOLVED)

    def is_resolved(self) -> bool:
        """伏笔是否已回收"""
        return self.status == ForeshadowStatus.RESOLVED

    def is_unresolved(self) -> bool:
        """伏笔是否未回收"""
        return self.status == ForeshadowStatus.PLANTED

    def is_abandoned(self) -> bool:
        """伏笔是否已放弃"""
        return self.status == ForeshadowStatus.ABANDONED

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "id": self.id,
            "description": self.description,
            "planted_chapter": self.planted_chapter,
            "resolved_chapter": self.resolved_chapter,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ForeshadowState:
        """从字典反序列化"""
        return cls(
            id=d["id"],
            description=d["description"],
            planted_chapter=d["planted_chapter"],
            resolved_chapter=d.get("resolved_chapter"),
            status=ForeshadowStatus(d.get("status", "planted")),
        )


# ── 核心类 ──


class ForeshadowSnapshot:
    """伏笔快照 — 捕获当前卷的伏笔状态

    提供按章节范围查询已解决、未解决和已放弃伏笔的功能。
    """

    def __init__(
        self,
        chapter_range: Iterable[int],
        all_foreshadows: Iterable[ForeshadowState],
        snapshot_time: datetime | None = None,
    ) -> None:
        """创建伏笔快照

        Args:
            chapter_range: 快照覆盖的章节范围（如 range(1, 15)）
            all_foreshadows: 所有伏笔列表
            snapshot_time: 快照时间（默认为当前时间）

        Raises:
            ForeshadowSnapshotError: chapter_range 为空时
        """
        chapter_list = list(chapter_range)
        if not chapter_list:
            raise ForeshadowSnapshotError(
                "章节范围不能为空",
                suggestion="请提供有效的章节范围",
            )

        self._chapter_range: tuple[int, ...] = tuple(chapter_list)
        self._snapshot_time: datetime = snapshot_time or datetime.now()
        self._all_foreshadows: tuple[ForeshadowState, ...] = tuple(all_foreshadows)

        # 构建索引
        self._by_id: dict[str, ForeshadowState] = {f.id: f for f in self._all_foreshadows}
        self._unresolved: tuple[ForeshadowState, ...] = tuple(
            f for f in self._all_foreshadows if f.is_unresolved()
        )
        self._resolved: tuple[ForeshadowState, ...] = tuple(
            f for f in self._all_foreshadows if f.is_resolved()
        )
        self._abandoned: tuple[ForeshadowState, ...] = tuple(
            f for f in self._all_foreshadows if f.is_abandoned()
        )

        logger.info(
            "伏笔快照已创建: 章节范围 %d-%d, 总计 %d 个伏笔 (%d 未解决/%d 已解决/%d 已放弃)",
            self.min_chapter, self.max_chapter,
            len(self._all_foreshadows),
            len(self._unresolved),
            len(self._resolved),
            len(self._abandoned),
        )

    # ── 属性 ──

    @property
    def min_chapter(self) -> int:
        """快照覆盖的最小章节"""
        return self._chapter_range[0]

    @property
    def max_chapter(self) -> int:
        """快照覆盖的最大章节"""
        return self._chapter_range[-1]

    @property
    def snapshot_time(self) -> datetime:
        """快照创建时间"""
        return self._snapshot_time

    @property
    def total_count(self) -> int:
        """伏笔总数"""
        return len(self._all_foreshadows)

    # ── 查询方法 ──

    def get_unresolved(self, current_chapter: int | None = None) -> tuple[ForeshadowState, ...]:
        """获取未回收的伏笔

        Args:
            current_chapter: 当前章节编号，如果提供则只返回在当前章节之前埋下的伏笔
                            （即 planted_chapter <= current_chapter）

        Returns:
            未回收伏笔的元组
        """
        if current_chapter is None:
            return self._unresolved

        return tuple(
            f for f in self._unresolved
            if f.planted_chapter <= current_chapter
        )

    def get_resolved(self, current_chapter: int | None = None) -> tuple[ForeshadowState, ...]:
        """获取已回收的伏笔

        Args:
            current_chapter: 当前章节编号，如果提供则只返回在当前章节之前回收的伏笔
                            （即 resolved_chapter <= current_chapter）

        Returns:
            已回收伏笔的元组
        """
        if current_chapter is None:
            return self._resolved

        return tuple(
            f for f in self._resolved
            if f.resolved_chapter is not None and f.resolved_chapter <= current_chapter
        )

    def get_abandoned(self) -> tuple[ForeshadowState, ...]:
        """获取已放弃的伏笔"""
        return self._abandoned

    def get_by_id(self, foreshadow_id: str) -> ForeshadowState | None:
        """按 ID 查找伏笔

        Args:
            foreshadow_id: 伏笔唯一标识

        Returns:
            找到的 ForeshadowState，不存在则返回 None
        """
        return self._by_id.get(foreshadow_id)

    def get_planted_in_chapter(self, chapter: int) -> tuple[ForeshadowState, ...]:
        """获取指定章节埋下的伏笔

        Args:
            chapter: 章节编号

        Returns:
            该章节埋下的所有伏笔
        """
        return tuple(
            f for f in self._all_foreshadows
            if f.planted_chapter == chapter
        )

    def get_resolved_in_chapter(self, chapter: int) -> tuple[ForeshadowState, ...]:
        """获取指定章节回收的伏笔

        Args:
            chapter: 章节编号

        Returns:
            该章节回收的所有伏笔
        """
        return tuple(
            f for f in self._resolved
            if f.resolved_chapter == chapter
        )

    # ── 统计 ──

    def get_stats(self) -> dict[str, Any]:
        """获取伏笔统计信息

        Returns:
            {
                "total": int,
                "unresolved": int,
                "resolved": int,
                "abandoned": int,
                "resolution_rate": float,  # 回收率（不含已放弃）
                "chapter_range": [int, int],
            }
        """
        active = len(self._unresolved) + len(self._resolved)
        resolution_rate = len(self._resolved) / max(active, 1)

        return {
            "total": self.total_count,
            "unresolved": len(self._unresolved),
            "resolved": len(self._resolved),
            "abandoned": len(self._abandoned),
            "resolution_rate": round(resolution_rate, 2),
            "chapter_range": [self.min_chapter, self.max_chapter],
        }

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "chapter_range": list(self._chapter_range),
            "snapshot_time": self._snapshot_time.isoformat(),
            "foreshadows": [f.to_dict() for f in self._all_foreshadows],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ForeshadowSnapshot:
        """从字典反序列化"""
        foreshadows = [ForeshadowState.from_dict(fd) for fd in d.get("foreshadows", [])]
        snapshot_time = None
        if "snapshot_time" in d:
            try:
                snapshot_time = datetime.fromisoformat(d["snapshot_time"])
            except ValueError:
                snapshot_time = datetime.now()

        return cls(
            chapter_range=d.get("chapter_range", []),
            all_foreshadows=foreshadows,
            snapshot_time=snapshot_time,
        )


# ── 模块级便捷函数 ──


def capture_foreshadow_state(
    chapter_range: Iterable[int],
    all_foreshadows: Iterable[ForeshadowState],
) -> ForeshadowSnapshot:
    """捕获当前卷的伏笔状态（便捷函数）

    Args:
        chapter_range: 章节范围（如 range(1, 15)）
        all_foreshadows: 所有伏笔列表

    Returns:
        ForeshadowSnapshot 实例
    """
    return ForeshadowSnapshot(chapter_range, all_foreshadows)


def get_unresolved_foreshadows(
    current_chapter: int,
    snapshot: ForeshadowSnapshot | None = None,
    all_foreshadows: Iterable[ForeshadowState] | None = None,
) -> tuple[ForeshadowState, ...]:
    """获取未回收的伏笔（便捷函数）

    Args:
        current_chapter: 当前章节编号
        snapshot: 已有的快照（可选），不提供则自动创建
        all_foreshadows: 所有伏笔（仅在没有 snapshot 时使用）

    Returns:
        未回收伏笔的元组
    """
    if snapshot is not None:
        return snapshot.get_unresolved(current_chapter)

    if all_foreshadows is None:
        raise ForeshadowSnapshotError(
            "必须提供 snapshot 或 all_foreshadows 参数",
            suggestion="请传入已有的 ForeshadowSnapshot 或伏笔列表",
        )

    temp = ForeshadowSnapshot(range(1, current_chapter + 1), all_foreshadows)
    return temp.get_unresolved(current_chapter)


def get_resolved_foreshadows(
    current_chapter: int,
    snapshot: ForeshadowSnapshot | None = None,
    all_foreshadows: Iterable[ForeshadowState] | None = None,
) -> tuple[ForeshadowState, ...]:
    """获取已回收的伏笔（便捷函数）

    Args:
        current_chapter: 当前章节编号
        snapshot: 已有的快照（可选），不提供则自动创建
        all_foreshadows: 所有伏笔（仅在没有 snapshot 时使用）

    Returns:
        已回收伏笔的元组
    """
    if snapshot is not None:
        return snapshot.get_resolved(current_chapter)

    if all_foreshadows is None:
        raise ForeshadowSnapshotError(
            "必须提供 snapshot 或 all_foreshadows 参数",
            suggestion="请传入已有的 ForeshadowSnapshot 或伏笔列表",
        )

    temp = ForeshadowSnapshot(range(1, current_chapter + 1), all_foreshadows)
    return temp.get_resolved(current_chapter)


__all__ = [
    "ForeshadowSnapshot",
    "ForeshadowState",
    "ForeshadowStatus",
    "ForeshadowSnapshotError",
    "capture_foreshadow_state",
    "get_unresolved_foreshadows",
    "get_resolved_foreshadows",
]