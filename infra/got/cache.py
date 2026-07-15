"""灵文 GoT · ThoughtCache

Phase 1.4 — Doc 4 (GoT 适配设计 v1.0) §4: 节点输出缓存。

设计原则 (per Doc 4):
- hash_inputs(inputs): SHA-256(json.dumps(inputs, sort_keys=True))[:16]
  - sort_keys=True → key 顺序无关
- get_or_compute(node_id, inputs_hash, compute_fn):
  - 命中 → 返回缓存
  - 未命中 → 调 compute_fn 存结果 → 返回
- clear(): 清空缓存 (测试用)
- size(): 缓存条目数
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Optional


class ThoughtCache:
    """GoT 节点输出缓存 (in-memory)

    简化实现: dict[(node_id, inputs_hash), output]
    """

    def __init__(self, store: Optional[dict[tuple[str, str], Any]] = None) -> None:
        self._store: dict[tuple[str, str], Any] = store if store is not None else {}

    def hash_inputs(self, inputs: Any) -> str:
        """计算 inputs 的稳定 hash (16 字符)

        算法: SHA-256(json.dumps(inputs, sort_keys=True, ensure_ascii=False))[:16]
        """
        encoded = json.dumps(inputs, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]

    def get_or_compute(
        self,
        node_id: str,
        inputs_hash: str,
        compute_fn: Callable[[], Any],
    ) -> Any:
        """命中返回缓存,未命中调 compute_fn 存结果"""
        key = (node_id, inputs_hash)
        if key in self._store:
            return self._store[key]
        value = compute_fn()
        self._store[key] = value
        return value

    def clear(self) -> None:
        """清空缓存"""
        self._store.clear()

    def size(self) -> int:
        """缓存条目数"""
        return len(self._store)

    def has(self, node_id: str, inputs_hash: str) -> bool:
        """查询是否缓存"""
        return (node_id, inputs_hash) in self._store


__all__ = ["ThoughtCache"]
