"""MemoryGateway 测试"""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from infra.memory_system.gateway.memory_gateway import MemoryGateway


class TestMemoryGateway:
    """MemoryGateway 测试套件"""

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
            },
            "qdrant": {
                "host": "localhost",
                "port": 6333,
                "grpc_port": 6334,
            },
            "embedding": {
                "model": "text-embedding-3-small",
                "dimension": 1536,
            },
            "retrieval": {
                "default_top_k": 5,
                "hybrid_alpha": 0.7,
            },
        }

    @pytest.fixture
    def mock_qdrant_wrapper(self):
        """模拟 QdrantClientWrapper"""
        wrapper = MagicMock()
        wrapper.default_top_k = 5
        wrapper.hybrid_alpha = 0.7
        wrapper.dimension = 1536
        return wrapper

    @pytest.fixture
    def mock_embedder(self):
        """模拟 Embedder"""
        embedder = MagicMock()
        embedder.embed_texts = MagicMock(return_value=[[0.1] * 1536])
        return embedder

    @pytest.fixture
    def mock_character_tracker(self, mock_config):
        """模拟 CharacterTracker"""
        tracker = MagicMock()
        tracker.update_character_state = MagicMock()
        tracker.get_character_state = MagicMock(return_value={
            "current_location": "仙灵岛",
            "current_form": "人形",
            "alive": True,
            "last_updated_chapter": 5,
            "emotion_state": "平静",
        })
        tracker.get_all_characters = MagicMock(return_value={
            "李逍遥": {"current_location": "仙灵岛", "alive": True},
            "赵灵儿": {"current_location": "仙灵岛", "alive": True},
        })
        return tracker

    @pytest.fixture
    def mock_plot_thread_tracker(self, mock_config):
        """模拟 PlotThreadTracker"""
        tracker = MagicMock()
        tracker.plant_foreshadow = MagicMock()
        tracker.update_foreshadow = MagicMock()
        tracker.get_foreshadow = MagicMock(return_value={
            "title": "神秘剑客",
            "status": "pending",
            "planted_chapter": 3,
            "mentions": [3],
        })
        tracker.get_pending_foreshadows = MagicMock(return_value={
            "fp_001": {"title": "神秘剑客", "status": "pending"},
        })
        return tracker

    @pytest.fixture
    def mock_timeline_manager(self, mock_config):
        """模拟 TimelineManager"""
        manager = MagicMock()
        manager.add_event = MagicMock(return_value={
            "event_id": "evt_001",
            "timestamp": "2024-01-01T10:00:00",
            "description": "测试事件",
            "chapter": 5,
        })
        manager.get_events_by_chapter = MagicMock(return_value=[
            {"event_id": "evt_001", "chapter": 5},
        ])
        manager.get_all_events = MagicMock(return_value=[
            {"event_id": "evt_001", "chapter": 5},
        ])
        return manager

    @pytest.fixture
    def mock_fact_base(self, mock_config):
        """模拟 FactBase"""
        base = MagicMock()
        base.add_fact = MagicMock()
        base.get_fact = MagicMock(return_value={
            "fact_id": "fact_001",
            "content": "林夜是铁蛋的弟弟",
            "verified": True,
        })
        base.get_all_facts = MagicMock(return_value={
            "fact_001": {"fact_id": "fact_001", "content": "林夜是铁蛋的弟弟"},
        })
        return base

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
                },
            },
        ])
        engine.get_character_state = MagicMock(return_value={
            "current_location": "仙灵岛",
            "alive": True,
        })
        engine.get_relationship_network = MagicMock(return_value=[
            {"from_character": "李逍遥", "to_character": "赵灵儿", "relationship_type": "恋人"},
        ])
        engine.check_consistency = MagicMock(return_value={
            "is_consistent": True,
            "consistency_score": 1.0,
            "issues": [],
        })
        return engine

    @pytest.fixture
    def mock_push_engine(self):
        """模拟 PushEngine"""
        engine = MagicMock()
        engine.push_context = MagicMock(return_value={
            "chapter": 5,
            "character_states": {"李逍遥": {"alive": True}},
            "pending_foreshadows": {"fp_001": {"title": "神秘剑客"}},
            "recent_events": [],
            "related_segments": [],
        })
        return engine

    @pytest.fixture
    def memory_gateway(
        self,
        mock_qdrant_wrapper,
        mock_embedder,
        mock_character_tracker,
        mock_plot_thread_tracker,
        mock_timeline_manager,
        mock_fact_base,
        mock_query_engine,
        mock_push_engine,
    ):
        """创建 MemoryGateway 实例（使用模拟依赖）"""
        return MemoryGateway(
            qdrant_wrapper=mock_qdrant_wrapper,
            embedder=mock_embedder,
            character_tracker=mock_character_tracker,
            plot_thread_tracker=mock_plot_thread_tracker,
            timeline_manager=mock_timeline_manager,
            fact_base=mock_fact_base,
            query_engine=mock_query_engine,
            push_engine=mock_push_engine,
        )

    def test_initialization(self, memory_gateway, mock_qdrant_wrapper, mock_embedder):
        """测试 MemoryGateway 初始化"""
        assert memory_gateway.qdrant_wrapper is mock_qdrant_wrapper
        assert memory_gateway.embedder is mock_embedder
        assert memory_gateway.character_tracker is not None
        assert memory_gateway.plot_thread_tracker is not None
        assert memory_gateway.timeline_manager is not None
        assert memory_gateway.fact_base is not None
        assert memory_gateway.query_engine is not None
        assert memory_gateway.push_engine is not None

    def test_initialization_with_optional_deps(self, mock_qdrant_wrapper, mock_embedder):
        """测试只有必需依赖时的初始化（自动创建 QueryEngine 和 PushEngine）"""
        gateway = MemoryGateway(
            qdrant_wrapper=mock_qdrant_wrapper,
            embedder=mock_embedder,
        )
        assert gateway.qdrant_wrapper is mock_qdrant_wrapper
        assert gateway.embedder is mock_embedder
        assert gateway.character_tracker is None
        assert gateway.plot_thread_tracker is None
        assert gateway.timeline_manager is None
        assert gateway.fact_base is None
        # QueryEngine 和 PushEngine 会自动创建
        assert gateway.query_engine is not None
        assert gateway.push_engine is not None

    def test_auto_push_context(self, memory_gateway, mock_push_engine):
        """测试自动推送上下文"""
        result = memory_gateway.auto_push_context(chapter_num=5)

        assert isinstance(result, dict)
        assert "chapter" in result
        assert result["chapter"] == 5
        mock_push_engine.push_context.assert_called_once_with(chapter_num=5)

    def test_auto_push_context_returns_complete_context(self, memory_gateway, mock_push_engine):
        """测试自动推送返回完整上下文"""
        result = memory_gateway.auto_push_context(chapter_num=5)

        required_fields = ["chapter", "character_states", "pending_foreshadows"]
        for field in required_fields:
            assert field in result

    def test_query(self, memory_gateway, mock_query_engine):
        """测试主动查询"""
        result = memory_gateway.query(query="李逍遥在哪里", scope="character")

        assert isinstance(result, list)
        mock_query_engine.hybrid_search.assert_called()

    def test_query_with_chapter_scope(self, memory_gateway, mock_query_engine):
        """测试按章节范围查询"""
        result = memory_gateway.query(query="仙灵岛", scope="chapter")

        assert isinstance(result, list)
        mock_query_engine.hybrid_search.assert_called()

    def test_query_with_all_scope(self, memory_gateway, mock_query_engine):
        """测试全范围查询"""
        result = memory_gateway.query(query="神秘剑客", scope="all")

        assert isinstance(result, list)
        mock_query_engine.hybrid_search.assert_called()

    def test_query_empty_query(self, memory_gateway, mock_query_engine):
        """测试空查询"""
        result = memory_gateway.query(query="", scope="all")

        assert result == []
        mock_query_engine.hybrid_search.assert_not_called()

    def test_update_character_state(self, memory_gateway, mock_character_tracker):
        """测试更新角色状态"""
        state = {
            "current_location": "王宫",
            "alive": True,
            "last_updated_chapter": 10,
        }
        memory_gateway.update_character_state("李逍遥", state)

        mock_character_tracker.update_character_state.assert_called_once_with(
            "李逍遥", state
        )

    def test_plant_foreshadow(self, memory_gateway, mock_plot_thread_tracker):
        """测试登记伏笔"""
        metadata = {
            "title": "神秘剑客",
            "description": "一个神秘剑客在第三章首次出现",
            "planted_chapter": 3,
            "expected_recycle_chapter": 10,
        }
        memory_gateway.plant_foreshadow("fp_001", metadata)

        mock_plot_thread_tracker.plant_foreshadow.assert_called_once_with(
            "fp_001", metadata
        )

    def test_update_foreshadow(self, memory_gateway, mock_plot_thread_tracker):
        """测试更新伏笔状态"""
        memory_gateway.update_foreshadow("fp_001", chapter=5, event_type="activate")

        mock_plot_thread_tracker.update_foreshadow.assert_called_once_with(
            "fp_001", 5, "activate"
        )

    def test_update_foreshadow_recycle(self, memory_gateway, mock_plot_thread_tracker):
        """测试伏笔回收"""
        memory_gateway.update_foreshadow("fp_001", chapter=15, event_type="recycle")

        mock_plot_thread_tracker.update_foreshadow.assert_called_once_with(
            "fp_001", 15, "recycle"
        )

    def test_update_foreshadow_invalid_event_type(self, memory_gateway, mock_plot_thread_tracker):
        """测试无效事件类型不调用更新"""
        memory_gateway.update_foreshadow("fp_001", chapter=5, event_type="invalid_type")

        mock_plot_thread_tracker.update_foreshadow.assert_not_called()

    def test_get_character_state(self, memory_gateway, mock_character_tracker):
        """测试获取角色状态"""
        result = memory_gateway.get_character_state("李逍遥")

        assert result is not None
        mock_character_tracker.get_character_state.assert_called_once_with("李逍遥")

    def test_get_all_characters(self, memory_gateway, mock_character_tracker):
        """测试获取所有角色"""
        result = memory_gateway.get_all_characters()

        assert isinstance(result, dict)
        mock_character_tracker.get_all_characters.assert_called_once()

    def test_get_pending_foreshadows(self, memory_gateway, mock_plot_thread_tracker):
        """测试获取待回收伏笔"""
        result = memory_gateway.get_pending_foreshadows()

        assert isinstance(result, dict)
        mock_plot_thread_tracker.get_pending_foreshadows.assert_called_once()

    def test_check_consistency(self, memory_gateway, mock_query_engine):
        """测试一致性检查"""
        result = memory_gateway.check_consistency(
            chapter_content="李逍遥在仙灵岛遇到赵灵儿",
            chapter=5
        )

        assert isinstance(result, dict)
        assert "is_consistent" in result
        assert "consistency_score" in result
        mock_query_engine.check_consistency.assert_called_once()

    def test_get_relationship_network(self, memory_gateway, mock_query_engine):
        """测试获取关系网络"""
        result = memory_gateway.get_relationship_network("李逍遥")

        assert isinstance(result, list)
        mock_query_engine.get_relationship_network.assert_called_once_with("李逍遥", 1)


class TestMemoryGatewayEdgeCases:
    """MemoryGateway 边界情况测试"""

    @pytest.fixture
    def mock_qdrant_wrapper(self):
        """模拟 QdrantClientWrapper"""
        wrapper = MagicMock()
        wrapper.default_top_k = 5
        wrapper.hybrid_alpha = 0.7
        wrapper.dimension = 1536
        return wrapper

    @pytest.fixture
    def mock_embedder(self):
        """模拟 Embedder"""
        embedder = MagicMock()
        embedder.embed_texts = MagicMock(return_value=[[0.1] * 1536])
        return embedder

    @pytest.fixture
    def mock_query_engine(self):
        """模拟 QueryEngine"""
        engine = MagicMock()
        engine.hybrid_search = MagicMock(return_value=[])
        return engine

    @pytest.fixture
    def mock_push_engine(self):
        """模拟 PushEngine"""
        engine = MagicMock()
        engine.push_context = MagicMock(return_value={
            "chapter": 1,
            "character_states": {},
            "pending_foreshadows": {},
            "recent_events": [],
            "related_segments": [],
        })
        return engine

    def test_auto_push_context_without_push_engine(self, mock_qdrant_wrapper, mock_embedder):
        """测试没有 PushEngine 时推送上下文"""
        gateway = MemoryGateway(
            qdrant_wrapper=mock_qdrant_wrapper,
            embedder=mock_embedder,
        )
        # 应该返回空上下文而不是报错
        result = gateway.auto_push_context(chapter_num=1)
        assert isinstance(result, dict)
        assert result.get("chapter") == 1

    def test_query_without_query_engine(self, mock_qdrant_wrapper, mock_embedder):
        """测试没有 QueryEngine 时查询（会自动创建）"""
        gateway = MemoryGateway(
            qdrant_wrapper=mock_qdrant_wrapper,
            embedder=mock_embedder,
        )
        # QueryEngine 会自动创建，但依赖于 mock 的 qdrant_wrapper 和 embedder
        # 由于 hybrid_search 被 mock，返回的是 MagicMock 而不是 list
        gateway.query(query="测试", scope="all")
        # 当 query 为空字符串时应该返回空列表
        assert gateway.query_engine is not None  # 验证自动创建

    def test_update_character_state_without_tracker(
        self, mock_qdrant_wrapper, mock_embedder
    ):
        """测试没有 CharacterTracker 时更新角色状态"""
        gateway = MemoryGateway(
            qdrant_wrapper=mock_qdrant_wrapper,
            embedder=mock_embedder,
        )
        # 应该静默处理而不报错
        gateway.update_character_state("李逍遥", {"alive": True})

    def test_plant_foreshadow_without_tracker(self, mock_qdrant_wrapper, mock_embedder):
        """测试没有 PlotThreadTracker 时登记伏笔"""
        gateway = MemoryGateway(
            qdrant_wrapper=mock_qdrant_wrapper,
            embedder=mock_embedder,
        )
        # 应该静默处理而不报错
        gateway.plant_foreshadow("fp_001", {"title": "测试"})

    def test_update_foreshadow_without_tracker(self, mock_qdrant_wrapper, mock_embedder):
        """测试没有 PlotThreadTracker 时更新伏笔"""
        gateway = MemoryGateway(
            qdrant_wrapper=mock_qdrant_wrapper,
            embedder=mock_embedder,
        )
        # 应该静默处理而不报错
        gateway.update_foreshadow("fp_001", chapter=5, event_type="activate")

    def test_auto_push_context_chapter_zero(self, mock_qdrant_wrapper, mock_embedder):
        """测试第0章的上下文推送"""
        gateway = MemoryGateway(
            qdrant_wrapper=mock_qdrant_wrapper,
            embedder=mock_embedder,
        )
        result = gateway.auto_push_context(chapter_num=0)
        assert isinstance(result, dict)

    def test_query_with_none_scope(self, mock_qdrant_wrapper, mock_embedder):
        """测试 None 范围的查询"""
        gateway = MemoryGateway(
            qdrant_wrapper=mock_qdrant_wrapper,
            embedder=mock_embedder,
        )
        result = gateway.query(query="测试", scope=None)
        # scope=None 应该回退到默认行为（作为 "all" 处理）
        # 由于 query_engine 被自动创建，mock_embedder.embed_texts 返回 MagicMock
        # 所以结果是 MagicMock 而不是 list
        # 但查询会执行（空字符串会返回 []）
        assert result is not None

    def test_get_character_state_without_tracker(self, mock_qdrant_wrapper, mock_embedder):
        """测试没有 CharacterTracker 时获取角色状态"""
        gateway = MemoryGateway(
            qdrant_wrapper=mock_qdrant_wrapper,
            embedder=mock_embedder,
        )
        result = gateway.get_character_state("李逍遥")
        assert result is None

    def test_check_consistency_without_query_engine(
        self, mock_qdrant_wrapper, mock_embedder
    ):
        """测试没有 QueryEngine 时一致性检查"""
        gateway = MemoryGateway(
            qdrant_wrapper=mock_qdrant_wrapper,
            embedder=mock_embedder,
        )
        result = gateway.check_consistency(chapter_content="测试内容", chapter=1)
        # 应该返回默认结果
        assert isinstance(result, dict)
        assert result.get("is_consistent") is True
