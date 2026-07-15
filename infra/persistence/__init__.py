"""Phase 15.0 T2.1: Persistence 子包入口。

设计: 不在 import 时副作用 — caller 显式调 `register_all()` 绑定 storage。
"""
from infra.persistence.registry import (
    RegisteredStorage,
    get,
    is_registered,
    register,
    registered_names,
    reset,
    reset_all,
)

__all__ = [
    "RegisteredStorage",
    "register",
    "get",
    "reset",
    "reset_all",
    "is_registered",
    "registered_names",
]
