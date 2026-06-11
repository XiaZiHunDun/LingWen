"""Phase 9.42 F31: query_impact LRU + TTL cache for CVG reference graph."""
from __future__ import annotations

import logging
import time
from collections import OrderedDict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DEFAULT_MAXSIZE = 100
DEFAULT_TTL_SECONDS = 60.0


@dataclass
class _CacheEntry:
    value: tuple[str, ...]
    expires_at: float


class QueryImpactCache:
    """LRU cache with TTL for query_impact(node_id, from_volume) results."""

    def __init__(
        self,
        maxsize: int = DEFAULT_MAXSIZE,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
    ) -> None:
        self._maxsize = maxsize
        self._ttl = ttl_seconds
        self._store: OrderedDict[str, _CacheEntry] = OrderedDict()
        self.hits = 0
        self.misses = 0

    @staticmethod
    def make_key(node_id: str, from_volume: int) -> str:
        return f"{node_id}:{from_volume}"

    def get(self, key: str) -> tuple[str, ...] | None:
        entry = self._store.get(key)
        if entry is None:
            self.misses += 1
            return None
        if entry.expires_at <= time.monotonic():
            del self._store[key]
            self.misses += 1
            return None
        self._store.move_to_end(key)
        self.hits += 1
        return entry.value

    def set(self, key: str, edge_ids: tuple[str, ...]) -> None:
        if key in self._store:
            del self._store[key]
        while len(self._store) >= self._maxsize:
            self._store.popitem(last=False)
        self._store[key] = _CacheEntry(
            value=edge_ids,
            expires_at=time.monotonic() + self._ttl,
        )

    def invalidate(self) -> None:
        if self._store:
            logger.debug("QueryImpactCache invalidate (%d entries)", len(self._store))
        self._store.clear()

    def stats(self) -> dict[str, int]:
        return {"hits": self.hits, "misses": self.misses, "size": len(self._store)}
