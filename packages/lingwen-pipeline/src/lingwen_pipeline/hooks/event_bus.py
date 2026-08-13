#!/usr/bin/env python3
"""
事件总线 - Hook系统的核心组件
提供事件订阅、发布、异步发布功能
"""
from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class EventBus:
    """
    事件总线 - 负责事件的订阅、发布和分发

    支持功能:
    - 同步/异步发布
    - 优先级机制
    - 事件过滤
    - 线程安全
    """

    def __init__(self):
        self._handlers: Dict[str, List[HandlerRegistration]] = {}
        self._lock = threading.RLock()
        self._event_filters: Dict[str, Callable[[Event], bool]] = {}

    def subscribe(
        self,
        event_name: str,
        handler: Callable[[Event], None],
        priority: int = 0,
        filter_func: Optional[Callable[[Event], bool]] = None
    ) -> None:
        """
        订阅事件

        Args:
            event_name: 事件名称（如 CHAPTER_WRITTEN）
            handler: 事件处理函数
            priority: 优先级（数值越大越先执行）
            filter_func: 过滤函数，返回True时才执行handler
        """
        with self._lock:
            if event_name not in self._handlers:
                self._handlers[event_name] = []

            registration = HandlerRegistration(
                handler=handler,
                priority=priority,
                filter_func=filter_func
            )
            self._handlers[event_name].append(registration)
            # 按优先级排序（高优先级在前）
            self._handlers[event_name].sort(key=lambda x: x.priority, reverse=True)

    def unsubscribe(
        self,
        event_name: str,
        handler: Callable[[Event], None]
    ) -> None:
        """
        取消订阅

        Args:
            event_name: 事件名称
            handler: 要移除的处理函数
        """
        with self._lock:
            if event_name in self._handlers:
                self._handlers[event_name] = [
                    reg for reg in self._handlers[event_name]
                    if reg.handler != handler
                ]

    def publish(self, event: Event) -> List[Any]:
        """
        同步发布事件

        Args:
            event: 要发布的事件

        Returns:
            所有handler的返回值列表
        """
        results = []
        with self._lock:
            handlers = self._handlers.get(event.name, []).copy()

        for registration in handlers:
            # 执行过滤函数
            if registration.filter_func and not registration.filter_func(event):
                continue

            try:
                result = registration.handler(event)
                results.append(result)
            except Exception as e:
                # 记录错误但不中断其他handler
                results.append(e)

        return results

    async def publish_async(self, event: Event) -> List[Any]:
        """
        异步发布事件（真正的异步执行）

        Args:
            event: 要发布的事件

        Returns:
            所有handler的返回值列表
        """
        tasks = []
        with self._lock:
            handlers = self._handlers.get(event.name, []).copy()

        for registration in handlers:
            if registration.filter_func and not registration.filter_func(event):
                continue
            task = asyncio.create_task(self._safe_handle(registration, event))
            tasks.append(task)

        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return list(results)

    async def _safe_handle(
        self,
        registration: HandlerRegistration,
        event: Event
    ) -> Any:
        """安全执行handler（捕获异常）"""
        try:
            result = registration.handler(event)
            # 如果handler返回协程，等待它完成
            if asyncio.iscoroutine(result):
                return await result
            return result
        except Exception as e:
            return e

    def clear(self, event_name: Optional[str] = None) -> None:
        """
        清除事件订阅

        Args:
            event_name: 如果指定，只清除该事件；否则清除所有
        """
        with self._lock:
            if event_name:
                self._handlers.pop(event_name, None)
            else:
                self._handlers.clear()

    def get_handler_count(self, event_name: str) -> int:
        """获取指定事件的handler数量"""
        with self._lock:
            return len(self._handlers.get(event_name, []))


@dataclass
class HandlerRegistration:
    """Handler注册信息"""
    handler: Callable[[Event], None]
    priority: int = 0
    filter_func: Optional[Callable[[Event], bool]] = None


@dataclass
class Event:
    """
    事件数据类

    Attributes:
        name: 事件名称（如 CHAPTER_WRITTEN、PHASE_CHANGED）
        source: 事件来源
        data: 事件数据（字典）
        timestamp: 事件发生时间
    """
    name: str
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"Event(name={self.name}, source={self.source}, timestamp={self.timestamp.isoformat()})"


# 预定义的事件类型常量
class EventTypes:
    """事件类型枚举"""
    # 工作流事件
    PHASE_CHANGED = "PHASE_CHANGED"
    STEP_COMPLETED = "STEP_COMPLETED"
    STEP_FAILED = "STEP_FAILED"

    # 写作事件
    CHAPTER_WRITTEN = "CHAPTER_WRITTEN"
    CHAPTER_REVISED = "CHAPTER_REVISED"
    CHAPTER_FINALIZED = "CHAPTER_FINALIZED"
    WRITER_IDLE = "WRITER_IDLE"

    # 审核事件
    REVIEW_STARTED = "REVIEW_STARTED"
    REVIEW_COMPLETED = "REVIEW_COMPLETED"
    REVIEW_FAILED = "REVIEW_FAILED"

    # 灵感事件
    INSPIRATION_GENERATED = "INSPIRATION_GENERATED"
    OUTLINE_APPROVED = "OUTLINE_APPROVED"

    # 汇总事件
    STAGE_SUMMARIZED = "STAGE_SUMMARIZED"
    VOLUME_SUMMARIZED = "VOLUME_SUMMARIZED"
    FINAL_SUMMARY_APPROVED = "FINAL_SUMMARY_APPROVED"

    # 外部事件
    MANUAL_TRIGGER = "MANUAL_TRIGGER"


# 全局事件总线实例（方便复用）
_global_event_bus: Optional[EventBus] = None
_global_event_bus_lock = threading.RLock()


def get_event_bus() -> EventBus:
    """获取全局事件总线实例"""
    global _global_event_bus
    if _global_event_bus is None:
        with _global_event_bus_lock:
            # 双重检查,避免多线程下重复创建
            if _global_event_bus is None:
                _global_event_bus = EventBus()
    return _global_event_bus


def reset_global_event_bus() -> None:
    """R1-008: 重置全局事件总线单例

    清空所有 handler + 释放单例引用,下次 get_event_bus() 会创建新实例。
    主要用于测试隔离:不同测试用例之间通过 fixture 调用本函数,
    避免 handler 跨用例泄漏 (e.g. 一次性 fixture 在 test_xxx1 里
    subscribe,test_xxx2 还看到那个 handler)。

    生产代码不应用本函数 — 业务逻辑应各自 new EventBus() 或在用完后
    unsubscribe 自己的 handler。
    """
    global _global_event_bus
    with _global_event_bus_lock:
        if _global_event_bus is not None:
            # 清掉所有 handler,防止旧 handler 仍持有引用导致内存泄漏
            _global_event_bus.clear()
        _global_event_bus = None
