"""创意豁免白名单

管理创意豁免章节的白名单，白名单中的章节在一致性检查时只保留
钻石级（diamond）检查，金级（gold）和银级（silver）检查降级为建议。

使用方式:
    from lingwen_quality.consistency.creative_whitelist import (
        CreativeWhitelist,
        add_whitelist,
        is_whitelisted,
        remove_whitelist,
        get_whitelisted_chapters,
    )

    add_whitelist(12, "关键转折章节，允许创意突破", expires_at="2026-12-31")
    if is_whitelisted(12):
        print("第 12 章在白名单中，仅执行钻石级检查")
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from infra.errors import ValidationError

logger = logging.getLogger(__name__)

# ── 自定义异常 ──


class WhitelistError(ValidationError):
    """白名单操作错误"""


class ChapterAlreadyWhitelistedError(WhitelistError):
    """章节已在白名单中"""


class ChapterNotWhitelistedError(WhitelistError):
    """章节不在白名单中"""


# ── 检查等级常量 ──

DIAMOND = "diamond"  # 钻石级 — 必须执行，不可降级
GOLD = "gold"        # 金级 — 白名单中降级为建议
SILVER = "silver"    # 银级 — 白名单中降级为建议

# 白名单章节只保留钻石级检查，金/银降级为建议
DOWNGRADED_LEVELS = frozenset({GOLD, SILVER})


# ── 数据模型 ──


@dataclass
class WhitelistChapter:
    """白名单章节条目"""

    chapter_num: int
    reason: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    expires_at: str | None = None  # ISO 日期字符串 "YYYY-MM-DD"，None 表示永不过期

    def is_expired(self) -> bool:
        """检查是否已过期"""
        if self.expires_at is None:
            return False
        try:
            expiry = date.fromisoformat(self.expires_at)
            return date.today() > expiry
        except ValueError:
            logger.warning("白名单章节 %d 的过期时间格式无效: %s", self.chapter_num, self.expires_at)
            return False


# ── 核心类 ──


class CreativeWhitelist:
    """创意豁免白名单管理器（单例）

    管理可豁免严格一致性检查的章节列表。
    白名单中的章节：
    - 钻石级检查：正常执行
    - 金级检查：降级为建议（不阻断）
    - 银级检查：降级为建议（不阻断）
    """

    _instance: CreativeWhitelist | None = None

    def __new__(cls) -> CreativeWhitelist:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._chapters: dict[int, WhitelistChapter] = {}

    # ── 白名单操作 ──

    def add(self, chapter_num: int, reason: str, expires_at: str | None = None) -> WhitelistChapter:
        """添加章节到白名单

        Args:
            chapter_num: 章节编号
            reason: 豁免原因
            expires_at: 过期日期（ISO 格式 "YYYY-MM-DD"），None 表示永不过期

        Returns:
            新创建的 WhitelistChapter

        Raises:
            ChapterAlreadyWhitelistedError: 章节已在白名单中
            WhitelistError: 参数无效
        """
        if chapter_num <= 0:
            raise WhitelistError(
                f"章节编号必须为正整数，收到: {chapter_num}",
                suggestion="请使用大于 0 的章节编号",
            )
        if not reason or not reason.strip():
            raise WhitelistError(
                "豁免原因不能为空",
                suggestion="请提供具体的豁免原因",
            )

        if chapter_num in self._chapters:
            existing = self._chapters[chapter_num]
            if not existing.is_expired():
                raise ChapterAlreadyWhitelistedError(
                    f"第 {chapter_num} 章已在白名单中（原因: {existing.reason}）",
                    suggestion="如需更新原因，请先 remove_whitelist 再 add_whitelist",
                )
            # 已过期则覆盖
            logger.info("第 %d 章白名单记录已过期，将被覆盖", chapter_num)

        if expires_at is not None:
            try:
                date.fromisoformat(expires_at)
            except ValueError as e:
                raise WhitelistError(
                    f"过期日期格式无效: {expires_at!r}",
                    suggestion='请使用 "YYYY-MM-DD" 格式',
                ) from e

        entry = WhitelistChapter(
            chapter_num=chapter_num,
            reason=reason.strip(),
            expires_at=expires_at,
        )
        self._chapters[chapter_num] = entry
        logger.info("第 %d 章已加入创意豁免白名单（原因: %s）", chapter_num, reason)
        return entry

    def is_whitelisted(self, chapter_num: int) -> bool:
        """检查章节是否在白名单中（且未过期）

        Args:
            chapter_num: 章节编号

        Returns:
            True 表示在白名单中且未过期
        """
        entry = self._chapters.get(chapter_num)
        if entry is None:
            return False
        if entry.is_expired():
            logger.debug("第 %d 章白名单记录已过期，自动清理", chapter_num)
            del self._chapters[chapter_num]
            return False
        return True

    def remove(self, chapter_num: int) -> WhitelistChapter:
        """从白名单中移除章节

        Args:
            chapter_num: 章节编号

        Returns:
            被移除的 WhitelistChapter

        Raises:
            ChapterNotWhitelistedError: 章节不在白名单中
        """
        if chapter_num not in self._chapters:
            raise ChapterNotWhitelistedError(
                f"第 {chapter_num} 章不在白名单中",
                suggestion="请确认章节编号是否正确",
            )
        entry = self._chapters.pop(chapter_num)
        logger.info("第 %d 章已从创意豁免白名单中移除", chapter_num)
        return entry

    def get_whitelisted_chapters(self) -> list[dict[str, Any]]:
        """列出所有白名单中的章节（自动清理过期记录）

        Returns:
            [{"chapter_num": int, "reason": str, "created_at": str, "expires_at": str|None}, ...]
        """
        # 清理过期记录
        expired = [n for n, e in self._chapters.items() if e.is_expired()]
        for n in expired:
            del self._chapters[n]
            logger.debug("清理过期的白名单记录: 第 %d 章", n)

        return [
            {
                "chapter_num": e.chapter_num,
                "reason": e.reason,
                "created_at": e.created_at,
                "expires_at": e.expires_at,
            }
            for e in sorted(self._chapters.values(), key=lambda x: x.chapter_num)
        ]

    def get_downgraded_levels(self) -> frozenset[str]:
        """返回白名单章节中应降级的检查等级

        Returns:
            frozenset({"gold", "silver"})
        """
        return DOWNGRADED_LEVELS

    def should_downgrade(self, check_level: str) -> bool:
        """判断指定检查等级在白名单中是否应降级为建议

        Args:
            check_level: 检查等级（"diamond" / "gold" / "silver"）

        Returns:
            True 表示应降级
        """
        return check_level in DOWNGRADED_LEVELS

    # ── 持久化 ──

    def save_to_file(self, filepath: str) -> None:
        """保存白名单到 JSON 文件"""
        import os
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        data = [
            {
                "chapter_num": e.chapter_num,
                "reason": e.reason,
                "created_at": e.created_at,
                "expires_at": e.expires_at,
            }
            for e in sorted(self._chapters.values(), key=lambda x: x.chapter_num)
        ]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("白名单已保存至 %s（%d 条记录）", filepath, len(data))

    def load_from_file(self, filepath: str) -> None:
        """从 JSON 文件加载白名单"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except FileNotFoundError:
            logger.warning("白名单文件不存在: %s，使用空白名单", filepath)
            self._chapters = {}
            return
        except (json.JSONDecodeError, OSError) as e:
            raise WhitelistError(f"白名单文件加载失败: {e}") from e

        self._chapters = {}
        for item in raw:
            if not isinstance(item, dict):
                continue
            entry = WhitelistChapter(
                chapter_num=item.get("chapter_num", 0),
                reason=item.get("reason", ""),
                created_at=item.get("created_at", ""),
                expires_at=item.get("expires_at"),
            )
            # 跳过已过期的记录
            if entry.is_expired():
                logger.debug("跳过已过期的白名单记录: 第 %d 章", entry.chapter_num)
                continue
            self._chapters[entry.chapter_num] = entry
        logger.info("从 %s 加载了 %d 条白名单记录", filepath, len(self._chapters))

    def clear(self) -> None:
        """清空所有白名单记录"""
        self._chapters.clear()
        logger.info("白名单记录已清空")


# ── 模块级便捷函数 ──


def add_whitelist(chapter_num: int, reason: str, expires_at: str | None = None) -> WhitelistChapter:
    """添加章节到创意豁免白名单（便捷函数）

    Args:
        chapter_num: 章节编号
        reason: 豁免原因
        expires_at: 过期日期（"YYYY-MM-DD"），None 表示永不过期

    Returns:
        新创建的 WhitelistChapter
    """
    return CreativeWhitelist().add(chapter_num, reason, expires_at)


def is_whitelisted(chapter_num: int) -> bool:
    """检查章节是否在白名单中（便捷函数）

    Args:
        chapter_num: 章节编号

    Returns:
        True 表示在白名单中且未过期
    """
    return CreativeWhitelist().is_whitelisted(chapter_num)


def remove_whitelist(chapter_num: int) -> WhitelistChapter:
    """从白名单中移除章节（便捷函数）

    Args:
        chapter_num: 章节编号

    Returns:
        被移除的 WhitelistChapter
    """
    return CreativeWhitelist().remove(chapter_num)


def get_whitelisted_chapters() -> list[dict[str, Any]]:
    """列出所有白名单章节（便捷函数）

    Returns:
        [{"chapter_num": int, "reason": str, ...}, ...]
    """
    return CreativeWhitelist().get_whitelisted_chapters()


__all__ = [
    "CreativeWhitelist",
    "WhitelistChapter",
    "WhitelistError",
    "ChapterAlreadyWhitelistedError",
    "ChapterNotWhitelistedError",
    "DIAMOND",
    "GOLD",
    "SILVER",
    "DOWNGRADED_LEVELS",
    "add_whitelist",
    "is_whitelisted",
    "remove_whitelist",
    "get_whitelisted_chapters",
]
