# novel-factory/infra/agent_system/agents/loaders/__init__.py
"""变体加载器模块 - 各角色池的 variant loader 集合"""

from .base_variant_loader import BaseVariantLoader, SimpleVariantLoader, create_variant_loader

__all__ = [
    "BaseVariantLoader",
    "SimpleVariantLoader",
    "create_variant_loader",
]