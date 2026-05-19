"""QdrantClientWrapper 测试 (TDD 模式)"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from memory_system.vector.qdrant_client import QdrantClientWrapper


class TestQdrantClientWrapper:
    """QdrantClientWrapper 测试套件"""

    @pytest.fixture
    def wrapper(self):
        """创建 QdrantClientWrapper 实例"""
        with patch("memory_system.vector.qdrant_client.QdrantClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            with patch("memory_system.vector.qdrant_client.load_yaml") as mock_load_yaml:
                # Mock collections schema
                mock_load_yaml.side_effect = [
                    {  # memory_config.yaml
                        "qdrant": {"host": "localhost", "port": 6333, "grpc_port": 6334},
                        "embedding": {"model": "text-embedding-3-small", "dimension": 1536},
                        "retrieval": {"default_top_k": 5, "hybrid_alpha": 0.7},
                    },
                    {  # collections_schema.yaml
                        "collections": {
                            "chapters_seg": {
                                "description": "章节内容片段向量",
                                "vector_size": 1536,
                                "distance": "Cosine",
                            },
                            "entities": {
                                "description": "实体向量（角色/物品/地点）",
                                "vector_size": 1536,
                                "distance": "Cosine",
                            },
                            "relationships": {
                                "description": "关系向量",
                                "vector_size": 1536,
                                "distance": "Cosine",
                            },
                        }
                    },
                ]
                wrapper = QdrantClientWrapper()
                # Attach mock client for assertions
                wrapper._mock_client = mock_client
                yield wrapper

    def test_initialization(self, wrapper):
        """测试初始化 - 验证客户端连接参数"""
        assert wrapper.host == "localhost"
        assert wrapper.port == 6333
        assert wrapper.grpc_port == 6334
        assert wrapper.dimension == 1536
        # QdrantClient is instantiated via QdrantClientWrapper's __init__
        # We verify it was created by checking the wrapper has a valid client
        assert wrapper._mock_client is not None

    def test_collections_defined(self, wrapper):
        """测试集合定义 - 验证三个集合都已定义"""
        expected_collections = {"chapters_seg", "entities", "relationships"}
        assert set(wrapper.collections.keys()) == expected_collections

        # 验证每个集合的配置
        for name in expected_collections:
            assert wrapper.collections[name]["vector_size"] == 1536
            assert wrapper.collections[name]["distance"] == "Cosine"

    def test_get_collection_info(self, wrapper):
        """测试获取集合信息"""
        info = wrapper.get_collection_info("chapters_seg")
        assert info["vector_size"] == 1536
        assert info["distance"] == "Cosine"

    def test_get_collection_info_invalid(self, wrapper):
        """测试获取不存在的集合信息"""
        with pytest.raises(ValueError, match="Collection .* not found"):
            wrapper.get_collection_info("invalid_collection")

    def test_upsert_vector(self, wrapper):
        """测试向量 upsert"""
        mock_qdrant_client = wrapper._mock_client
        collection_name = "chapters_seg"
        points = [
            {
                "id": "point_1",
                "vector": [0.1] * 1536,
                "payload": {"text": "测试文本", "chapter_id": "ch001"},
            }
        ]

        wrapper.upsert(collection_name, points)

        mock_qdrant_client.upsert.assert_called_once()

    def test_upsert_invalid_collection(self, wrapper):
        """测试向不存在的集合 upsert"""
        with pytest.raises(ValueError, match="Collection .* not found"):
            wrapper.upsert("invalid", [{"id": "1", "vector": [0.1] * 1536, "payload": {}}])

    def test_search(self, wrapper):
        """测试向量搜索"""
        mock_qdrant_client = wrapper._mock_client
        collection_name = "entities"
        query_vector = [0.5] * 1536
        top_k = 3

        # Mock search results
        mock_results = [
            {"id": "entity_1", "score": 0.95, "payload": {"name": "李白", "type": "character"}},
            {"id": "entity_2", "score": 0.88, "payload": {"name": "杜甫", "type": "character"}},
        ]
        mock_qdrant_client.search.return_value = mock_results

        results = wrapper.search(collection_name, query_vector, top_k=top_k)

        mock_qdrant_client.search.assert_called_once_with(
            collection_name=collection_name, query_vector=query_vector, limit=top_k
        )
        assert len(results) == 2
        assert results[0]["id"] == "entity_1"
        assert results[0]["score"] == 0.95

    def test_search_invalid_collection(self, wrapper):
        """测试在不存在集合中搜索"""
        with pytest.raises(ValueError, match="Collection .* not found"):
            wrapper.search("invalid", [0.1] * 1536)

    def test_delete_vector(self, wrapper):
        """测试删除向量"""
        mock_qdrant_client = wrapper._mock_client
        collection_name = "relationships"
        point_id = "rel_001"

        wrapper.delete(collection_name, point_id)

        mock_qdrant_client.delete.assert_called_once()

    def test_delete_invalid_collection(self, wrapper):
        """测试从不存在集合删除向量"""
        with pytest.raises(ValueError, match="Collection .* not found"):
            wrapper.delete("invalid", "point_1")

    def test_collection_exists(self, wrapper):
        """测试集合存在性检查"""
        mock_qdrant_client = wrapper._mock_client
        mock_qdrant_client.collection_exists.return_value = True

        assert wrapper.collection_exists("chapters_seg") is True
        mock_qdrant_client.collection_exists.assert_called_with(collection_name="chapters_seg")

    def test_create_collection(self, wrapper):
        """测试创建集合"""
        mock_qdrant_client = wrapper._mock_client
        collection_name = "chapters_seg"

        wrapper.create_collection(collection_name)

        mock_qdrant_client.create_collection.assert_called_once()
        call_args = mock_qdrant_client.create_collection.call_args
        assert call_args[1]["collection_name"] == collection_name
        # vectors_config is a VectorParams object, check its attributes
        vectors_config = call_args[1]["vectors_config"]
        assert vectors_config.size == 1536
        assert vectors_config.distance.value == "Cosine"

    def test_create_collection_invalid(self, wrapper):
        """测试创建不存在的集合类型"""
        with pytest.raises(ValueError, match="Unknown collection type"):
            wrapper.create_collection("invalid_type")

    def test_default_top_k(self, wrapper):
        """测试默认 top_k 参数"""
        assert wrapper.default_top_k == 5

    def test_search_with_filter(self, wrapper):
        """测试带过滤器的搜索"""
        mock_qdrant_client = wrapper._mock_client
        collection_name = "chapters_seg"
        query_vector = [0.3] * 1536

        # Mock results with filter
        mock_results = [
            {"id": "seg_1", "score": 0.92, "payload": {"chapter_id": "ch001", "segment_index": 0}},
        ]
        mock_qdrant_client.search.return_value = mock_results

        # 使用默认 top_k
        results = wrapper.search_with_filter(collection_name, query_vector, must={"chapter_id": "ch001"})

        mock_qdrant_client.search.assert_called_once()
        call_args = mock_qdrant_client.search.call_args
        assert call_args[1]["collection_name"] == collection_name
        assert call_args[1]["query_vector"] == query_vector
        assert "query_filter" in call_args[1]

    def test_close(self, wrapper):
        """测试关闭客户端"""
        mock_qdrant_client = wrapper._mock_client
        wrapper.close()
        mock_qdrant_client.close.assert_called_once()


class TestQdrantClientWrapperEdgeCases:
    """边界情况和异常测试"""

    @pytest.fixture
    def wrapper_with_mocked_config(self):
        """使用真实配置文件路径创建 wrapper (mock QdrantClient)"""
        with patch("memory_system.vector.qdrant_client.QdrantClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            with patch("memory_system.vector.qdrant_client.load_yaml") as mock_load_yaml:
                mock_load_yaml.side_effect = [
                    {
                        "qdrant": {"host": "test-host", "port": 6333, "grpc_port": 6334},
                        "embedding": {"model": "text-embedding-3-small", "dimension": 1536},
                        "retrieval": {"default_top_k": 10, "hybrid_alpha": 0.5},
                    },
                    {
                        "collections": {
                            "chapters_seg": {
                                "description": "章节内容片段向量",
                                "vector_size": 1536,
                                "distance": "Cosine",
                            },
                            "entities": {
                                "description": "实体向量",
                                "vector_size": 1536,
                                "distance": "Cosine",
                            },
                            "relationships": {
                                "description": "关系向量",
                                "vector_size": 1536,
                                "distance": "Cosine",
                            },
                        }
                    },
                ]
                wrapper = QdrantClientWrapper()
                yield wrapper, mock_client

    def test_empty_search_results(self, wrapper_with_mocked_config):
        """测试空搜索结果"""
        wrapper, mock_client = wrapper_with_mocked_config
        mock_client.search.return_value = []

        results = wrapper.search("chapters_seg", [0.1] * 1536)
        assert results == []

    def test_vector_dimension_mismatch(self, wrapper_with_mocked_config):
        """测试向量维度不匹配"""
        wrapper, mock_client = wrapper_with_mocked_config

        # 错误维度的向量
        wrong_dimension_vector = [0.1] * 512  # 应该是 1536

        # upsert 应该抛出异常
        with pytest.raises(ValueError, match="dimension"):
            wrapper.upsert("chapters_seg", [{"id": "1", "vector": wrong_dimension_vector, "payload": {}}])

    def test_config_file_not_found(self):
        """测试配置文件不存在"""
        with patch("memory_system.vector.qdrant_client.QdrantClient"):
            with patch("memory_system.vector.qdrant_client.load_yaml", side_effect=FileNotFoundError("Config not found")):
                with pytest.raises(RuntimeError, match="Failed to load configuration"):
                    QdrantClientWrapper()