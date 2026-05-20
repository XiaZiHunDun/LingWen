"""PushEngine 测试"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from infra.memory_system.gateway.push_engine import PushEngine


class TestPushEngine:
    """PushEngine 测试套件"""

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
    def mock_query_engine(self):
        """模拟 QueryEngine"""
        engine = MagicMock()
        engine.hybrid_search = MagicMock(return_value=[
            {
                "id": "seg_001",
                "score": 0.95,
                "payload": {
                    "content": "李逍遥与赵灵儿在仙灵岛相遇",
                    "chapter": 3,
                    "character": "李逍遥",
                },
            },
            {
                "id": "seg_002",
                "score": 0.85,
                "payload": {
                    "content": "林夜是铁蛋的弟弟",
                    "chapter": 5,
                    "character": "林夜",
                },
            },
        ])
        return engine

    @pytest.fixture
    def mock_character_tracker(self):
        """模拟 CharacterTracker"""
        tracker = MagicMock()
        tracker.get_all_characters = MagicMock(return_value={
            "李逍遥": {
                "current_location": "仙灵岛",
                "current_form": "人形",
                "alive": True,
                "last_updated_chapter": 5,
                "emotion_state": "平静",
            },
            "赵灵儿": {
                "current_location": "仙灵岛",
                "current_form": "人形",
                "alive": True,
                "last_updated_chapter": 5,
                "emotion_state": "欢喜",
            },
        })
        return tracker

    @pytest.fixture
    def mock_plot_thread_tracker(self):
        """模拟 PlotThreadTracker"""
        tracker = MagicMock()
        tracker.get_pending_foreshadows = MagicMock(return_value={
            "fp_001": {
                "title": "神秘剑客",
                "description": "一个神秘剑客在第三章首次出现",
                "status": "pending",
                "planted_chapter": 3,
                "mentions": [3],
                "expected_recycle_chapter": 10,
            },
            "fp_002": {
                "title": "门派恩怨",
                "description": "蜀山派与魔教的历史恩怨",
                "status": "in_progress",
                "planted_chapter": 2,
                "mentions": [2, 5],
                "expected_recycle_chapter": 15,
            },
        })
        tracker.get_all_foreshadows = MagicMock(return_value={
            "fp_001": {
                "title": "神秘剑客",
                "status": "pending",
                "planted_chapter": 3,
            },
            "fp_002": {
                "title": "门派恩怨",
                "status": "in_progress",
                "planted_chapter": 2,
            },
            "fp_003": {
                "title": "已回收伏笔",
                "status": "recycled",
                "planted_chapter": 1,
                "recycled_chapter": 8,
            },
        })
        return tracker

    @pytest.fixture
    def mock_timeline_manager(self):
        """模拟 TimelineManager"""
        manager = MagicMock()
        manager.get_all_events = MagicMock(return_value=[
            {
                "event_id": "evt_001",
                "timestamp": "2024-01-01T10:00:00",
                "description": "李逍遥与赵灵儿相遇",
                "chapter": 3,
            },
            {
                "event_id": "evt_002",
                "timestamp": "2024-01-01T12:00:00",
                "description": "林夜首次出场",
                "chapter": 5,
            },
            {
                "event_id": "evt_003",
                "timestamp": "2024-01-01T14:00:00",
                "description": "神秘剑客出现",
                "chapter": 3,
            },
        ])
        manager.get_events_by_chapter = MagicMock(return_value=[
            {
                "event_id": "evt_001",
                "timestamp": "2024-01-01T10:00:00",
                "description": "李逍遥与赵灵儿相遇",
                "chapter": 3,
            },
        ])
        return manager

    @pytest.fixture
    def push_engine(
        self,
        mock_query_engine,
        mock_character_tracker,
        mock_plot_thread_tracker,
        mock_timeline_manager,
    ):
        """创建 PushEngine 实例（使用模拟依赖）"""
        return PushEngine(
            query_engine=mock_query_engine,
            character_tracker=mock_character_tracker,
            plot_thread_tracker=mock_plot_thread_tracker,
            timeline_manager=mock_timeline_manager,
        )

    def test_initialization(self, push_engine, mock_query_engine):
        """测试 PushEngine 初始化"""
        assert push_engine.query_engine is mock_query_engine
        assert push_engine.character_tracker is not None
        assert push_engine.plot_thread_tracker is not None
        assert push_engine.timeline_manager is not None

    def test_initialization_without_optional_deps(self, mock_query_engine):
        """测试只有 query_engine 时的初始化"""
        engine = PushEngine(query_engine=mock_query_engine)
        assert engine.query_engine is mock_query_engine
        assert engine.character_tracker is None
        assert engine.plot_thread_tracker is None
        assert engine.timeline_manager is None

    def test_get_character_states(self, push_engine, mock_character_tracker):
        """测试获取所有角色状态摘要"""
        result = push_engine.get_character_states()

        assert isinstance(result, dict)
        assert "李逍遥" in result
        assert "赵灵儿" in result
        assert result["李逍遥"]["current_location"] == "仙灵岛"
        assert result["李逍遥"]["alive"] is True
        assert result["赵灵儿"]["emotion_state"] == "欢喜"
        mock_character_tracker.get_all_characters.assert_called_once()

    def test_get_character_states_no_tracker(self, mock_query_engine):
        """测试没有 CharacterTracker 时获取角色状态"""
        engine = PushEngine(query_engine=mock_query_engine)
        result = engine.get_character_states()

        assert result == {}

    def test_get_pending_foreshadows(self, push_engine, mock_plot_thread_tracker):
        """测试获取待回收伏笔摘要"""
        result = push_engine.get_pending_foreshadows()

        assert isinstance(result, dict)
        assert "fp_001" in result
        assert "fp_002" in result
        assert result["fp_001"]["title"] == "神秘剑客"
        assert result["fp_001"]["status"] == "pending"
        assert result["fp_002"]["status"] == "in_progress"
        mock_plot_thread_tracker.get_pending_foreshadows.assert_called_once()

    def test_get_pending_foreshadows_no_tracker(self, mock_query_engine):
        """测试没有 PlotThreadTracker 时获取伏笔"""
        engine = PushEngine(query_engine=mock_query_engine)
        result = engine.get_pending_foreshadows()

        assert result == {}

    def test_get_recent_events(self, push_engine, mock_timeline_manager):
        """测试获取最近事件"""
        result = push_engine.get_recent_events(count=3)

        assert isinstance(result, list)
        assert len(result) == 3
        # 应该按时间倒序返回最近的事件
        assert result[0]["event_id"] == "evt_003"
        assert result[1]["event_id"] == "evt_002"
        assert result[2]["event_id"] == "evt_001"

    def test_get_recent_events_count_limit(self, push_engine, mock_timeline_manager):
        """测试获取最近事件的默认数量限制"""
        result = push_engine.get_recent_events()

        # 默认应该是 5
        assert len(result) == 3  # 只有3个事件

    def test_get_recent_events_no_tracker(self, mock_query_engine):
        """测试没有 TimelineManager 时获取最近事件"""
        engine = PushEngine(query_engine=mock_query_engine)
        result = engine.get_recent_events(count=5)

        assert result == []

    def test_push_context(self, push_engine, mock_query_engine):
        """测试推送当前章节相关上下文"""
        result = push_engine.push_context(chapter_num=5)

        assert isinstance(result, dict)
        assert "chapter" in result
        assert result["chapter"] == 5
        assert "character_states" in result
        assert "pending_foreshadows" in result
        assert "recent_events" in result
        assert "related_segments" in result

    def test_push_context_without_trackers(self, mock_query_engine):
        """测试没有追踪器时推送上下文"""
        engine = PushEngine(query_engine=mock_query_engine)
        result = engine.push_context(chapter_num=5)

        assert isinstance(result, dict)
        assert result["chapter"] == 5
        assert result["character_states"] == {}
        assert result["pending_foreshadows"] == {}
        assert result["recent_events"] == []
        # related_segments 仍然应该返回一些结果
        assert "related_segments" in result

    def test_push_context_includes_chapter_events(
        self, push_engine, mock_timeline_manager
    ):
        """测试推送上下文包含当前章节的事件"""
        result = push_engine.push_context(chapter_num=3)

        mock_timeline_manager.get_events_by_chapter.assert_called_with(3)

    def test_push_context_with_query(self, push_engine, mock_query_engine):
        """测试推送上下文时使用查询引擎"""
        result = push_engine.push_context(chapter_num=5)

        mock_query_engine.hybrid_search.assert_called()
        call_args = mock_query_engine.hybrid_search.call_args
        # 应该传入包含章节信息的查询
        assert "related_segments" in result

    def test_push_context_returns_complete_context(self, push_engine):
        """测试推送返回完整上下文"""
        result = push_engine.push_context(chapter_num=5)

        # 验证所有必需字段都存在
        required_fields = [
            "chapter",
            "character_states",
            "pending_foreshadows",
            "recent_events",
            "related_segments",
        ]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_foreshadow_summary_format(self, push_engine):
        """测试伏笔摘要格式"""
        result = push_engine.push_context(chapter_num=5)

        pending = result["pending_foreshadows"]
        if pending:
            for fp_id, fp_data in pending.items():
                # 伏笔应该包含关键信息
                assert "title" in fp_data
                assert "status" in fp_data
                assert "planted_chapter" in fp_data

    def test_character_state_summary_format(self, push_engine):
        """测试角色状态摘要格式"""
        result = push_engine.push_context(chapter_num=5)

        char_states = result["character_states"]
        if char_states:
            for char_name, state in char_states.items():
                # 角色状态应该包含关键信息
                assert "current_location" in state or "alive" in state or "emotion_state" in state

    def test_recent_events_sorted_by_timestamp(self, push_engine, mock_timeline_manager):
        """测试最近事件按时间戳排序"""
        mock_timeline_manager.get_all_events.return_value = [
            {
                "event_id": "evt_old",
                "timestamp": "2024-01-01T10:00:00",
                "description": "旧事件",
                "chapter": 1,
            },
            {
                "event_id": "evt_new",
                "timestamp": "2024-01-01T20:00:00",
                "description": "新事件",
                "chapter": 10,
            },
        ]

        result = push_engine.get_recent_events(count=5)

        assert result[0]["event_id"] == "evt_new"
        assert result[1]["event_id"] == "evt_old"

    def test_push_context_with_empty_events(self, push_engine, mock_timeline_manager):
        """测试章节没有事件时的推送"""
        mock_timeline_manager.get_events_by_chapter.return_value = []
        mock_timeline_manager.get_all_events.return_value = []

        result = push_engine.push_context(chapter_num=999)

        assert isinstance(result, dict)
        # 即使没有事件，也应该返回空列表而不是报错
        assert result["recent_events"] == []


class TestPushEngineEdgeCases:
    """PushEngine 边界情况测试"""

    @pytest.fixture
    def mock_query_engine(self):
        """模拟 QueryEngine"""
        engine = MagicMock()
        engine.hybrid_search = MagicMock(return_value=[])
        return engine

    @pytest.fixture
    def mock_character_tracker(self):
        """模拟 CharacterTracker"""
        tracker = MagicMock()
        tracker.get_all_characters = MagicMock(return_value={})
        return tracker

    @pytest.fixture
    def mock_plot_thread_tracker(self):
        """模拟 PlotThreadTracker"""
        tracker = MagicMock()
        tracker.get_pending_foreshadows = MagicMock(return_value={})
        return tracker

    @pytest.fixture
    def mock_timeline_manager(self):
        """模拟 TimelineManager"""
        manager = MagicMock()
        manager.get_all_events = MagicMock(return_value=[])
        manager.get_events_by_chapter = MagicMock(return_value=[])
        return manager

    def test_empty_character_states(self, mock_query_engine, mock_character_tracker):
        """测试空角色状态"""
        engine = PushEngine(
            query_engine=mock_query_engine,
            character_tracker=mock_character_tracker,
        )
        result = engine.get_character_states()
        assert result == {}

    def test_empty_pending_foreshadows(self, mock_query_engine, mock_plot_thread_tracker):
        """测试空伏笔列表"""
        engine = PushEngine(
            query_engine=mock_query_engine,
            plot_thread_tracker=mock_plot_thread_tracker,
        )
        result = engine.get_pending_foreshadows()
        assert result == {}

    def test_empty_recent_events(self, mock_query_engine, mock_timeline_manager):
        """测试空事件列表"""
        engine = PushEngine(
            query_engine=mock_query_engine,
            timeline_manager=mock_timeline_manager,
        )
        result = engine.get_recent_events(count=5)
        assert result == []

    def test_push_context_chapter_zero(self, mock_query_engine):
        """测试第0章的上下文推送"""
        engine = PushEngine(query_engine=mock_query_engine)
        result = engine.push_context(chapter_num=0)

        assert isinstance(result, dict)
        assert result["chapter"] == 0
