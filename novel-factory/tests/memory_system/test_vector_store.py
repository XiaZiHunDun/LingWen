"""向量存储测试 (TDD 模式)

测试 Qdrant 客户端、批量嵌入和相似度搜索功能。
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from infra.memory_system.vector_store.qdrant_client import QdrantClientWrapper
from infra.memory_system.embeddings.batch_embed import BatchEmbedder, find_similar_chapters


class TestQdrantClientWrapper:
    """QdrantClientWrapper 测试套件"""

    @pytest.fixture
    def wrapper(self):
        """创建 QdrantClientWrapper 实例（带 mock）"""
        with patch("infra.memory_system.vector.qdrant_client.QdrantClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            with patch("infra.memory_system.vector.qdrant_client.load_yaml") as mock_load_yaml:
                mock_load_yaml.side_effect = [
                    {
                        "qdrant": {"host": "localhost", "port": 6333, "grpc_port": 6334},
                        "embedding": {"model": "text-embedding-3-small", "dimension": 1536},
                        "retrieval": {"default_top_k": 5, "hybrid_alpha": 0.7},
                    },
                    {
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
                wrapper._mock_client = mock_client
                yield wrapper

    def test_initialization(self, wrapper):
        """测试初始化 - 验证客户端连接参数"""
        assert wrapper.host == "localhost"
        assert wrapper.port == 6333
        assert wrapper.grpc_port == 6334
        assert wrapper.dimension == 1536
        assert wrapper._mock_client is not None

    def test_collections_defined(self, wrapper):
        """测试集合定义 - 验证三个集合都已定义"""
        expected_collections = {"chapters_seg", "entities", "relationships"}
        assert set(wrapper.collections.keys()) == expected_collections

    def test_search(self, wrapper):
        """测试向量搜索"""
        mock_qdrant_client = wrapper._mock_client
        collection_name = "chapters_seg"
        query_vector = [0.5] * 1536
        top_k = 3

        mock_results = [
            {"id": "ch_001", "score": 0.95, "payload": {"content": "测试内容1", "chapter_id": "ch_001"}},
            {"id": "ch_002", "score": 0.88, "payload": {"content": "测试内容2", "chapter_id": "ch_002"}},
        ]
        mock_qdrant_client.search.return_value = mock_results

        results = wrapper.search(collection_name, query_vector, top_k=top_k)

        mock_qdrant_client.search.assert_called_once()
        assert len(results) == 2
        assert results[0]["id"] == "ch_001"
        assert results[0]["score"] == 0.95

    def test_search_with_filter(self, wrapper):
        """测试带过滤器的搜索"""
        mock_qdrant_client = wrapper._mock_client
        collection_name = "chapters_seg"
        query_vector = [0.3] * 1536

        mock_results = [
            {"id": "ch_001", "score": 0.92, "payload": {"chapter_id": "ch_001"}},
        ]
        mock_qdrant_client.search.return_value = mock_results

        results = wrapper.search_with_filter(collection_name, query_vector, must={"chapter_id": "ch_001"})

        mock_qdrant_client.search.assert_called_once()


class TestBatchEmbedder:
    """BatchEmbedder 测试套件"""

    @pytest.fixture
    def mock_embedder(self):
        """创建 Mock Embedder"""
        embedder = Mock()
        return embedder

    @pytest.fixture
    def mock_qdrant(self):
        """创建 Mock QdrantClientWrapper"""
        qdrant = Mock()
        qdrant.upsert.return_value = None
        return qdrant

    def test_embed_chapters_basic(self, mock_embedder, mock_qdrant):
        """测试基本批量章节嵌入"""
        # Mock returns 3 vectors, matching 3 chapters
        mock_embedder.embed_texts.return_value = [
            [0.1] * 1536,
            [0.2] * 1536,
            [0.3] * 1536,
        ]

        batch_embedder = BatchEmbedder(
            qdrant_wrapper=mock_qdrant,
            embedder=mock_embedder,
            collection_name="chapters_seg",
        )

        chapters = [
            {"chapter_id": "ch_001", "content": "这是第一章的内容", "title": "第一章"},
            {"chapter_id": "ch_002", "content": "这是第二章的内容", "title": "第二章"},
            {"chapter_id": "ch_003", "content": "这是第三章的内容", "title": "第三章"},
        ]

        result = batch_embedder.embed_chapters(chapters)

        assert len(result) == 3
        assert "ch_001" in result
        assert "ch_002" in result
        assert "ch_003" in result
        mock_embedder.embed_texts.assert_called_once()
        mock_qdrant.upsert.assert_called_once()

    def test_embed_chapters_with_metadata(self, mock_embedder, mock_qdrant):
        """测试带元数据的批量嵌入"""
        mock_embedder.embed_texts.return_value = [
            [0.1] * 1536,
            [0.2] * 1536,
        ]

        batch_embedder = BatchEmbedder(
            qdrant_wrapper=mock_qdrant,
            embedder=mock_embedder,
            collection_name="chapters_seg",
        )

        chapters = [
            {"chapter_id": "ch_001", "content": "内容1", "chapter_num": 1, "author": "张三"},
            {"chapter_id": "ch_002", "content": "内容2", "chapter_num": 2, "author": "张三"},
        ]

        result = batch_embedder.embed_chapters(
            chapters,
            metadata_fields=["chapter_num", "author"]
        )

        assert len(result) == 2

        # 验证 upsert 调用
        call_args = mock_qdrant.upsert.call_args
        points = call_args[0][1]

        # 检查 payload 包含元数据
        for point in points:
            assert "chapter_num" in point["payload"]
            assert "author" in point["payload"]
            assert "content" in point["payload"]

    def test_embed_chapters_empty_list(self, mock_embedder, mock_qdrant):
        """测试空列表处理"""
        batch_embedder = BatchEmbedder(
            qdrant_wrapper=mock_qdrant,
            embedder=mock_embedder,
        )

        result = batch_embedder.embed_chapters([])
        assert result == []
        mock_embedder.embed_texts.assert_not_called()

    def test_embed_chapters_validation_missing_id(self, mock_embedder, mock_qdrant):
        """测试缺少 chapter_id 的验证"""
        batch_embedder = BatchEmbedder(
            qdrant_wrapper=mock_qdrant,
            embedder=mock_embedder,
        )

        chapters = [
            {"content": "内容1"},  # 缺少 chapter_id
        ]

        with pytest.raises(ValueError, match="missing required field"):
            batch_embedder.embed_chapters(chapters)

    def test_embed_chapters_validation_missing_content(self, mock_embedder, mock_qdrant):
        """测试缺少 content 的验证"""
        batch_embedder = BatchEmbedder(
            qdrant_wrapper=mock_qdrant,
            embedder=mock_embedder,
        )

        chapters = [
            {"chapter_id": "ch_001"},  # 缺少 content
        ]

        with pytest.raises(ValueError, match="missing required field"):
            batch_embedder.embed_chapters(chapters)

    def test_embed_chapters_validation_empty_content(self, mock_embedder, mock_qdrant):
        """测试空内容的验证"""
        batch_embedder = BatchEmbedder(
            qdrant_wrapper=mock_qdrant,
            embedder=mock_embedder,
        )

        chapters = [
            {"chapter_id": "ch_001", "content": ""},  # 空 content
        ]

        with pytest.raises(ValueError, match="empty content"):
            batch_embedder.embed_chapters(chapters)

    def test_embed_segments(self, mock_embedder, mock_qdrant):
        """测试段落嵌入"""
        mock_embedder.embed_texts.return_value = [
            [0.1] * 1536,
            [0.2] * 1536,
            [0.3] * 1536,
        ]

        batch_embedder = BatchEmbedder(
            qdrant_wrapper=mock_qdrant,
            embedder=mock_embedder,
        )

        segments = [
            {"segment_id": "seg_001", "text": "段落1内容", "chapter_id": "ch_001"},
            {"segment_id": "seg_002", "text": "段落2内容", "chapter_id": "ch_001"},
            {"segment_id": "seg_003", "text": "段落3内容", "chapter_id": "ch_002"},
        ]

        result = batch_embedder.embed_segments(segments)

        assert len(result) == 3
        assert "seg_001" in result
        mock_qdrant.upsert.assert_called_once()

    def test_batch_size_handling(self, mock_embedder, mock_qdrant):
        """测试批量大小处理"""
        # 每批返回不同的向量
        mock_embedder.embed_texts.side_effect = [
            [[0.1] * 1536, [0.2] * 1536],
            [[0.3] * 1536],
        ]

        batch_embedder = BatchEmbedder(
            qdrant_wrapper=mock_qdrant,
            embedder=mock_embedder,
            collection_name="chapters_seg",
        )

        chapters = [
            {"chapter_id": "ch_001", "content": "内容1"},
            {"chapter_id": "ch_002", "content": "内容2"},
            {"chapter_id": "ch_003", "content": "内容3"},
        ]

        result = batch_embedder.embed_chapters(chapters, batch_size=2)

        assert len(result) == 3
        # 验证被调用两次（3个章节，batch_size=2）
        assert mock_embedder.embed_texts.call_count == 2


class TestFindSimilarChapters:
    """find_similar_chapters 便捷函数测试"""

    @pytest.fixture
    def mock_embedder(self):
        """创建 Mock Embedder"""
        embedder = Mock()
        embedder.embed_texts.return_value = [[0.5] * 1536]
        return embedder

    @pytest.fixture
    def mock_qdrant(self):
        """创建 Mock QdrantClientWrapper"""
        qdrant = Mock()
        qdrant.search.return_value = [
            {"id": "ch_001", "score": 0.95, "payload": {"content": "相似内容1"}},
            {"id": "ch_002", "score": 0.88, "payload": {"content": "相似内容2"}},
        ]
        return qdrant

    def test_find_similar_chapters_basic(self, mock_embedder, mock_qdrant):
        """测试基本相似章节查找"""
        results = find_similar_chapters(
            qdrant_wrapper=mock_qdrant,
            embedder=mock_embedder,
            query_text="查找相似的内容",
            collection_name="chapters_seg",
            top_k=5,
        )

        assert len(results) == 2
        mock_embedder.embed_texts.assert_called_once_with(["查找相似的内容"])
        mock_qdrant.search.assert_called_once()

    def test_find_similar_chapters_with_filters(self, mock_embedder, mock_qdrant):
        """测试带过滤条件的相似章节查找"""
        results = find_similar_chapters(
            qdrant_wrapper=mock_qdrant,
            embedder=mock_embedder,
            query_text="战斗场景",
            filters={"chapter_num": 5},
        )

        assert len(results) == 2
        # 验证 filter 被传递
        call_args = mock_qdrant.search.call_args
        assert call_args[1]["query_filter"] is not None

    def test_find_similar_chapters_empty_query(self, mock_embedder, mock_qdrant):
        """测试空查询处理"""
        results = find_similar_chapters(
            qdrant_wrapper=mock_qdrant,
            embedder=mock_embedder,
            query_text="",
        )

        assert results == []
        mock_embedder.embed_texts.assert_not_called()

    def test_find_similar_chapters_embed_failed(self, mock_embedder, mock_qdrant):
        """测试嵌入失败处理"""
        mock_embedder.embed_texts.return_value = []

        results = find_similar_chapters(
            qdrant_wrapper=mock_qdrant,
            embedder=mock_embedder,
            query_text="测试内容",
        )

        assert results == []
        mock_qdrant.search.assert_not_called()


class TestBatchEmbedderEdgeCases:
    """BatchEmbedder 边界情况测试"""

    @pytest.fixture
    def mock_embedder(self):
        """创建 Mock Embedder"""
        embedder = Mock()
        return embedder

    @pytest.fixture
    def mock_qdrant(self):
        """创建 Mock QdrantClientWrapper"""
        qdrant = Mock()
        return qdrant

    def test_embed_chapters_single_chapter(self, mock_embedder, mock_qdrant):
        """测试单章节处理"""
        mock_embedder.embed_texts.return_value = [[0.1] * 1536]

        batch_embedder = BatchEmbedder(
            qdrant_wrapper=mock_qdrant,
            embedder=mock_embedder,
        )

        chapters = [{"chapter_id": "ch_001", "content": "唯一章节"}]
        result = batch_embedder.embed_chapters(chapters)

        assert len(result) == 1
        assert result[0] == "ch_001"

    def test_embed_chapters_with_specified_metadata(self, mock_embedder, mock_qdrant):
        """测试仅包含指定的元数据字段"""
        mock_embedder.embed_texts.return_value = [[0.1] * 1536]

        batch_embedder = BatchEmbedder(
            qdrant_wrapper=mock_qdrant,
            embedder=mock_embedder,
        )

        chapters = [{
            "chapter_id": "ch_001",
            "content": "内容",
            "extra_field": "额外数据",
            "title": "章节标题",  # 这会作为 metadata_fields 被包含
        }]

        batch_embedder.embed_chapters(chapters, metadata_fields=["title"])

        call_args = mock_qdrant.upsert.call_args
        points = call_args[0][1]
        assert points[0]["payload"]["title"] == "章节标题"
        assert "extra_field" not in points[0]["payload"]  # 不在 metadata_fields 中所以不包含

    def test_embed_segments_parent_field(self, mock_embedder, mock_qdrant):
        """测试段落嵌入时的父引用字段"""
        mock_embedder.embed_texts.return_value = [[0.1] * 1536]

        batch_embedder = BatchEmbedder(
            qdrant_wrapper=mock_qdrant,
            embedder=mock_embedder,
        )

        segments = [{
            "segment_id": "seg_001",
            "text": "段落内容",
            "chapter_id": "ch_001",
            "position": 5,
        }]

        batch_embedder.embed_segments(segments, parent_field="chapter_id")

        call_args = mock_qdrant.upsert.call_args
        points = call_args[0][1]
        assert points[0]["payload"]["chapter_id"] == "ch_001"
        assert points[0]["payload"]["position"] == 5
        # segment_id 不应在 payload 中（已被排除）
        assert "segment_id" not in points[0]["payload"]
        # text 应该在 payload 中（显式添加为主字段）
        assert "text" in points[0]["payload"]