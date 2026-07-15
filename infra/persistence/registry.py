"""Phase 15.0 T2.1: SQLite singleton registry.

集中管理多个 storage 类的 lazy init + thread-safe singleton + test 隔离。

典型用法:
    from infra.persistence.registry import register, get, reset_all
    from infra.persistence.bootstrap import register_all

    register_all()  # 启动时调一次
    storage = get("ripple")
    storage2 = get("ripple")  # 同 instance

测试隔离:
    pytest fixture: `reset_all()` 在每个 test 结束清空。

设计原则:
- 0 改 baseline: 既有的 `RippleStorage(db_path=...)` 直接构造仍可用
- 0 真 LLM: 无外部依赖
- 0 改 .state: db_path 默认值不强制
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


@dataclass
class RegisteredStorage:
    """单条 storage 注册记录."""

    name: str
    cls: Callable[..., Any]
    db_path: Optional[str] = None
    kwargs: Dict[str, Any] = field(default_factory=dict)


# 模块级 registry + instance cache + 守护锁
_registry: Dict[str, RegisteredStorage] = {}
_instances: Dict[str, Any] = {}
_lock = threading.Lock()


def register(
    name: str,
    cls: Callable[..., Any],
    *,
    db_path: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """注册一个 storage 类（lazy，不立即构造）。

    Args:
        name: 注册名（必须唯一）
        cls: storage 类（可调用对象）
        db_path: 默认 db 路径（get 时可被覆盖）
        **kwargs: 透传给 cls() 的其他参数

    Raises:
        TypeError: cls 不可调用
    """
    if not callable(cls):
        raise TypeError(f"cls 必须是可调用对象, got {type(cls).__name__}")
    with _lock:
        _registry[name] = RegisteredStorage(
            name=name, cls=cls, db_path=db_path, kwargs=dict(kwargs)
        )


def get(name: str, *, db_path: Optional[str] = None, **override: Any) -> Any:
    """获取一个 storage singleton（lazy init + thread-safe）。

    优先级: get(override) > register(kwargs) > register(db_path)

    Args:
        name: 注册名
        db_path: 覆盖注册的默认 db_path
        **override: 覆盖注册时的其他 kwargs

    Returns:
        storage instance

    Raises:
        KeyError: name 未注册
    """
    with _lock:
        if name not in _registry:
            raise KeyError(
                f"storage '{name}' 未注册. 已注册: {sorted(_registry.keys())}"
            )
        # 已构造且无 override → 直接返回（singleton）
        if name in _instances and db_path is None and not override:
            return _instances[name]
        # 构造新 instance
        spec = _registry[name]
        init_kwargs = dict(spec.kwargs)
        if spec.db_path is not None:
            init_kwargs.setdefault("db_path", spec.db_path)
        if db_path is not None:
            init_kwargs["db_path"] = db_path
        init_kwargs.update(override)
        instance = spec.cls(**init_kwargs)
        _instances[name] = instance
        return instance


def reset(name: str) -> None:
    """重置单个 storage（下次 get() 重新构造）。"""
    with _lock:
        _instances.pop(name, None)


def reset_all() -> None:
    """重置所有 storage（测试间隔离用）。"""
    with _lock:
        _instances.clear()


def is_registered(name: str) -> bool:
    """检查 name 是否已注册。"""
    with _lock:
        return name in _registry


def registered_names() -> list[str]:
    """返回所有已注册 storage 名（按字母排序）。"""
    with _lock:
        return sorted(_registry.keys())


__all__ = [
    "RegisteredStorage",
    "register",
    "get",
    "reset",
    "reset_all",
    "is_registered",
    "registered_names",
]
