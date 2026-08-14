"""灵文配置模块

提供统一的配置加载机制。

核心导出:
- APIConfig — API 配置加载器（单例）
"""

from infra.config.api_config_loader import APIConfig

__all__ = [
    "APIConfig",
]