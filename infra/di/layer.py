#!/usr/bin/env python3
"""
依赖注入 Layer 系统

灵感来自 ZIO Layer，支持：
1. 模块化依赖定义
2. Layer 组合（flatMap, zip）
3. 运行时依赖组装
4. 测试时依赖替换
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


@dataclass(frozen=True)
class Tag(Generic[T]):
    """类型标签，用于依赖查找"""
    type: Type[T]
    name: str = ""

    def __post_init__(self):
        if not self.name:
            object.__setattr__(self, 'name', self.type.__name__)

    def __hash__(self):
        return hash((self.type, self.name))

    def __eq__(self, other):
        if not isinstance(other, Tag):
            return False
        return self.type == other.type and self.name == other.name


class Layer:
    """
    依赖层，描述如何创建一组依赖

    Layer 可以：
    1. 独立创建（make）
    2. 组合（zip）
    3. 转换（flatMap）
    """

    def __init__(self, provides: List[Tag], dependencies: List[Tag], build: Callable[[Dict[Tag, Any]], Dict[Tag, Any]]):
        self._provides = provides
        self._dependencies = dependencies
        self._build = build

    @property
    def provides(self) -> List[Tag]:
        """该层提供的依赖"""
        return self._provides

    @property
    def dependencies(self) -> List[Tag]:
        """该层依赖的其他依赖"""
        return self._dependencies

    def build(self, env: Dict[Tag, Any]) -> Dict[Tag, Any]:
        """构建该层的依赖"""
        missing = [d for d in self.dependencies if d not in env]
        if missing:
            raise RuntimeError(f"Missing dependencies: {missing}")
        return self._build(env)

    def zip(self, other: 'Layer') -> 'Layer':
        """与另一层组合"""
        provides = self.provides + other.provides
        dependencies = list(set(self.dependencies + other.dependencies))

        def build(env: Dict[Tag, Any]) -> Dict[Tag, Any]:
            result = {}
            result.update(self.build(env))
            result.update(other.build(env))
            return result

        return Layer(provides, dependencies, build)

    def flat_map(self, f: Callable[['Layer'], 'Layer']) -> 'Layer':
        """转换并组合"""
        other = f(self)
        provides = other.provides
        dependencies = list(set(self.dependencies + other.dependencies))

        def build(env: Dict[Tag, Any]) -> Dict[Tag, Any]:
            self_result = self.build(env)
            combined_env = {**env, **self_result}
            return other.build(combined_env)

        return Layer(provides, dependencies, build)

    def map(self, f: Callable[[Dict[Tag, Any]], Dict[Tag, Any]]) -> 'Layer':
        """转换输出"""
        def build(env: Dict[Tag, Any]) -> Dict[Tag, Any]:
            return f(self.build(env))
        return Layer(self.provides, self.dependencies, build)

    @classmethod
    def succeed(cls, **kwargs: Any) -> 'Layer':
        """创建成功层（无依赖）"""
        provides = [Tag(type(v), k) for k, v in kwargs.items()]
        dependencies = []

        def build(env: Dict[Tag, Any]) -> Dict[Tag, Any]:
            return {Tag(type(v), k): v for k, v in kwargs.items()}

        return cls(provides, dependencies, build)

    @classmethod
    def from_service(cls, tag: Tag[T], build: Callable[[Dict[Tag, Any]], T]) -> 'Layer':
        """从服务构建层"""
        dependencies = []

        def _build(env: Dict[Tag, Any]) -> Dict[Tag, Any]:
            return {tag: build(env)}

        return cls([tag], dependencies, _build)

    @classmethod
    def from_service_with_deps(cls, tag: Tag[T], deps: List[Tag], build: Callable[[Dict[Tag, Any]], T]) -> 'Layer':
        """从服务构建层（带依赖）"""
        def _build(env: Dict[Tag, Any]) -> Dict[Tag, Any]:
            return {tag: build(env)}

        return cls([tag], deps, _build)

    def __and__(self, other: 'Layer') -> 'Layer':
        """使用 & 操作符合并层"""
        return self.zip(other)


class Runtime:
    """
    依赖运行时

    负责组装和管理所有依赖
    """

    def __init__(self):
        self._layers: List[Layer] = []
        self._env: Dict[Tag, Any] = {}
        self._loaded = False

    def add_layer(self, layer: Layer) -> 'Runtime':
        """添加层"""
        self._layers.append(layer)
        self._loaded = False
        return self

    def add_layers(self, *layers: Layer) -> 'Runtime':
        """添加多个层"""
        for layer in layers:
            self.add_layer(layer)
        return self

    def load(self) -> 'Runtime':
        """加载所有层"""
        if self._loaded:
            return self

        self._env = {}
        for layer in self._layers:
            result = layer.build(self._env)
            self._env.update(result)

        self._loaded = True
        logger.info(f"Loaded {len(self._env)} dependencies")
        return self

    def get(self, tag: Tag[T]) -> T:
        """获取依赖"""
        if not self._loaded:
            self.load()

        if tag not in self._env:
            raise RuntimeError(f"Dependency not found: {tag}")

        return self._env[tag]

    def get_by_type(self, type_: Type[T]) -> T:
        """按类型获取依赖（返回第一个匹配）"""
        if not self._loaded:
            self.load()

        for tag, value in self._env.items():
            if isinstance(value, type_):
                return value

        raise RuntimeError(f"No dependency of type {type_} found")

    def set(self, tag: Tag[T], value: T) -> 'Runtime':
        """设置依赖（用于测试替换）"""
        self._env[tag] = value
        return self

    def override(self, **kwargs: Any) -> 'Runtime':
        """覆盖依赖（用于测试）"""
        for k, v in kwargs.items():
            tag = Tag(type(v), k)
            self._env[tag] = v
        return self

    def keys(self) -> List[Tag]:
        """获取所有依赖标签"""
        if not self._loaded:
            self.load()
        return list(self._env.keys())

    def __contains__(self, tag: Tag) -> bool:
        """检查依赖是否存在"""
        if not self._loaded:
            self.load()
        return tag in self._env


def make(tag: Tag[T], build: Callable[[], T]) -> Layer:
    """创建简单层"""
    def _build(env: Dict[Tag, Any]) -> Dict[Tag, Any]:
        return {tag: build()}
    return Layer([tag], [], _build)


def make_with_deps(tag: Tag[T], deps: List[Tag], build: Callable[[Dict[Tag, Any]], T]) -> Layer:
    """创建带依赖的层"""
    def _build(env: Dict[Tag, Any]) -> Dict[Tag, Any]:
        return {tag: build(env)}
    return Layer([tag], deps, _build)


def provide(tag: Tag[T]) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """装饰器：提供依赖"""
    def decorator(f: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            return result
        wrapper.__layer_tag__ = tag
        return wrapper
    return decorator


_instance: Optional[Runtime] = None


def get_runtime() -> Runtime:
    """获取全局运行时实例"""
    global _instance
    if _instance is None:
        _instance = Runtime()
    return _instance


def reset_runtime() -> None:
    """重置运行时（用于测试）"""
    global _instance
    _instance = None
