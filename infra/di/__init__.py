"""依赖注入模块（DI）

灵感来自 ZIO Layer，提供类型安全的依赖管理系统。

核心功能：
1. Layer 依赖层定义
2. Runtime 运行时组装
3. Tag 类型标签
4. 模块化依赖注册
"""

from .layer import (
    Layer,
    Runtime,
    Tag,
    get_runtime,
    make,
    make_with_deps,
    provide,
    reset_runtime,
)

__all__ = [
    "Layer",
    "Runtime",
    "Tag",
    "get_runtime",
    "make",
    "make_with_deps",
    "provide",
    "reset_runtime",
]
