# novel-factory/infra/agent_system/agents/shared/__init__.py
"""共享模块 - Agent系统中跨角色共享的组件"""

from .base_variant_loader import BaseVariantLoader, SimpleVariantLoader, create_variant_loader

__all__ = [
    "BaseVariantLoader",
    "SimpleVariantLoader",
    "create_variant_loader",
]