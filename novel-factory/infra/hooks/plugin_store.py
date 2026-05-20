#!/usr/bin/env python3
"""
Plugin Store - Hook插件注册与管理中心

负责：
- 插件注册/注销
- 插件启用/禁用
- 插件搜索与筛选
- 插件状态统计
- 插件依赖验证
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PluginMetadata:
    """
    插件元数据

    Attributes:
        id: 唯一标识符（英文，推荐使用 kebab-case 或 snake_case）
        name: 显示名称
        version: 版本号（遵循语义化版本规范，如 "1.0.0"）
        description: 插件描述
        author: 作者
        hooks: 该插件提供的钩子名称列表
        actions: 该插件提供的动作类型列表
        dependencies: 该插件依赖的其他插件ID列表
        enabled: 是否启用（默认 True）
        config: 插件特定配置
    """
    id: str
    name: str
    version: str
    description: str
    author: str
    hooks: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """验证必需字段"""
        if not self.id:
            raise ValueError("Plugin id cannot be empty")
        if not self.version:
            raise ValueError("Plugin version cannot be empty")

    def __hash__(self) -> int:
        """支持将 PluginMetadata 用作字典键"""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """基于 id 比较插件是否相同"""
        if not isinstance(other, PluginMetadata):
            return NotImplemented
        return self.id == other.id


class PluginStore:
    """
    插件存储与管理系统

    负责插件的注册、注销、查询、启用/禁用等操作。
    支持插件间的依赖验证，以及基于钩子/动作类型的查询。

    Example:
        >>> store = PluginStore()
        >>> plugin = PluginMetadata(
        ...     id="my-plugin",
        ...     name="My Plugin",
        ...     version="1.0.0",
        ...     description="A sample plugin",
        ...     author="Author",
        ...     hooks=["on_review_complete"],
        ...     actions=["notify"]
        ... )
        >>> store.register_plugin(plugin)
        True
        >>> store.get_plugin("my-plugin")
        PluginMetadata(id='my-plugin', ...)
        >>> store.list_plugins()
        [PluginMetadata(id='my-plugin', ...)]
    """

    def __init__(self) -> None:
        """初始化插件存储"""
        self._plugins: Dict[str, PluginMetadata] = {}

    def register_plugin(self, plugin: PluginMetadata) -> bool:
        """
        注册插件

        Args:
            plugin: 插件元数据

        Returns:
            True 表示注册成功，False 表示该 id 已存在
        """
        if plugin.id in self._plugins:
            return False

        self._plugins[plugin.id] = plugin
        return True

    def unregister_plugin(self, plugin_id: str) -> bool:
        """
        注销插件

        Args:
            plugin_id: 插件ID

        Returns:
            True 表示注销成功，False 表示该插件不存在
        """
        if plugin_id not in self._plugins:
            return False

        del self._plugins[plugin_id]
        return True

    def get_plugin(self, plugin_id: str) -> Optional[PluginMetadata]:
        """
        根据ID获取插件

        Args:
            plugin_id: 插件ID

        Returns:
            插件元数据，不存在则返回 None
        """
        return self._plugins.get(plugin_id)

    def list_plugins(self, include_disabled: bool = False) -> List[PluginMetadata]:
        """
        列出所有插件

        Args:
            include_disabled: 是否包含已禁用的插件（默认只返回已启用的）

        Returns:
            插件列表
        """
        if include_disabled:
            return list(self._plugins.values())

        return [p for p in self._plugins.values() if p.enabled]

    def enable_plugin(self, plugin_id: str) -> bool:
        """
        启用插件

        Args:
            plugin_id: 插件ID

        Returns:
            True 表示启用成功，False 表示插件不存在或依赖未满足
        """
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return False

        # 验证依赖是否满足
        valid, _ = self._validate_dependencies(plugin)
        if not valid:
            return False

        plugin.enabled = True
        return True

    def disable_plugin(self, plugin_id: str) -> bool:
        """
        禁用插件

        Args:
            plugin_id: 插件ID

        Returns:
            True 表示禁用成功，False 表示插件不存在
        """
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return False

        plugin.enabled = False
        return True

    def search_plugins(self, query: str) -> List[PluginMetadata]:
        """
        搜索插件（按名称或描述）

        Args:
            query: 搜索关键词（不区分大小写）

        Returns:
            匹配的插件列表
        """
        query_lower = query.lower()
        results: List[PluginMetadata] = []

        for plugin in self._plugins.values():
            if (query_lower in plugin.name.lower() or
                query_lower in plugin.description.lower()):
                results.append(plugin)

        return results

    def get_plugins_by_hook(self, hook_name: str) -> List[PluginMetadata]:
        """
        获取提供特定钩子的所有插件

        Args:
            hook_name: 钩子名称

        Returns:
            提供该钩子的插件列表（只返回已启用的）
        """
        return [
            p for p in self._plugins.values()
            if p.enabled and hook_name in p.hooks
        ]

    def get_plugins_by_action(self, action_type: str) -> List[PluginMetadata]:
        """
        获取提供特定动作类型的所有插件

        Args:
            action_type: 动作类型

        Returns:
            提供该动作类型的插件列表（只返回已启用的）
        """
        return [
            p for p in self._plugins.values()
            if p.enabled and action_type in p.actions
        ]

    def get_plugin_count(self) -> dict:
        """
        获取插件统计信息

        Returns:
            包含 total、enabled、disabled 数量的字典
        """
        total = len(self._plugins)
        enabled = sum(1 for p in self._plugins.values() if p.enabled)
        disabled = total - enabled

        return {
            "total": total,
            "enabled": enabled,
            "disabled": disabled
        }

    def _validate_dependencies(self, plugin: PluginMetadata) -> tuple[bool, List[str]]:
        """
        验证插件的依赖是否满足

        检查所有依赖的插件是否存在且已启用

        Args:
            plugin: 要验证的插件

        Returns:
            (是否有效, 未满足的依赖ID列表)
        """
        missing: List[str] = []

        for dep_id in plugin.dependencies:
            dep = self._plugins.get(dep_id)
            if not dep:
                missing.append(dep_id)
            elif not dep.enabled:
                missing.append(dep_id)

        return (len(missing) == 0, missing)