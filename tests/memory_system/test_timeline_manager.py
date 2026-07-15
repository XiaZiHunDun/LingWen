"""TimelineManager 测试"""
from datetime import datetime
from pathlib import Path

import pytest

from infra.memory_system.state.timeline_manager import TimelineManager


class TestTimelineManager:
    """TimelineManager 测试套件"""

    @pytest.fixture
    def temp_state_dir(self, tmp_path):
        """创建临时状态目录"""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        return state_dir

    @pytest.fixture
    def mock_config(self, temp_state_dir):
        """模拟配置"""
        return {
            "storage": {
                "state_file": str(temp_state_dir / "state_tracker.json"),
                "plot_threads_file": str(temp_state_dir / "plot_threads.yaml"),
                "timeline_file": str(temp_state_dir / "timeline.json"),
            }
        }

    @pytest.fixture
    def manager(self, mock_config):
        """创建 TimelineManager 实例"""
        return TimelineManager(mock_config)

    def test_add_event(self, manager):
        """测试添加事件"""
        event = manager.add_event(
            event_id="evt_001",
            timestamp="2026-05-19T10:00:00",
            description="主角进入王宫",
            chapter=1,
            metadata={"location": "王宫", "characters": ["李逍遥"]}
        )

        assert event["event_id"] == "evt_001"
        assert event["timestamp"] == "2026-05-19T10:00:00"
        assert event["description"] == "主角进入王宫"
        assert event["chapter"] == 1
        assert event["metadata"]["location"] == "王宫"

    def test_add_multiple_events(self, manager):
        """测试添加多个事件"""
        manager.add_event(
            event_id="evt_001",
            timestamp="2026-05-19T10:00:00",
            description="事件1",
            chapter=1,
            metadata={}
        )
        manager.add_event(
            event_id="evt_002",
            timestamp="2026-05-19T11:00:00",
            description="事件2",
            chapter=2,
            metadata={}
        )

        events = manager.get_all_events()
        assert len(events) == 2
        assert events[0]["event_id"] == "evt_001"
        assert events[1]["event_id"] == "evt_002"

    def test_get_events_in_range(self, manager):
        """测试按时间范围查询事件"""
        manager.add_event(
            event_id="evt_001",
            timestamp="2026-05-19T08:00:00",
            description="早期事件",
            chapter=1,
            metadata={}
        )
        manager.add_event(
            event_id="evt_002",
            timestamp="2026-05-19T10:00:00",
            description="中期事件",
            chapter=5,
            metadata={}
        )
        manager.add_event(
            event_id="evt_003",
            timestamp="2026-05-19T14:00:00",
            description="晚期事件",
            chapter=10,
            metadata={}
        )

        events = manager.get_events_in_range(
            start_time="2026-05-19T09:00:00",
            end_time="2026-05-19T12:00:00"
        )

        assert len(events) == 1
        assert events[0]["event_id"] == "evt_002"

    def test_get_events_in_range_boundary(self, manager):
        """测试时间范围边界包含"""
        manager.add_event(
            event_id="evt_001",
            timestamp="2026-05-19T09:00:00",
            description="边界事件1",
            chapter=1,
            metadata={}
        )
        manager.add_event(
            event_id="evt_002",
            timestamp="2026-05-19T10:00:00",
            description="边界事件2",
            chapter=2,
            metadata={}
        )

        events = manager.get_events_in_range(
            start_time="2026-05-19T09:00:00",
            end_time="2026-05-19T10:00:00"
        )

        assert len(events) == 2

    def test_get_events_by_chapter(self, manager):
        """测试按章节查询事件"""
        manager.add_event(
            event_id="evt_001",
            timestamp="2026-05-19T10:00:00",
            description="第1章事件",
            chapter=1,
            metadata={}
        )
        manager.add_event(
            event_id="evt_002",
            timestamp="2026-05-19T11:00:00",
            description="第1章事件2",
            chapter=1,
            metadata={}
        )
        manager.add_event(
            event_id="evt_003",
            timestamp="2026-05-19T12:00:00",
            description="第5章事件",
            chapter=5,
            metadata={}
        )

        events = manager.get_events_by_chapter(1)
        assert len(events) == 2
        assert all(e["chapter"] == 1 for e in events)

    def test_get_events_by_chapter_not_found(self, manager):
        """测试查询不存在的章节"""
        manager.add_event(
            event_id="evt_001",
            timestamp="2026-05-19T10:00:00",
            description="事件",
            chapter=1,
            metadata={}
        )

        events = manager.get_events_by_chapter(999)
        assert len(events) == 0

    def test_get_all_events_empty(self, manager):
        """测试在没有事件时返回空列表"""
        events = manager.get_all_events()
        assert events == []

    def test_get_all_events(self, manager):
        """测试获取所有事件"""
        manager.add_event(
            event_id="evt_001",
            timestamp="2026-05-19T10:00:00",
            description="事件1",
            chapter=1,
            metadata={}
        )
        manager.add_event(
            event_id="evt_002",
            timestamp="2026-05-19T11:00:00",
            description="事件2",
            chapter=2,
            metadata={}
        )

        events = manager.get_all_events()
        assert len(events) == 2

    def test_event_persistence_after_save_load(self, mock_config, temp_state_dir):
        """测试事件数据在保存和加载后保持一致"""
        manager1 = TimelineManager(mock_config)
        manager1.add_event(
            event_id="evt_persist",
            timestamp="2026-05-19T15:00:00",
            description="持久化测试",
            chapter=20,
            metadata={"key": "value"}
        )

        # 创建新实例模拟重启
        manager2 = TimelineManager(mock_config)
        events = manager2.get_all_events()

        assert len(events) == 1
        assert events[0]["event_id"] == "evt_persist"
        assert events[0]["description"] == "持久化测试"
        assert events[0]["metadata"]["key"] == "value"

    def test_get_events_in_range_no_matches(self, manager):
        """测试时间范围内没有匹配事件"""
        manager.add_event(
            event_id="evt_001",
            timestamp="2026-05-19T10:00:00",
            description="事件",
            chapter=1,
            metadata={}
        )

        events = manager.get_events_in_range(
            start_time="2026-05-20T00:00:00",
            end_time="2026-05-20T23:59:59"
        )

        assert len(events) == 0

    def test_add_event_without_optional_fields(self, manager):
        """测试添加事件时不提供可选字段"""
        event = manager.add_event(
            event_id="evt_minimal",
            timestamp="2026-05-19T10:00:00",
            description="最小事件",
            chapter=1
        )

        assert event["event_id"] == "evt_minimal"
        assert event["chapter"] == 1
        assert event["metadata"] == {}

    def test_get_events_in_range_invalid_format(self, manager):
        """测试时间格式无效时返回空列表"""
        manager.add_event(
            event_id="evt_001",
            timestamp="2026-05-19T10:00:00",
            description="事件",
            chapter=1,
            metadata={}
        )

        events = manager.get_events_in_range(
            start_time="invalid",
            end_time="also_invalid"
        )

        assert events == []
