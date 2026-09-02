#!/usr/bin/env python3
"""
AI Provider 插件管理器

支持：
1. 自动发现项目内的 provider 模块
2. 动态加载外部 provider 插件
3. Provider 配置和优先级管理
"""

import importlib
import logging
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from .base import AIProvider, ProviderConfig, register_provider

logger = logging.getLogger(__name__)


@dataclass
class PluginInfo:
    """插件信息"""

    name: str
    module_path: str
    provider_class: Type[AIProvider]
    config_schema: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


class PluginManager:
    """
    Provider 插件管理器

    负责发现、加载和管理所有 AI Provider 插件。
    """

    _instance: Optional["PluginManager"] = None

    def __init__(self):
        self._plugins: Dict[str, PluginInfo] = {}
        self._provider_priority: List[str] = []
        self._loaded = False

    def _discover_internal_providers(self) -> None:
        """发现项目内的 provider 模块"""
        ai_service_dir = os.path.dirname(__file__)
        providers_dir = os.path.join(ai_service_dir, "providers")

        if not os.path.exists(providers_dir):
            os.makedirs(providers_dir, exist_ok=True)

        for filename in os.listdir(ai_service_dir):
            if filename.endswith("_provider.py") and filename != "__init__.py":
                module_name = filename[:-3]
                module_path = f"lingwen_llm.providers.{module_name}"
                try:
                    module = importlib.import_module(module_path)
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and issubclass(attr, AIProvider) and attr != AIProvider:
                            provider_name = attr_name.replace("Provider", "").lower()
                            self._plugins[provider_name] = PluginInfo(
                                name=provider_name,
                                module_path=module_path,
                                provider_class=attr,
                            )
                            logger.debug(f"Discovered internal provider: {provider_name}")
                except Exception as e:
                    logger.warning(f"Failed to load internal provider module {module_name}: {e}")

        for filename in os.listdir(providers_dir):
            if filename.endswith("_provider.py"):
                module_name = filename[:-3]
                module_path = f"lingwen_llm.providers.{module_name}"
                try:
                    module = importlib.import_module(module_path)
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and issubclass(attr, AIProvider) and attr != AIProvider:
                            provider_name = attr_name.replace("Provider", "").lower()
                            self._plugins[provider_name] = PluginInfo(
                                name=provider_name,
                                module_path=module_path,
                                provider_class=attr,
                            )
                            logger.debug(f"Discovered plugin provider: {provider_name}")
                except Exception as e:
                    logger.warning(f"Failed to load plugin provider module {module_name}: {e}")

    def _discover_external_plugins(self, plugin_dirs: Optional[List[str]] = None) -> None:
        """发现外部插件目录中的 provider"""
        if not plugin_dirs:
            plugin_dirs = []

        env_plugin_dirs = os.environ.get("AI_SERVICE_PLUGIN_DIRS", "")
        if env_plugin_dirs:
            plugin_dirs.extend(env_plugin_dirs.split(":"))

        for plugin_dir in plugin_dirs:
            if not os.path.isabs(plugin_dir):
                plugin_dir = os.path.abspath(plugin_dir)

            if not os.path.exists(plugin_dir):
                continue

            if plugin_dir not in sys.path:
                sys.path.insert(0, plugin_dir)

            for filename in os.listdir(plugin_dir):
                if filename.endswith("_provider.py"):
                    module_name = filename[:-3]
                    try:
                        module = importlib.import_module(module_name)
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if isinstance(attr, type) and issubclass(attr, AIProvider) and attr != AIProvider:
                                provider_name = attr_name.replace("Provider", "").lower()
                                self._plugins[provider_name] = PluginInfo(
                                    name=provider_name,
                                    module_path=module_name,
                                    provider_class=attr,
                                )
                                logger.info(f"Discovered external plugin: {provider_name}")
                    except Exception as e:
                        logger.warning(f"Failed to load external plugin {module_name}: {e}")

    def load_plugins(self, plugin_dirs: Optional[List[str]] = None) -> None:
        """加载所有插件"""
        if self._loaded:
            return

        self._discover_internal_providers()
        self._discover_external_plugins(plugin_dirs)

        default_priority = ["minimax", "anthropic", "openai"]
        self._provider_priority = [p for p in default_priority if p in self._plugins] + [
            p for p in self._plugins if p not in default_priority
        ]

        self._loaded = True
        logger.info(f"Loaded {len(self._plugins)} providers: {list(self._plugins.keys())}")

    def get_plugin(self, name: str) -> Optional[PluginInfo]:
        """获取插件信息"""
        if not self._loaded:
            self.load_plugins()
        return self._plugins.get(name.lower())

    def get_provider_class(self, name: str) -> Optional[Type[AIProvider]]:
        """获取 provider 类"""
        plugin = self.get_plugin(name)
        return plugin.provider_class if plugin else None

    def create_provider(self, name: str, config: ProviderConfig) -> AIProvider:
        """创建 provider 实例"""
        provider_class = self.get_provider_class(name)
        if not provider_class:
            raise ValueError(f"Provider '{name}' not found. Available: {list(self._plugins.keys())}")
        return provider_class(config)

    def list_providers(self) -> List[str]:
        """列出所有可用的 provider"""
        if not self._loaded:
            self.load_plugins()
        return list(self._plugins.keys())

    def get_priority(self) -> List[str]:
        """获取 provider 优先级列表"""
        if not self._loaded:
            self.load_plugins()
        return self._provider_priority.copy()

    def set_priority(self, priorities: List[str]) -> None:
        """设置 provider 优先级"""
        if not self._loaded:
            self.load_plugins()

        valid_providers = [p for p in priorities if p in self._plugins]
        remaining = [p for p in self._plugins if p not in valid_providers]
        self._provider_priority = valid_providers + remaining

    def enable_provider(self, name: str) -> None:
        """启用 provider"""
        plugin = self.get_plugin(name)
        if plugin:
            plugin.enabled = True

    def disable_provider(self, name: str) -> None:
        """禁用 provider"""
        plugin = self.get_plugin(name)
        if plugin:
            plugin.enabled = False

    def get_enabled_providers(self) -> List[str]:
        """获取已启用的 provider"""
        if not self._loaded:
            self.load_plugins()
        return [p for p, info in self._plugins.items() if info.enabled]

    @classmethod
    def get(cls) -> "PluginManager":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def get_plugin_manager() -> PluginManager:
    """获取插件管理器实例"""
    return PluginManager.get()


def discover_and_register() -> None:
    """发现并注册所有 provider（在应用启动时调用）"""
    manager = PluginManager.get()
    manager.load_plugins()

    for name, plugin in manager._plugins.items():
        register_provider(name)(plugin.provider_class)
