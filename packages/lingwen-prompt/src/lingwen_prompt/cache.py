"""灵文提示词工程 · 上下文缓存层

V3.1 Phase 1.2 — 三层缓存降低 AI 调用 token 消耗。

设计原则:
- 三层缓存: 永久(故事契约/世界观) → 卷级(大纲/人物状态) → 章节级(上下文)
- 哈希校验: 内容变更 → 缓存失效，否则复用
- 延迟加载: 首次访问时构建，后续命中缓存
- 线程安全: 适用于单线程 WSGI/ASGI，如需要多线程加锁由上层处理

缓存层级:
- permanent: 故事契约 + 世界观设定 — 极少变更，构建一次
- volume: 当前卷大纲 + 人物状态 + 伏笔快照 — 卷切换时重建
- chapter: 章节历史 + 用户输入 — 每次调用更新

与 ContextBuilder 集成:
    cache = ContextCache()
    cached = cache.get_or_build("volume_outline", lambda: build_volume_outline())
    builder = ContextBuilder(ctx).add_source("volume_outline", cached)
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger(__name__)


class ContextCacheError(Exception):
    """上下文缓存异常基类"""


class CacheMissError(ContextCacheError):
    """缓存未命中（不应该发生，表明构建函数未注册）"""


@dataclass
class CacheEntry:
    """缓存条目 — 携带内容、哈希和时间戳"""

    key: str
    content: str
    content_hash: str
    created_at: float
    last_accessed_at: float
    hit_count: int = 0

    def touch(self) -> None:
        """更新访问时间"""
        self.last_accessed_at = __import__("time").time()
        self.hit_count += 1


@dataclass
class CacheStats:
    """缓存统计信息"""

    hits: int = 0
    misses: int = 0
    builds: int = 0
    entries: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total


class ContextCache:
    """三层上下文缓存

    用法:
        cache = ContextCache()

        # 注册构建函数
        cache.register("story_contract", build_story_contract, tier="permanent")
        cache.register("volume_outline", build_volume_outline, tier="volume")

        # 获取缓存（自动构建或返回缓存）
        contract = cache.get_or_build("story_contract")
        outline = cache.get_or_build("volume_outline")

        # 卷切换时失效卷级缓存
        cache.invalidate_tier("volume")

        # 查看统计
        stats = cache.stats
    """

    # 缓存层级定义
    TIERS = ("permanent", "volume", "chapter")

    def __init__(self) -> None:
        self._entries: dict[str, CacheEntry] = {}
        self._builders: dict[str, Callable[[], str]] = {}
        self._tier_map: dict[str, str] = {}  # key → tier
        self._stats = CacheStats()

    def register(
        self,
        key: str,
        builder: Callable[[], str],
        tier: str = "chapter",
    ) -> None:
        """注册缓存 key 及其构建函数

        Args:
            key: 缓存键名
            builder: 构建函数（返回字符串内容）
            tier: 缓存层级 (permanent/volume/chapter)
        """
        if tier not in self.TIERS:
            raise ValueError(f"Invalid tier: {tier}, must be one of {self.TIERS}")
        self._builders[key] = builder
        self._tier_map[key] = tier

    def get_or_build(self, key: str) -> str:
        """获取缓存内容，未命中则构建

        如果缓存存在且哈希未变，直接返回。
        如果缓存不存在或构建函数变更（哈希不匹配），调用构建函数重新生成。

        Returns:
            缓存的内容字符串
        """
        if key not in self._builders:
            raise CacheMissError(f"No builder registered for key: {key}. Call register() first.")

        # 尝试从缓存获取
        entry = self._entries.get(key)
        if entry is not None:
            # 检查内容是否变更（重新构建并比对哈希）
            new_content = self._builders[key]()
            new_hash = self._compute_hash(new_content)

            if new_hash == entry.content_hash:
                # 缓存命中
                entry.touch()
                self._stats.hits += 1
                return entry.content

            # 内容变更，更新缓存
            old_hash = entry.content_hash
            entry.content = new_content
            entry.content_hash = new_hash
            entry.created_at = __import__("time").time()
            entry.touch()
            self._stats.misses += 1
            logger.debug(
                "Cache content changed for key=%r (old_hash=%s, new_hash=%s)",
                key,
                old_hash[:8],
                new_hash[:8],
            )
            return new_content

        # 首次构建
        content = self._builders[key]()
        content_hash = self._compute_hash(content)
        now = __import__("time").time()
        self._entries[key] = CacheEntry(
            key=key,
            content=content,
            content_hash=content_hash,
            created_at=now,
            last_accessed_at=now,
        )
        self._stats.builds += 1
        self._stats.entries = len(self._entries)
        return content

    def invalidate(self, key: str) -> None:
        """失效指定缓存条目"""
        if key in self._entries:
            del self._entries[key]
            self._stats.entries = len(self._entries)

    def invalidate_tier(self, tier: str) -> int:
        """失效指定层级的所有缓存条目

        Args:
            tier: 缓存层级 (permanent/volume/chapter)

        Returns:
            失效的条目数
        """
        if tier not in self.TIERS:
            raise ValueError(f"Invalid tier: {tier}")
        keys_to_remove = [k for k, t in self._tier_map.items() if t == tier]
        for key in keys_to_remove:
            if key in self._entries:
                del self._entries[key]
        self._stats.entries = len(self._entries)
        logger.info("Invalidated tier=%r, removed %d entries", tier, len(keys_to_remove))
        return len(keys_to_remove)

    def has(self, key: str) -> bool:
        """检查缓存是否存在"""
        return key in self._entries

    def clear(self) -> None:
        """清空所有缓存"""
        self._entries.clear()
        self._stats = CacheStats()

    @property
    def stats(self) -> CacheStats:
        """获取缓存统计"""
        self._stats.entries = len(self._entries)
        return self._stats

    @staticmethod
    def _compute_hash(content: str) -> str:
        """计算内容哈希 (SHA-256 前 16 字符)"""
        return hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()[:16]


def build_cache_key(*parts: str) -> str:
    """构建缓存 key 名称

    Args:
        parts: key 组成部分，用 "." 连接

    Returns:
        如 build_cache_key("volume", "v3", "outline") → "volume.v3.outline"
    """
    return ".".join(p.replace(".", "_") for p in parts if p)


def estimate_tokens(text: str, chars_per_token: int = 4) -> int:
    """估算文本的 token 数

    Args:
        text: 文本内容
        chars_per_token: 每 token 字符数（中英文混合约 4 chars/token）

    Returns:
        估算 token 数
    """
    if not text:
        return 0
    # 中英文混合: 英文约 4 chars/token，中文约 2 chars/token
    # 保守估计用 4 chars/token
    return max(1, len(text) // chars_per_token)


__all__ = [
    "ContextCache",
    "CacheEntry",
    "CacheStats",
    "ContextCacheError",
    "CacheMissError",
    "build_cache_key",
    "estimate_tokens",
]
