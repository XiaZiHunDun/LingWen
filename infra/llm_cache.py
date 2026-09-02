#!/usr/bin/env python3
"""
LLM 缓存策略系统

参考 opencode 的 llm/src/cache-policy.ts，实现智能缓存机制。

核心功能：
1. CacheHint 标记缓存断点
2. 多种缓存策略（auto、full、none 等）
3. 不同粒度的缓存（工具、系统消息、用户消息）
4. TTL 缓存过期
5. 缓存存储抽象
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from infra.errors import BaseError


class CacheError(BaseError):
    """缓存错误"""

    __error_name__ = "CacheError"
    __error_tags__ = ["cache"]


class CacheMissError(CacheError):
    """缓存未命中"""

    __error_name__ = "CacheMissError"
    __error_tags__ = ["cache", "miss"]


class CacheExpiredError(CacheError):
    """缓存过期"""

    __error_name__ = "CacheExpiredError"
    __error_tags__ = ["cache", "expired"]


@dataclass(frozen=True)
class CacheHint:
    """
    缓存提示

    参考 opencode 的 CacheHint，标记缓存断点。

    Args:
        ttl_seconds: TTL 秒数
        key: 缓存键
        tags: 标签
    """

    ttl_seconds: int = 3600  # 默认 1 小时
    key: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "ttl_seconds": self.ttl_seconds,
            "key": self.key,
            "tags": self.tags,
        }


class MessageRole:
    """消息角色"""

    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"
    TOOL = "tool"


class CachePolicyObject:
    """
    缓存策略对象

    Args:
        tools: 是否缓存工具定义
        system: 是否缓存系统消息
        messages: 消息缓存模式（none/latest-user-message/all）
    """

    def __init__(
        self,
        tools: bool = False,
        system: bool = False,
        messages: str = "none",
    ):
        self.tools = tools
        self.system = system
        self.messages = messages

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "tools": self.tools,
            "system": self.system,
            "messages": self.messages,
        }


class CachePolicy:
    """
    缓存策略

    参考 opencode 的缓存策略，支持多种预设策略。
    """

    # 默认策略：缓存工具 + 系统 + 最新用户消息
    AUTO = CachePolicyObject(
        tools=True,
        system=True,
        messages="latest-user-message",
    )

    # 完整缓存
    FULL = CachePolicyObject(
        tools=True,
        system=True,
        messages="all",
    )

    # 无缓存
    NONE = CachePolicyObject(
        tools=False,
        system=False,
        messages="none",
    )

    # 仅工具缓存
    TOOLS_ONLY = CachePolicyObject(
        tools=True,
        system=False,
        messages="none",
    )

    # 仅系统消息缓存
    SYSTEM_ONLY = CachePolicyObject(
        tools=False,
        system=True,
        messages="none",
    )

    @staticmethod
    def resolve(policy: Union[str, CachePolicyObject]) -> CachePolicyObject:
        """
        解析缓存策略

        Args:
            policy: 策略名称或策略对象

        Returns:
            缓存策略对象
        """
        if isinstance(policy, CachePolicyObject):
            return policy

        policy_map = {
            "auto": CachePolicy.AUTO,
            "full": CachePolicy.FULL,
            "none": CachePolicy.NONE,
            "tools-only": CachePolicy.TOOLS_ONLY,
            "system-only": CachePolicy.SYSTEM_ONLY,
        }

        return policy_map.get(policy, CachePolicy.AUTO)


class CacheEntry:
    """
    缓存条目

    Args:
        key: 缓存键
        value: 缓存值
        hint: 缓存提示
        created_at: 创建时间
        accessed_at: 最后访问时间
    """

    def __init__(self, key: str, value: Any, hint: CacheHint):
        self.key = key
        self.value = value
        self.hint = hint
        self.created_at = time.time()
        self.accessed_at = time.time()

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.hint.ttl_seconds <= 0:
            return False
        return time.time() - self.created_at > self.hint.ttl_seconds

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "key": self.key,
            "value": self.value,
            "hint": self.hint.to_dict(),
            "created_at": self.created_at,
            "accessed_at": self.accessed_at,
        }


class CacheStorage:
    """
    缓存存储抽象

    参考 opencode 的缓存存储，支持不同的后端实现。
    """

    def get(self, key: str) -> Optional[CacheEntry]:
        """获取缓存"""
        raise NotImplementedError

    def set(self, key: str, value: Any, hint: CacheHint) -> None:
        """设置缓存"""
        raise NotImplementedError

    def delete(self, key: str) -> None:
        """删除缓存"""
        raise NotImplementedError

    def clear(self) -> None:
        """清空所有缓存"""
        raise NotImplementedError

    def keys(self) -> List[str]:
        """获取所有缓存键"""
        raise NotImplementedError

    def prune(self) -> int:
        """清理过期缓存"""
        raise NotImplementedError


class MemoryCacheStorage(CacheStorage):
    """
    内存缓存存储

    简单的内存实现，用于测试和开发。
    """

    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size

    def get(self, key: str) -> Optional[CacheEntry]:
        """获取缓存"""
        entry = self._cache.get(key)
        if entry:
            if entry.is_expired():
                del self._cache[key]
                return None
            entry.accessed_at = time.time()
        return entry

    def set(self, key: str, value: Any, hint: CacheHint) -> None:
        """设置缓存"""
        # 检查大小限制
        if len(self._cache) >= self._max_size:
            # 删除最旧的条目
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
            del self._cache[oldest_key]

        self._cache[key] = CacheEntry(key, value, hint)

    def delete(self, key: str) -> None:
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()

    def keys(self) -> List[str]:
        """获取所有缓存键"""
        return list(self._cache.keys())

    def prune(self) -> int:
        """清理过期缓存"""
        count = 0
        keys_to_remove = []
        for key, entry in self._cache.items():
            if entry.is_expired():
                keys_to_remove.append(key)
                count += 1

        for key in keys_to_remove:
            del self._cache[key]

        return count


class FileCacheStorage(CacheStorage):
    """
    文件缓存存储

    将缓存持久化到文件系统。
    """

    def __init__(self, cache_dir: str = "./cache"):
        self._cache_dir = cache_dir
        import os

        os.makedirs(cache_dir, exist_ok=True)

    def _key_to_path(self, key: str) -> str:
        """将键转换为文件路径"""
        import os

        hash_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self._cache_dir, f"{hash_key}.json")

    def get(self, key: str) -> Optional[CacheEntry]:
        """获取缓存"""
        import os

        path = self._key_to_path(key)
        if not os.path.exists(path):
            return None

        try:
            with open(path, "r") as f:
                data = json.load(f)
                hint = CacheHint(**data["hint"])
                entry = CacheEntry(data["key"], data["value"], hint)
                entry.created_at = data["created_at"]
                entry.accessed_at = data["accessed_at"]

                if entry.is_expired():
                    os.remove(path)
                    return None

                entry.accessed_at = time.time()
                self._save_entry(entry)
                return entry
        except Exception:
            return None

    def set(self, key: str, value: Any, hint: CacheHint) -> None:
        """设置缓存"""
        entry = CacheEntry(key, value, hint)
        self._save_entry(entry)

    def _save_entry(self, entry: CacheEntry) -> None:
        """保存条目到文件"""
        path = self._key_to_path(entry.key)
        with open(path, "w") as f:
            json.dump(entry.to_dict(), f)

    def delete(self, key: str) -> None:
        """删除缓存"""
        import os

        path = self._key_to_path(key)
        if os.path.exists(path):
            os.remove(path)

    def clear(self) -> None:
        """清空所有缓存"""
        import os

        for filename in os.listdir(self._cache_dir):
            if filename.endswith(".json"):
                os.remove(os.path.join(self._cache_dir, filename))

    def keys(self) -> List[str]:
        """获取所有缓存键"""
        keys = []
        import os

        for filename in os.listdir(self._cache_dir):
            if filename.endswith(".json"):
                path = os.path.join(self._cache_dir, filename)
                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                        keys.append(data["key"])
                except Exception:
                    pass
        return keys

    def prune(self) -> int:
        """清理过期缓存"""
        count = 0
        import os

        for filename in os.listdir(self._cache_dir):
            if filename.endswith(".json"):
                path = os.path.join(self._cache_dir, filename)
                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                        hint = CacheHint(**data["hint"])
                        created_at = data["created_at"]
                        if hint.ttl_seconds > 0 and time.time() - created_at > hint.ttl_seconds:
                            os.remove(path)
                            count += 1
                except Exception:
                    pass
        return count


class LLMCache:
    """
    LLM 缓存系统

    参考 opencode 的缓存策略，提供智能缓存功能。

    Args:
        storage: 缓存存储
        default_policy: 默认缓存策略
    """

    def __init__(
        self,
        storage: Optional[CacheStorage] = None,
        default_policy: Union[str, CachePolicyObject] = "auto",
    ):
        self._storage = storage or MemoryCacheStorage()
        self._default_policy = CachePolicy.resolve(default_policy)

    def make_key(self, *parts: Any) -> str:
        """
        生成缓存键

        Args:
            parts: 键的组成部分

        Returns:
            缓存键
        """
        data = json.dumps(parts, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值或 None
        """
        entry = self._storage.get(key)
        if entry:
            return entry.value
        return None

    def set(self, key: str, value: Any, hint: Optional[CacheHint] = None) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            hint: 缓存提示
        """
        self._storage.set(key, value, hint or CacheHint())

    def delete(self, key: str) -> None:
        """
        删除缓存

        Args:
            key: 缓存键
        """
        self._storage.delete(key)

    def clear(self) -> None:
        """清空所有缓存"""
        self._storage.clear()

    def prune(self) -> int:
        """清理过期缓存"""
        return self._storage.prune()

    def cache_request(
        self,
        request: Dict[str, Any],
        policy: Optional[Union[str, CachePolicyObject]] = None,
    ) -> Tuple[str, bool]:
        """
        缓存请求并返回缓存键和是否命中

        Args:
            request: LLM 请求
            policy: 缓存策略

        Returns:
            (缓存键, 是否命中)
        """
        resolved_policy = CachePolicy.resolve(policy or self._default_policy)

        # 构建缓存键
        cache_parts = []
        if resolved_policy.tools and "tools" in request:
            cache_parts.append(("tools", request["tools"]))
        if resolved_policy.system and "system" in request:
            cache_parts.append(("system", request["system"]))
        if resolved_policy.messages != "none" and "messages" in request:
            messages = request["messages"]
            if resolved_policy.messages == "latest-user-message":
                # 只取最新的用户消息
                latest_user = None
                for msg in reversed(messages):
                    if msg.get("role") == MessageRole.USER:
                        latest_user = msg
                        break
                if latest_user:
                    cache_parts.append(("messages", [latest_user]))
            else:
                # 全部消息
                cache_parts.append(("messages", messages))

        if "model" in request:
            cache_parts.append(("model", request["model"]))

        key = self.make_key(*cache_parts)

        # 检查缓存
        cached_value = self.get(key)
        if cached_value is not None:
            return key, True

        return key, False

    def wrap_request(
        self,
        request: Dict[str, Any],
        func: Callable[[Dict[str, Any]], Any],
        policy: Optional[Union[str, CachePolicyObject]] = None,
    ) -> Any:
        """
        包装请求，自动处理缓存

        Args:
            request: LLM 请求
            func: 请求函数
            policy: 缓存策略

        Returns:
            请求结果（可能来自缓存）
        """
        key, hit = self.cache_request(request, policy)

        if hit:
            return self.get(key)

        # 执行请求
        result = func(request)

        # 缓存结果
        self.set(key, result)

        return result


class CacheHintMarker:
    """
    缓存提示标记器

    参考 opencode 的 markLastTool、markLastSystem、markMessages 等函数。
    """

    @staticmethod
    def mark_tool(tools: List[Dict[str, Any]], hint: CacheHint) -> List[Dict[str, Any]]:
        """
        标记工具定义

        Args:
            tools: 工具列表
            hint: 缓存提示

        Returns:
            标记后的工具列表
        """
        if not tools:
            return tools

        # 标记最后一个工具
        marked_tools = []
        for i, tool in enumerate(tools):
            if i == len(tools) - 1:
                marked_tools.append({**tool, "_cache_hint": hint.to_dict()})
            else:
                marked_tools.append(tool)

        return marked_tools

    @staticmethod
    def mark_system(system: Dict[str, Any], hint: CacheHint) -> Dict[str, Any]:
        """
        标记系统消息

        Args:
            system: 系统消息
            hint: 缓存提示

        Returns:
            标记后的系统消息
        """
        if not system:
            return system
        return {**system, "_cache_hint": hint.to_dict()}

    @staticmethod
    def mark_messages(
        messages: List[Dict[str, Any]],
        mode: str = "latest-user-message",
        hint: Optional[CacheHint] = None,
    ) -> List[Dict[str, Any]]:
        """
        标记消息

        Args:
            messages: 消息列表
            mode: 标记模式
            hint: 缓存提示

        Returns:
            标记后的消息列表
        """
        if not messages:
            return messages

        hint = hint or CacheHint()

        if mode == "latest-user-message":
            # 标记最新的用户消息
            marked_messages = []
            found = False
            for msg in reversed(messages):
                if not found and msg.get("role") == MessageRole.USER:
                    marked_messages.insert(0, {**msg, "_cache_hint": hint.to_dict()})
                    found = True
                else:
                    marked_messages.insert(0, msg)
            return marked_messages

        elif mode == "all":
            # 标记所有消息
            return [{**msg, "_cache_hint": hint.to_dict()} for msg in messages]

        else:
            return messages


def apply_cache_policy(
    request: Dict[str, Any],
    policy: Union[str, CachePolicyObject] = "auto",
) -> Dict[str, Any]:
    """
    应用缓存策略

    参考 opencode 的 applyCachePolicy 函数。

    Args:
        request: LLM 请求
        policy: 缓存策略

    Returns:
        应用策略后的请求
    """
    resolved_policy = CachePolicy.resolve(policy)
    hint = CacheHint()

    if not resolved_policy.tools and not resolved_policy.system and resolved_policy.messages == "none":
        return request

    new_request = dict(request)

    if resolved_policy.tools and "tools" in request:
        new_request["tools"] = CacheHintMarker.mark_tool(request["tools"], hint)

    if resolved_policy.system and "system" in request:
        new_request["system"] = CacheHintMarker.mark_system(request["system"], hint)

    if resolved_policy.messages != "none" and "messages" in request:
        new_request["messages"] = CacheHintMarker.mark_messages(
            request["messages"],
            resolved_policy.messages,
            hint,
        )

    return new_request


class NamespacedStorage(CacheStorage):
    """
    命名空间存储包装器

    在键中添加命名空间前缀，实现不同命名空间的数据隔离。
    """

    def __init__(self, namespace: str, storage: CacheStorage):
        self._namespace = namespace
        self._storage = storage

    def _prefix_key(self, key: str) -> str:
        """为键添加命名空间前缀"""
        return f"{self._namespace}:{key}"

    def get(self, key: str) -> Optional[CacheEntry]:
        """获取缓存"""
        return self._storage.get(self._prefix_key(key))

    def set(self, key: str, value: Any, hint: CacheHint) -> None:
        """设置缓存"""
        self._storage.set(self._prefix_key(key), value, hint)

    def delete(self, key: str) -> None:
        """删除缓存"""
        self._storage.delete(self._prefix_key(key))

    def clear(self) -> None:
        """清空所有缓存（仅当前命名空间）"""
        # 需要遍历所有键并删除属于当前命名空间的
        for key in self._storage.keys():
            if key.startswith(f"{self._namespace}:"):
                self._storage.delete(key)

    def keys(self) -> List[str]:
        """获取所有缓存键"""
        return [k for k in self._storage.keys() if k.startswith(f"{self._namespace}:")]

    def prune(self) -> int:
        """清理过期缓存"""
        # 需要检查当前命名空间的键是否过期
        count = 0
        for key in list(self.keys()):
            entry = self._storage.get(key)
            if entry and entry.is_expired():
                self._storage.delete(key)
                count += 1
        return count


class UnifiedCacheManager:
    """
    统一缓存管理器

    整合多个缓存实现，支持命名空间，提供统一的缓存接口。

    命名空间示例：
    - llm: LLM 请求缓存
    - checker: 检测结果缓存
    - cross_volume: 跨卷缓存
    - api: API 响应缓存

    Example:
        cache = UnifiedCacheManager()
        llm_cache = cache.namespace('llm')
        checker_cache = cache.namespace('checker')
    """

    def __init__(self, default_storage: Optional[CacheStorage] = None):
        self._default_storage = default_storage or MemoryCacheStorage()
        self._namespaces: Dict[str, LLMCache] = {}

    def namespace(self, name: str) -> LLMCache:
        """
        获取或创建命名空间缓存

        Args:
            name: 命名空间名称

        Returns:
            命名空间对应的缓存实例
        """
        if name not in self._namespaces:
            # 为每个命名空间创建独立的存储包装器
            storage = NamespacedStorage(name, self._default_storage)
            self._namespaces[name] = LLMCache(storage=storage)
        return self._namespaces[name]

    def get(self, namespace: str, key: str) -> Optional[Any]:
        """
        获取缓存值（快捷方法）

        Args:
            namespace: 命名空间
            key: 缓存键

        Returns:
            缓存值或 None
        """
        return self.namespace(namespace).get(key)

    def set(self, namespace: str, key: str, value: Any, hint: Optional[CacheHint] = None) -> None:
        """
        设置缓存值（快捷方法）

        Args:
            namespace: 命名空间
            key: 缓存键
            value: 缓存值
            hint: 缓存提示
        """
        self.namespace(namespace).set(key, value, hint)

    def delete(self, namespace: str, key: str) -> None:
        """
        删除缓存（快捷方法）

        Args:
            namespace: 命名空间
            key: 缓存键
        """
        self.namespace(namespace).delete(key)

    def clear(self, namespace: str = None) -> None:
        """
        清空缓存

        Args:
            namespace: 命名空间（None 表示清空所有）
        """
        if namespace:
            self.namespace(namespace).clear()
        else:
            for cache in self._namespaces.values():
                cache.clear()
            self._namespaces.clear()

    def prune(self, namespace: str = None) -> int:
        """
        清理过期缓存

        Args:
            namespace: 命名空间（None 表示清理所有）

        Returns:
            清理的缓存数量
        """
        if namespace:
            return self.namespace(namespace).prune()
        else:
            total = 0
            for cache in self._namespaces.values():
                total += cache.prune()
            return total

    def list_namespaces(self) -> List[str]:
        """
        获取所有命名空间

        Returns:
            命名空间列表
        """
        return list(self._namespaces.keys())


# 全局缓存管理器实例
_global_cache_manager = UnifiedCacheManager()


def get_cache(namespace: str = "default") -> LLMCache:
    """
    获取指定命名空间的缓存实例

    Args:
        namespace: 命名空间名称

    Returns:
        缓存实例
    """
    return _global_cache_manager.namespace(namespace)


def get_cache_manager() -> UnifiedCacheManager:
    """
    获取全局缓存管理器

    Returns:
        缓存管理器实例
    """
    return _global_cache_manager


__all__ = [
    "CacheHint",
    "CachePolicy",
    "CachePolicyObject",
    "CacheEntry",
    "CacheStorage",
    "MemoryCacheStorage",
    "FileCacheStorage",
    "LLMCache",
    "CacheHintMarker",
    "apply_cache_policy",
    "MessageRole",
    "CacheError",
    "CacheMissError",
    "CacheExpiredError",
    "UnifiedCacheManager",
    "get_cache",
    "get_cache_manager",
]
