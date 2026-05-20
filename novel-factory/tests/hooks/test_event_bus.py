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
        handler1 = lambda e: None
        handler2 = lambda e: None

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


if __name__ == "__main__":
    import unittest
    unittest.main()