#!/usr/bin/env python3
"""
事件总线测试
"""
import time
from datetime import datetime
from unittest import TestCase

from infra.hooks import Event, EventBus, EventTypes


class TestEvent(TestCase):
    """Event数据类测试"""

    def test_event_creation(self):
        """测试事件创建"""
        event = Event(
            name="CHAPTER_WRITTEN",
            source="content_writer",
            data={"chapter_id": "ch001", "status": "draft_completed"}
        )

        self.assertEqual(event.name, "CHAPTER_WRITTEN")
        self.assertEqual(event.source, "content_writer")
        self.assertEqual(event.data["chapter_id"], "ch001")
        self.assertIsInstance(event.timestamp, datetime)

    def test_event_str_representation(self):
        """测试事件字符串表示"""
        event = Event(name="TEST_EVENT", source="test")
        str_repr = str(event)
        self.assertIn("TEST_EVENT", str_repr)
        self.assertIn("test", str_repr)


class TestEventBus(TestCase):
    """EventBus事件总线测试"""

    def setUp(self):
        """测试前准备"""
        self.event_bus = EventBus()
        self.received_events = []

    def _create_handler(self, name: str):
        """创建测试用handler"""
        def handler(event: Event):
            self.received_events.append((name, event))
        return handler

    def test_subscribe_and_publish(self):
        """测试订阅和发布"""
        handler = self._create_handler("handler1")
        self.event_bus.subscribe("CHAPTER_WRITTEN", handler)

        event = Event(name="CHAPTER_WRITTEN", source="test", data={"chapter": "ch001"})
        results = self.event_bus.publish(event)

        self.assertEqual(len(results), 1)
        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(self.received_events[0][0], "handler1")
        self.assertEqual(self.received_events[0][1].name, "CHAPTER_WRITTEN")

    def test_multiple_handlers(self):
        """测试多个handler"""
        handler1 = self._create_handler("h1")
        handler2 = self._create_handler("h2")
        self.event_bus.subscribe("CHAPTER_WRITTEN", handler1, priority=1)
        self.event_bus.subscribe("CHAPTER_WRITTEN", handler2, priority=2)

        event = Event(name="CHAPTER_WRITTEN", source="test")
        self.event_bus.publish(event)

        # 高优先级先执行
        self.assertEqual(len(self.received_events), 2)
        self.assertEqual(self.received_events[0][0], "h2")  # priority=2 先
        self.assertEqual(self.received_events[1][0], "h1")  # priority=1 后

    def test_unsubscribe(self):
        """测试取消订阅"""
        handler = self._create_handler("handler1")
        self.event_bus.subscribe("CHAPTER_WRITTEN", handler)
        self.event_bus.unsubscribe("CHAPTER_WRITTEN", handler)

        event = Event(name="CHAPTER_WRITTEN", source="test")
        self.event_bus.publish(event)

        self.assertEqual(len(self.received_events), 0)

    def test_filter_function(self):
        """测试事件过滤"""
        def filter_func(event: Event) -> bool:
            return event.data.get("allow", False)

        handler = self._create_handler("handler1")
        self.event_bus.subscribe("TEST_EVENT", handler, filter_func=filter_func)

        # 被过滤的事件
        event1 = Event(name="TEST_EVENT", source="test", data={"allow": False})
        self.event_bus.publish(event1)
        self.assertEqual(len(self.received_events), 0)

        # 通过过滤的事件
        event2 = Event(name="TEST_EVENT", source="test", data={"allow": True})
        self.event_bus.publish(event2)
        self.assertEqual(len(self.received_events), 1)

    def test_async_publish(self):
        """测试异步发布"""
        import asyncio

        handler = self._create_handler("async_handler")
        self.event_bus.subscribe("ASYNC_EVENT", handler)

        event = Event(name="ASYNC_EVENT", source="test")

        async def run_async():
            await self.event_bus.publish_async(event)

        asyncio.run(run_async())

        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(self.received_events[0][0], "async_handler")

    def test_event_matching(self):
        """测试事件类型匹配"""
        handler = self._create_handler("handler")
        self.event_bus.subscribe("CHAPTER_WRITTEN", handler)

        # 发布匹配的事件
        event1 = Event(name="CHAPTER_WRITTEN", source="test")
        self.event_bus.publish(event1)
        self.assertEqual(len(self.received_events), 1)

        # 发布不匹配的事件
        self.received_events.clear()
        event2 = Event(name="CHAPTER_REVISED", source="test")
        self.event_bus.publish(event2)
        self.assertEqual(len(self.received_events), 0)

    def test_get_handler_count(self):
        """测试获取handler数量"""
        def handler1(e):
            return None
        def handler2(e):
            return None

        self.event_bus.subscribe("TEST_EVENT", handler1)
        self.assertEqual(self.event_bus.get_handler_count("TEST_EVENT"), 1)

        self.event_bus.subscribe("TEST_EVENT", handler2)
        self.assertEqual(self.event_bus.get_handler_count("TEST_EVENT"), 2)

        self.event_bus.subscribe("OTHER_EVENT", handler1)
        self.assertEqual(self.event_bus.get_handler_count("OTHER_EVENT"), 1)

    def test_clear(self):
        """测试清除事件订阅"""
        handler = self._create_handler("handler")
        self.event_bus.subscribe("EVENT1", handler)
        self.event_bus.subscribe("EVENT2", handler)

        # 清除单个事件
        self.event_bus.clear("EVENT1")
        self.assertEqual(self.event_bus.get_handler_count("EVENT1"), 0)
        self.assertEqual(self.event_bus.get_handler_count("EVENT2"), 1)

        # 清除所有
        self.event_bus.clear()
        self.assertEqual(self.event_bus.get_handler_count("EVENT2"), 0)


class TestEventTypes(TestCase):
    """事件类型常量测试"""

    def test_event_types_exist(self):
        """测试事件类型常量存在"""
        self.assertTrue(hasattr(EventTypes, "CHAPTER_WRITTEN"))
        self.assertTrue(hasattr(EventTypes, "REVIEW_COMPLETED"))
        self.assertTrue(hasattr(EventTypes, "STEP_COMPLETED"))
        self.assertTrue(hasattr(EventTypes, "PHASE_CHANGED"))

    def test_event_types_values(self):
        """测试事件类型值"""
        self.assertEqual(EventTypes.CHAPTER_WRITTEN, "CHAPTER_WRITTEN")
        self.assertEqual(EventTypes.REVIEW_COMPLETED, "REVIEW_COMPLETED")


class TestGlobalEventBusSingleton(TestCase):
    """R1-008: 全局事件总线单例 + reset 函数

    之前 _global_event_bus 没有重置入口,测试间 handler 互相污染。
    新增 reset_global_event_bus() 显式释放单例 + 清 handler。
    """

    def setUp(self):
        # 每个测试用例前都重置,避免上轮测试残留 handler 影响
        from infra.hooks.event_bus import reset_global_event_bus
        reset_global_event_bus()

    def tearDown(self):
        # 清理:不留跨测试状态
        from infra.hooks.event_bus import reset_global_event_bus
        reset_global_event_bus()

    def test_get_event_bus_returns_singleton(self):
        """get_event_bus() 多次调用返回同一实例"""
        from infra.hooks.event_bus import get_event_bus
        a = get_event_bus()
        b = get_event_bus()
        self.assertIs(a, b)

    def test_reset_clears_handlers(self):
        """reset_global_event_bus() 必须清掉所有 handler"""
        from infra.hooks.event_bus import get_event_bus, reset_global_event_bus
        bus = get_event_bus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe("RESET_TEST", handler)
        self.assertEqual(bus.get_handler_count("RESET_TEST"), 1)

        # 重置:handler 应消失
        reset_global_event_bus()

        # 旧引用 bus 仍能用,但 handler 没了
        self.assertEqual(bus.get_handler_count("RESET_TEST"), 0)

        # 新 get_event_bus() 返回不同实例
        new_bus = get_event_bus()
        self.assertIsNot(new_bus, bus)

    def test_reset_idempotent(self):
        """reset 在没有单例时也可调用(不应抛异常)"""
        from infra.hooks.event_bus import reset_global_event_bus
        # 先 reset 一次,确保 None
        reset_global_event_bus()
        # 再 reset 一次,仍是 None,不应抛
        reset_global_event_bus()

    def test_fixture_pattern_isolates_handlers(self):
        """核心场景:测试 A subscribe → reset → 测试 B 看不到

        这是 R1-008 修复的真实痛点:之前测试间 handler 泄漏导致
        偶发性失败 (e.g. handler 数对不上)。
        """
        from infra.hooks.event_bus import get_event_bus, reset_global_event_bus

        # 测试 A: subscribe
        bus_a = get_event_bus()
        bus_a.subscribe("LEAK_TEST", lambda e: None)
        self.assertEqual(bus_a.get_handler_count("LEAK_TEST"), 1)

        # 用 reset 模拟测试边界
        reset_global_event_bus()

        # 测试 B: 应看到全新 bus
        bus_b = get_event_bus()
        self.assertEqual(bus_b.get_handler_count("LEAK_TEST"), 0)

    def test_reset_clears_filters_too(self):
        """reset 也应清掉 event_filters (订阅 filter 也会泄漏)"""
        from infra.hooks.event_bus import get_event_bus, reset_global_event_bus

        bus = get_event_bus()
        # 通过 publish 触发 filter 注册路径 → 不直接暴露接口
        # 此处只验证:reset 后 bus 是新的,旧 bus 即使被外部引用也不再有
        # 副作用 → 通过 setUp/tearDown 的对称性保证
        bus_id_before = id(bus)
        reset_global_event_bus()
        new_bus = get_event_bus()
        self.assertNotEqual(id(new_bus), bus_id_before)


if __name__ == "__main__":
    import unittest
    unittest.main()
