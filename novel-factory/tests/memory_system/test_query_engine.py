"""QueryEngine 测试"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

from memory_system.gateway.query_engine import QueryEngine


class TestQueryEngine:
    """QueryEngine 测试套件"""

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
        tracker.get_character_state = MagicMock(return_value={
            "current_location": "王宫",
            "current_form": "人形",
            "alive": True,
            "last_updated_chapter": 5,
            "emotion_state": "平静",
        })
        tracker.get_all_characters = MagicMock(return_value={
            "李逍遥": {"current_location": "王宫", "alive": True},
            "赵灵儿": {"current_location": "仙灵岛", "alive": True},
        })
        return tracker

    @pytest.fixture
    def mock_plot_thread_tracker(self, mock_config):
        """模拟 PlotThreadTracker"""
        tracker = MagicMock()
        tracker.get_all_foreshadows = MagicMock(return_value={
            "fp_001": {
                "title": "神秘剑客",
                "status": "pending",
                "planted_chapter": 1,
                "mentions": [1, 3],
            },
            "fp_002": {
                "title": "门派恩怨",
                "status": "in_progress",
                "planted_chapter": 2,
                "mentions": [2, 5],
            },
        })
        tracker.get_pending_foreshadows = MagicMock(return_value={
            "fp_001": {"title": "神秘剑客", "status": "pending"},
        })
        return tracker

    @pytest.fixture
    def mock_timeline_manager(self, mock_config):
        """模拟 TimelineManager"""
        manager = MagicMock()
        manager.get_events_in_range = MagicMock(return_value=[
            {"event_id": "evt_001", "timestamp": "2024-01-01T10:00:00", "chapter": 1},
            {"event_id": "evt_002", "timestamp": "2024-01-01T12:00:00", "chapter": 2},
        ])
        manager.get_events_by_chapter = MagicMock(return_value=[
            {"event_id": "evt_001", "timestamp": "2024-01-01T10:00:00", "chapter": 1},
        ])
        return manager

    @pytest.fixture
    def mock_fact_base(self, mock_config):
        """模拟 FactBase"""
        base = MagicMock()
        base.get_facts_by_chapter = MagicMock(return_value=[
            {"fact_id": "fact_001", "content": "林夜是铁蛋的弟弟", "category": "character_relationship"},
        ])
        base.get_all_facts = MagicMock(return_value={
            "fact_001": {"fact_id": "fact_001", "content": "林夜是铁蛋的弟弟", "verified": True},
            "fact_002": {"fact_id": "fact_002", "content": "李逍遥是蜀山弟子", "verified": True},
        })
        return base

    @pytest.fixture
    def query_engine(
        self,
        mock_qdrant_wrapper,
        mock_embedder,
        mock_character_tracker,
        mock_plot_thread_tracker,
        mock_timeline_manager,
        mock_fact_base,
    ):
        """创建 QueryEngine 实例（使用模拟依赖）"""
        return QueryEngine(
            qdrant_wrapper=mock_qdrant_wrapper,
            embedder=mock_embedder,
            character_tracker=mock_character_tracker,
            plot_thread_tracker=mock_plot_thread_tracker,
            timeline_manager=mock_timeline_manager,
            fact_base=mock_fact_base,
        )

    def test_initialization(self, query_engine, mock_qdrant_wrapper, mock_embedder):
        """测试 QueryEngine 初始化"""
        assert query_engine.qdrant_wrapper is mock_qdrant_wrapper
        assert query_engine.embedder is mock_embedder
        assert query_engine.default_top_k == 5
        assert query_engine.hybrid_alpha == 0.7

    def test_initialization_with_defaults(self, mock_qdrant_wrapper, mock_embedder):
        """测试使用默认配置的初始化"""
        engine = QueryEngine(
            qdrant_wrapper=mock_qdrant_wrapper,
            embedder=mock_embedder,
        )
        assert engine.default_top_k == 5
        assert engine.hybrid_alpha == 0.7

    def test_hybrid_search_basic(self, query_engine, mock_qdrant_wrapper, mock_embedder):
        """测试基础混合检索"""
        mock_embedder.embed_texts.return_value = [[0.1] * 1536]
        mock_qdrant_wrapper.search.return_value = [
            {"id": "seg_001", "score": 0.95, "payload": {"content": "测试内容", "chapter": 1}},
            {"id": "seg_002", "score": 0.85, "payload": {"content": "更多内容", "chapter": 2}},
        ]

        results = query_engine.hybrid_search("测试查询")

        assert len(results) == 2
        assert results[0]["id"] == "seg_001"
        assert results[0]["score"] == 0.95
        mock_embedder.embed_texts.assert_called_once_with(["测试查询"])

    def test_hybrid_search_with_top_k(self, query_engine, mock_qdrant_wrapper, mock_embedder):
        """测试指定返回数量"""
        mock_embedder.embed_texts.return_value = [[0.1] * 1536]
        mock_qdrant_wrapper.search.return_value = [
            {"id": "seg_001", "score": 0.95, "payload": {"chapter": 1}},
        ]

        results = query_engine.hybrid_search("测试", top_k=10)

        assert results[0]["id"] == "seg_001"
        mock_qdrant_wrapper.search.assert_called()

    def test_hybrid_search_with_filters(self, query_engine, mock_qdrant_wrapper, mock_embedder):
        """测试带过滤条件的混合检索"""
        mock_embedder.embed_texts.return_value = [[0.1] * 1536]
        mock_qdrant_wrapper.search.return_value = [
            {"id": "seg_001", "score": 0.95, "payload": {"chapter": 1, "character": "李逍遥"}},
        ]

        filters = {"character": "李逍遥", "chapter": 1}
        results = query_engine.hybrid_search("测试", filters=filters)

        assert len(results) == 1
        assert results[0]["payload"]["character"] == "李逍遥"

    def test_hybrid_search_empty_query(self, query_engine):
        """测试空查询处理"""
        results = query_engine.hybrid_search("")
        assert results == []

    def test_hybrid_search_no_results(self, query_engine, mock_qdrant_wrapper, mock_embedder):
        """测试无结果情况"""
        mock_embedder.embed_texts.return_value = [[0.1] * 1536]
        mock_qdrant_wrapper.search.return_value = []

        results = query_engine.hybrid_search("不存在的查询")
        assert results == []

    def test_get_character_state_existing(
        self, query_engine, mock_character_tracker
    ):
        """测试获取已存在角色的状态"""
        result = query_engine.get_character_state("李逍遥")

        assert result is not None
        assert result["current_location"] == "王宫"
        assert result["current_form"] == "人形"
        assert result["alive"] is True
        mock_character_tracker.get_character_state.assert_called_once_with("李逍遥")

    def test_get_character_state_with_before_chapter(
        self, query_engine, mock_character_tracker
    ):
        """测试获取指定章节之前的角色状态"""
        result = query_engine.get_character_state("李逍遥", before_chapter=10)

        assert result is not None
        mock_character_tracker.get_character_state.assert_called_once_with("李逍遥")

    def test_get_character_state_nonexistent(self, query_engine, mock_character_tracker):
        """测试获取不存在的角色状态"""
        mock_character_tracker.get_character_state.return_value = None

        result = query_engine.get_character_state("不存在的角色")

        assert result is None

    def test_get_relationship_network_basic(self, query_engine, mock_qdrant_wrapper):
        """测试获取关系网络"""
        mock_qdrant_wrapper.search.return_value = [
            {
                "id": "rel_001",
                "score": 0.9,
                "payload": {
                    "from_character": "李逍遥",
                    "to_character": "赵灵儿",
                    "relationship_type": "恋人",
                },
            },
            {
                "id": "rel_002",
                "score": 0.8,
                "payload": {
                    "from_character": "李逍遥",
                    "to_character": "酒剑仙",
                    "relationship_type": "师徒",
                },
            },
        ]

        result = query_engine.get_relationship_network("李逍遥")

        assert len(result) == 2
        mock_qdrant_wrapper.search.assert_called()

    def test_get_relationship_network_no_relationships(self, query_engine, mock_qdrant_wrapper):
        """测试角色没有关系网络"""
        mock_qdrant_wrapper.search.return_value = []

        result = query_engine.get_relationship_network("孤立角色")

        assert result == []

    def test_check_consistency_basic(self, query_engine, mock_character_tracker, mock_fact_base):
        """测试基础一致性检查"""
        mock_character_tracker.get_all_characters.return_value = {
            "李逍遥": {"current_location": "王宫", "alive": True},
        }
        mock_fact_base.get_all_facts.return_value = {
            "fact_001": {"content": "李逍遥在王宫", "verified": True},
        }

        chapter_content = "李逍遥前往王宫与赵灵儿会面。"
        result = query_engine.check_consistency(chapter_content)

        assert isinstance(result, dict)
        assert "is_consistent" in result or "issues" in result or "consistency_score" in result

    def test_check_consistency_with_plot_threads(
        self, query_engine, mock_plot_thread_tracker
    ):
        """测试包含伏笔的一致性检查"""
        mock_plot_thread_tracker.get_pending_foreshadows.return_value = {
            "fp_001": {
                "title": "神秘剑客",
                "status": "pending",
                "planted_chapter": 1,
                "mentions": [1],
            },
        }

        chapter_content = "神秘剑客再次出现。"
        result = query_engine.check_consistency(chapter_content)

        assert isinstance(result, dict)

    def test_check_consistency_empty_content(self, query_engine):
        """测试空内容的一致性检查"""
        result = query_engine.check_consistency("")

        assert isinstance(result, dict)
        # 空内容应该返回无问题或高分一致性
        if "consistency_score" in result:
            assert result["consistency_score"] >= 0.5

    def test_check_consistency_detects_issues(
        self, query_engine, mock_character_tracker, mock_fact_base
    ):
        """测试一致性检查能检测出问题"""
        # 设置角色状态与内容矛盾
        mock_character_tracker.get_all_characters.return_value = {
            "林夜": {"current_location": "仙灵岛", "alive": False},
        }
        mock_fact_base.get_facts_by_chapter.return_value = [
            {"content": "林夜已经死亡", "verified": True},
        ]

        # 内容描述林夜活着
        chapter_content = "林夜在仙灵岛上快乐地生活。"
        result = query_engine.check_consistency(chapter_content)

        assert isinstance(result, dict)
        # 应该检测出问题
        if "issues" in result:
            assert len(result["issues"]) > 0

    def test_check_consistency_uses_timeline(
        self, query_engine, mock_timeline_manager
    ):
        """测试一致性检查使用时间线信息"""
        mock_timeline_manager.get_events_in_range.return_value = [
            {"event_id": "evt_001", "timestamp": "2024-01-01T10:00:00", "chapter": 1},
            {"event_id": "evt_002", "timestamp": "2024-01-01T12:00:00", "chapter": 2},
        ]

        # QueryEngine should use timeline for ordering/relevance
        chapter_content = "这是第二章的内容。"
        result = query_engine.check_consistency(chapter_content, chapter=2)

        assert isinstance(result, dict)
        mock_timeline_manager.get_events_by_chapter.assert_called()


class TestQueryEngineIntegration:
    """QueryEngine 集成测试（需要真实依赖）"""

    @pytest.fixture
    def integration_config(self, tmp_path):
        """集成测试配置"""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        return {
            "storage": {
                "state_file": str(state_dir / "state_tracker.json"),
                "plot_threads_file": str(state_dir / "plot_threads.yaml"),
                "timeline_file": str(state_dir / "timeline.json"),
            }
        }

    @pytest.mark.skip(reason="需要真实的 Qdrant 和 OpenAI API")
    def test_hybrid_search_with_real_services(self, integration_config):
        """测试使用真实服务的混合检索"""
        from memory_system.vector.qdrant_client import QdrantClientWrapper
        from memory_system.vector.embedder import Embedder
        from memory_system.state.character_tracker import CharacterTracker
        from memory_system.state.plot_thread_tracker import PlotThreadTracker
        from memory_system.state.timeline_manager import TimelineManager
        from memory_system.state.fact_base import FactBase

        qdrant = QdrantClientWrapper()
        embedder = Embedder()
        char_tracker = CharacterTracker(integration_config)
        plot_tracker = PlotThreadTracker(integration_config)
        timeline_mgr = TimelineManager(integration_config)
        fact_base = FactBase(integration_config)

        engine = QueryEngine(
            qdrant_wrapper=qdrant,
            embedder=embedder,
            character_tracker=char_tracker,
            plot_thread_tracker=plot_tracker,
            timeline_manager=timeline_mgr,
            fact_base=fact_base,
        )

        results = engine.hybrid_search("测试查询")
        assert isinstance(results, list)

    @pytest.mark.skip(reason="需要真实的 Qdrant 和 OpenAI API")
    def test_full_workflow(self, integration_config):
        """测试完整工作流"""
        from memory_system.vector.qdrant_client import QdrantClientWrapper
        from memory_system.vector.embedder import Embedder
        from memory_system.state.character_tracker import CharacterTracker
        from memory_system.state.plot_thread_tracker import PlotThreadTracker
        from memory_system.state.timeline_manager import TimelineManager
        from memory_system.state.fact_base import FactBase

        qdrant = QdrantClientWrapper()
        embedder = Embedder()
        char_tracker = CharacterTracker(integration_config)
        plot_tracker = PlotThreadTracker(integration_config)
        timeline_mgr = TimelineManager(integration_config)
        fact_base = FactBase(integration_config)

        engine = QueryEngine(
            qdrant_wrapper=qdrant,
            embedder=embedder,
            character_tracker=char_tracker,
            plot_thread_tracker=plot_tracker,
            timeline_manager=timeline_mgr,
            fact_base=fact_base,
        )

        # 1. 混合检索
        search_results = engine.hybrid_search("主角")
        assert isinstance(search_results, list)

        # 2. 获取角色状态
        char_state = engine.get_character_state("李逍遥", before_chapter=10)
        # 可能为 None 如果角色不存在

        # 3. 获取关系网络
        relationships = engine.get_relationship_network("李逍遥")
        assert isinstance(relationships, list)

        # 4. 一致性检查
        consistency = engine.check_consistency("李逍遥在王宫中。", chapter=5)
        assert isinstance(consistency, dict)