#!/usr/bin/env python3
"""
SQL查询集中管理模块

集中管理所有SQL查询模板，支持：
1. 参数化查询
2. 查询命名空间
3. 查询版本管理
4. 统一查询获取接口

使用方式：
    from infra.persistence.queries import get_query

    # 获取查询
    query = get_query('events.get_by_aggregate')

    # 执行查询
    cursor.execute(query.sql, query.params({'aggregate_id': 'abc'}))
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass(frozen=True)
class Query:
    """
    SQL查询定义

    Args:
        name: 查询名称
        sql: SQL语句模板
        params_schema: 参数验证schema（可选）
        description: 查询描述
        namespace: 命名空间
        version: 查询版本
    """

    name: str
    sql: str
    params_schema: Optional[Dict[str, type]] = None
    description: str = ""
    namespace: str = "default"
    version: int = 1

    def params(self, **kwargs) -> Dict[str, Any]:
        """
        构建查询参数

        Args:
            **kwargs: 参数键值对

        Returns:
            参数字典

        Raises:
            ValueError: 如果参数不符合schema
        """
        if self.params_schema:
            for key, expected_type in self.params_schema.items():
                if key in kwargs:
                    value = kwargs[key]
                    if not isinstance(value, expected_type):
                        raise ValueError(
                            f"Parameter '{key}' expects {expected_type.__name__}, got {type(value).__name__}"
                        )

        return {k: v for k, v in kwargs.items() if v is not None}


class QueryRegistry:
    """
    查询注册表

    管理所有SQL查询，支持按名称和命名空间查找。
    """

    def __init__(self):
        self._queries: Dict[str, Query] = {}
        self._namespaces: Dict[str, List[str]] = {}

    def register(self, query: Query) -> None:
        """
        注册查询

        Args:
            query: 查询对象
        """
        key = self._make_key(query.namespace, query.name)
        self._queries[key] = query

        if query.namespace not in self._namespaces:
            self._namespaces[query.namespace] = []
        if query.name not in self._namespaces[query.namespace]:
            self._namespaces[query.namespace].append(query.name)

    def register_multiple(self, queries: List[Query]) -> None:
        """
        批量注册查询

        Args:
            queries: 查询列表
        """
        for query in queries:
            self.register(query)

    def get(self, name: str, namespace: str = "default") -> Optional[Query]:
        """
        获取查询

        Args:
            name: 查询名称
            namespace: 命名空间

        Returns:
            查询对象或None
        """
        key = self._make_key(namespace, name)
        return self._queries.get(key)

    def get_by_namespace(self, namespace: str) -> List[Query]:
        """
        按命名空间获取所有查询

        Args:
            namespace: 命名空间

        Returns:
            查询列表
        """
        if namespace not in self._namespaces:
            return []

        return [self._queries[self._make_key(namespace, name)] for name in self._namespaces[namespace]]

    def list_namespaces(self) -> List[str]:
        """
        获取所有命名空间

        Returns:
            命名空间列表
        """
        return list(self._namespaces.keys())

    def list_queries(self) -> List[str]:
        """
        获取所有查询名称

        Returns:
            查询名称列表
        """
        return list(self._queries.keys())

    def exists(self, name: str, namespace: str = "default") -> bool:
        """
        检查查询是否存在

        Args:
            name: 查询名称
            namespace: 命名空间

        Returns:
            是否存在
        """
        key = self._make_key(namespace, name)
        return key in self._queries

    def unregister(self, name: str, namespace: str = "default") -> None:
        """
        卸载查询

        Args:
            name: 查询名称
            namespace: 命名空间
        """
        key = self._make_key(namespace, name)
        if key in self._queries:
            del self._queries[key]

            if namespace in self._namespaces and name in self._namespaces[namespace]:
                self._namespaces[namespace].remove(name)
                if not self._namespaces[namespace]:
                    del self._namespaces[namespace]

    def clear(self) -> None:
        """
        清空所有查询
        """
        self._queries.clear()
        self._namespaces.clear()

    def _make_key(self, namespace: str, name: str) -> str:
        """
        生成查询键

        Args:
            namespace: 命名空间
            name: 查询名称

        Returns:
            查询键
        """
        return f"{namespace}.{name}"


# 全局查询注册表
_global_registry = QueryRegistry()


def register_query(query: Query) -> None:
    """
    注册查询（快捷方法）

    Args:
        query: 查询对象
    """
    _global_registry.register(query)


def register_queries(queries: List[Query]) -> None:
    """
    批量注册查询（快捷方法）

    Args:
        queries: 查询列表
    """
    _global_registry.register_multiple(queries)


def get_query(name: str, namespace: str = "default") -> Query:
    """
    获取查询

    Args:
        name: 查询名称
        namespace: 命名空间

    Returns:
        查询对象

    Raises:
        ValueError: 如果查询不存在
    """
    query = _global_registry.get(name, namespace)
    if not query:
        raise ValueError(f"Query '{name}' not found in namespace '{namespace}'")
    return query


def list_queries(namespace: str = None) -> List[Query]:
    """
    列出查询

    Args:
        namespace: 命名空间（可选）

    Returns:
        查询列表
    """
    if namespace:
        return _global_registry.get_by_namespace(namespace)
    return [q for q in _global_registry._queries.values()]


def query_exists(name: str, namespace: str = "default") -> bool:
    """
    检查查询是否存在

    Args:
        name: 查询名称
        namespace: 命名空间

    Returns:
        是否存在
    """
    return _global_registry.exists(name, namespace)


def get_registry() -> QueryRegistry:
    """
    获取全局查询注册表

    Returns:
        查询注册表
    """
    return _global_registry


# 导入查询模块（自动注册）
try:
    from infra.persistence.queries import events
except ImportError:
    pass

__all__ = [
    "Query",
    "QueryRegistry",
    "register_query",
    "register_queries",
    "get_query",
    "list_queries",
    "query_exists",
    "get_registry",
]
