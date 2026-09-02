#!/usr/bin/env python3
"""
状态转换系统

参考 opencode 的 state.ts，实现可重放的状态转换。

核心功能：
1. State.create() 创建状态机
2. 定义转换器（transformers）
3. 应用转换
4. 状态快照和恢复
5. 事件重放

Example:
    counter_state = State.create({
        'counter': 0,
        'transformers': [
            State.transform('increment', lambda s, n: {'counter': s['counter'] + n}),
        ]
    })

    result = counter_state.apply('increment', 5)
    print(result.state['counter'])  # 5
"""

import copy
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, Type, TypeVar, Union

from infra.errors import BaseError

T = TypeVar("T")
S = TypeVar("S")


class StateError(BaseError):
    """状态错误"""

    __error_name__ = "StateError"
    __error_tags__ = ["state"]


class UnknownTransformError(StateError):
    """未知转换错误"""

    __error_name__ = "UnknownTransformError"
    __error_tags__ = ["state", "transform"]


class StateValidationError(StateError):
    """状态验证错误"""

    __error_name__ = "StateValidationError"
    __error_tags__ = ["state", "validation"]


@dataclass(frozen=True)
class Transform:
    """
    状态转换器

    Args:
        name: 转换名称
        fn: 转换函数 (state, payload) -> new_state
        schema: 参数 Schema（可选）
    """

    name: str
    fn: Callable[[Any, Any], Any]
    schema: Optional[Any] = None

    def apply(self, state: Any, payload: Any) -> Any:
        """
        应用转换

        Args:
            state: 当前状态
            payload: 转换参数

        Returns:
            新状态
        """
        return self.fn(state, payload)


@dataclass
class StateEvent:
    """
    状态变更事件

    Args:
        transform: 转换名称
        payload: 转换参数
        timestamp: 时间戳
    """

    transform: str
    payload: Any
    timestamp: float = field(default_factory=lambda: __import__("time").time())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "transform": self.transform,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


@dataclass
class StateSnapshot:
    """
    状态快照

    Args:
        state: 状态数据
        version: 版本号
        timestamp: 时间戳
        event_count: 事件数量
    """

    state: Any
    version: int = 1
    timestamp: float = field(default_factory=lambda: __import__("time").time())
    event_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "state": self.state,
            "version": self.version,
            "timestamp": self.timestamp,
            "event_count": self.event_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateSnapshot":
        """从字典创建"""
        return cls(**data)


class State(Generic[T]):
    """
    状态机类

    参考 opencode 的 State，提供可重放的状态转换。

    Args:
        initial_state: 初始状态
        transformers: 转换器列表
        events: 事件历史
        snapshot: 当前快照
        version: 当前版本
    """

    def __init__(
        self,
        initial_state: T,
        transformers: List[Transform] = None,
        events: List[StateEvent] = None,
        snapshot: Optional[StateSnapshot] = None,
        version: int = 1,
    ):
        self._state = copy.deepcopy(initial_state)
        self._transformers = transformers or []
        self._transform_map = {t.name: t for t in self._transformers}
        self._events = events or []
        self._snapshot = snapshot
        self._version = version

    @property
    def state(self) -> T:
        """获取当前状态"""
        return copy.deepcopy(self._state)

    @property
    def version(self) -> int:
        """获取当前版本"""
        return self._version

    @property
    def events(self) -> List[StateEvent]:
        """获取事件历史"""
        return list(self._events)

    @property
    def event_count(self) -> int:
        """获取事件数量"""
        return len(self._events)

    def get_transform(self, name: str) -> Optional[Transform]:
        """
        获取转换器

        Args:
            name: 转换器名称

        Returns:
            转换器或 None
        """
        return self._transform_map.get(name)

    def apply(self, transform_name: str, payload: Any = None) -> "State[T]":
        """
        应用转换

        Args:
            transform_name: 转换名称
            payload: 转换参数

        Returns:
            新状态机实例

        Raises:
            UnknownTransformError: 未知转换
        """
        transform = self.get_transform(transform_name)
        if not transform:
            raise UnknownTransformError(f"Unknown transform: {transform_name}")

        # 创建事件
        event = StateEvent(transform=transform_name, payload=payload)

        # 应用转换
        new_state = transform.apply(self._state, payload)

        # 创建新状态机
        new_events = self._events + [event]
        new_version = self._version + 1

        return State(
            initial_state=new_state,
            transformers=self._transformers,
            events=new_events,
            version=new_version,
        )

    def apply_many(self, transforms: List[Tuple[str, Any]]) -> "State[T]":
        """
        批量应用转换

        Args:
            transforms: 转换列表 [(name, payload), ...]

        Returns:
            新状态机实例
        """
        result = self
        for transform_name, payload in transforms:
            result = result.apply(transform_name, payload)
        return result

    def snapshot(self) -> StateSnapshot:
        """
        创建状态快照

        Returns:
            状态快照
        """
        self._snapshot = StateSnapshot(
            state=self.state,
            version=self._version,
            event_count=self.event_count,
        )
        return self._snapshot

    def restore(self, snapshot: StateSnapshot) -> "State[T]":
        """
        从快照恢复

        Args:
            snapshot: 状态快照

        Returns:
            恢复后的状态机实例
        """
        return State(
            initial_state=snapshot.state,
            transformers=self._transformers,
            events=[],
            snapshot=snapshot,
            version=snapshot.version,
        )

    def replay(self, events: List[StateEvent]) -> "State[T]":
        """
        重放事件

        Args:
            events: 事件列表

        Returns:
            重放后的状态机实例
        """
        result = State(
            initial_state=self.state,
            transformers=self._transformers,
            events=self._events,
            version=self._version,
        )

        for event in events:
            result = result.apply(event.transform, event.payload)

        return result

    def reset(self) -> "State[T]":
        """
        重置到初始状态

        Returns:
            重置后的状态机实例
        """
        # 如果有快照，从快照恢复
        if self._snapshot:
            return self.restore(self._snapshot)

        # 否则从头重放所有事件
        if self._events:
            initial_state = self._replay_from_beginning()
            return State(
                initial_state=initial_state,
                transformers=self._transformers,
                events=self._events,
                version=self._version,
            )

        return self

    def _replay_from_beginning(self) -> T:
        """从头重放事件获取初始状态"""
        # 这是一个简化实现，实际应存储原始初始状态
        import copy

        state = copy.deepcopy(self._state)
        for event in reversed(self._events):
            # 反向重放（需要可逆转换）
            # 这里简化处理，返回当前状态
            pass
        return state

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "state": self.state,
            "version": self._version,
            "event_count": self.event_count,
            "transforms": [t.name for t in self._transformers],
        }

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict())

    @classmethod
    def create(cls, config: Dict[str, Any]) -> "State":
        """
        创建状态机（工厂方法）

        Args:
            config: 配置字典

        Returns:
            状态机实例

        Example:
            state = State.create({
                'initial': {'counter': 0},
                'transformers': [
                    State.transform('increment', lambda s, n: {'counter': s['counter'] + n}),
                ]
            })
        """
        initial_state = config.get("initial", {})
        transformers = config.get("transformers", [])

        return cls(
            initial_state=initial_state,
            transformers=transformers,
        )

    @staticmethod
    def transform(name: str, fn: Callable[[Any, Any], Any], schema: Optional[Any] = None) -> Transform:
        """
        创建转换器（静态工厂方法）

        Args:
            name: 转换名称
            fn: 转换函数
            schema: 参数 Schema

        Returns:
            转换器实例
        """
        return Transform(name=name, fn=fn, schema=schema)


class StructuredState(State[T]):
    """
    结构化状态机

    使用 Schema 验证状态和转换参数。
    """

    def __init__(
        self,
        initial_state: T,
        transformers: List[Transform] = None,
        state_schema: Optional[Any] = None,
        events: List[StateEvent] = None,
        snapshot: Optional[StateSnapshot] = None,
        version: int = 1,
    ):
        super().__init__(initial_state, transformers, events, snapshot, version)
        self._state_schema = state_schema

    def _validate_state(self, state: T) -> None:
        """
        验证状态

        Args:
            state: 状态数据

        Raises:
            StateValidationError: 验证失败
        """
        if self._state_schema:
            try:
                if hasattr(self._state_schema, "decode"):
                    self._state_schema.decode(state)
            except Exception as e:
                raise StateValidationError(f"State validation failed: {e}") from e

    def apply(self, transform_name: str, payload: Any = None) -> "StructuredState[T]":
        """
        应用转换（带验证）

        Args:
            transform_name: 转换名称
            payload: 转换参数

        Returns:
            新状态机实例
        """
        result = super().apply(transform_name, payload)

        # 验证新状态
        if self._state_schema:
            self._validate_state(result._state)

        return self.__class__(
            initial_state=result._state,
            transformers=self._transformers,
            state_schema=self._state_schema,
            events=result._events,
            version=result._version,
        )


class CounterState(StructuredState[Dict[str, int]]):
    """
    计数器状态机

    预设的计数器状态机，支持增减操作。
    """

    def __init__(
        self,
        initial_value: int = 0,
        *,
        initial_state: Optional[Dict[str, int]] = None,
        transformers: Optional[List[Transform]] = None,
        state_schema: Optional[Any] = None,
        events: Optional[List["StateEvent"]] = None,
        version: int = 1,
    ):
        if initial_state is not None:
            # 从状态恢复（用于 apply() 方法）
            super().__init__(
                initial_state=initial_state,
                transformers=transformers or [],
                state_schema=state_schema,
                events=events,
                version=version,
            )
        else:
            # 正常初始化
            default_transformers = [
                State.transform("increment", lambda s, n: {"value": s["value"] + n}),
                State.transform("decrement", lambda s, n: {"value": max(0, s["value"] - n)}),
                State.transform("reset", lambda s, _: {"value": 0}),
                State.transform("set", lambda s, v: {"value": v}),
            ]
            super().__init__(
                initial_state={"value": initial_value},
                transformers=default_transformers,
            )

    @property
    def value(self) -> int:
        """获取当前值"""
        return self.state["value"]


class ToggleState(StructuredState[Dict[str, bool]]):
    """
    开关状态机

    预设的开关状态机，支持切换操作。
    """

    def __init__(
        self,
        initial_value: bool = False,
        *,
        initial_state: Optional[Dict[str, bool]] = None,
        transformers: Optional[List[Transform]] = None,
        state_schema: Optional[Any] = None,
        events: Optional[List["StateEvent"]] = None,
        version: int = 1,
    ):
        if initial_state is not None:
            super().__init__(
                initial_state=initial_state,
                transformers=transformers or [],
                state_schema=state_schema,
                events=events,
                version=version,
            )
        else:
            default_transformers = [
                State.transform("toggle", lambda s, _: {"value": not s["value"]}),
                State.transform("on", lambda s, _: {"value": True}),
                State.transform("off", lambda s, _: {"value": False}),
                State.transform("set", lambda s, v: {"value": v}),
            ]
            super().__init__(
                initial_state={"value": initial_value},
                transformers=default_transformers,
            )

    @property
    def value(self) -> bool:
        """获取当前值"""
        return self.state["value"]


class ListState(StructuredState[Dict[str, List[Any]]]):
    """
    列表状态机

    预设的列表状态机，支持增删查操作。
    """

    def __init__(
        self,
        initial_items: List[Any] = None,
        *,
        initial_state: Optional[Dict[str, List[Any]]] = None,
        transformers: Optional[List[Transform]] = None,
        state_schema: Optional[Any] = None,
        events: Optional[List["StateEvent"]] = None,
        version: int = 1,
    ):
        if initial_state is not None:
            super().__init__(
                initial_state=initial_state,
                transformers=transformers or [],
                state_schema=state_schema,
                events=events,
                version=version,
            )
        else:
            default_transformers = [
                State.transform("add", lambda s, item: {"items": s["items"] + [item]}),
                State.transform("remove", lambda s, idx: {"items": s["items"][:idx] + s["items"][idx + 1 :]}),
                State.transform("clear", lambda s, _: {"items": []}),
                State.transform("set", lambda s, items: {"items": items}),
            ]
            super().__init__(
                initial_state={"items": initial_items or []},
                transformers=default_transformers,
            )

    @property
    def items(self) -> List[Any]:
        """获取当前列表"""
        return self.state["items"]

    @property
    def length(self) -> int:
        """获取列表长度"""
        return len(self.items)


__all__ = [
    "State",
    "StructuredState",
    "CounterState",
    "ToggleState",
    "ListState",
    "Transform",
    "StateEvent",
    "StateSnapshot",
    "StateError",
    "UnknownTransformError",
    "StateValidationError",
]
