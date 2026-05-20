"""CollectionManager 测试 (TDD 模式)"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from infra.memory_system.vector.collections import CollectionManager


class TestCollectionManager:
    """CollectionManager 测试套件"""

    @pytest.fixture
    def collection_manager(self):
        """创建 CollectionManager 实例（mock QdrantClientWrapper）"""
        with patch("infra.memory_system.vector.collections.QdrantClientWrapper") as mock_wrapper_class:
            mock_instance = Mock()
            mock_wrapper_class.return_value = mock_instance

            # 设置 mock 配置
            mock_instance.collections = {
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

            manager = CollectionManager()
            manager._client = mock_instance
            yield manager, mock_instance

    def test_initialization(self, collection_manager):
        """测试初始化 - 验证 QdrantClientWrapper 已初始化"""
        manager, mock_client = collection_manager
        assert manager._client is mock_client

    def test_collections_config_loaded(self, collection_manager):
        """测试集合配置已加载"""
        manager, mock_client = collection_manager
        expected_collections = {"chapters_seg", "entities", "relationships"}
        assert set(manager.collections.keys()) == expected_collections

    def test_create_collections(self, collection_manager):
        """测试创建所有集合"""
        manager, mock_client = collection_manager

        # Mock collection_exists 返回 False（集合不存在，需要创建）
        mock_client.collection_exists.return_value = False

        manager.create_collections()

        # 验证每个集合都被创建
        assert mock_client.create_collection.call_count == 3
        mock_client.create_collection.assert_any_call("chapters_seg")
        mock_client.create_collection.assert_any_call("entities")
        mock_client.create_collection.assert_any_call("relationships")

    def test_create_collections_already_exist(self, collection_manager):
        """测试创建集合时集合已存在的情况"""
        manager, mock_client = collection_manager

        # Mock collection_exists 返回 True（集合已存在）
        mock_client.collection_exists.return_value = True

        manager.create_collections()

        # create_collection 不应被调用
        mock_client.create_collection.assert_not_called()

    def test_list_collections(self, collection_manager):
        """测试列出所有集合"""
        manager, mock_client = collection_manager

        mock_client.collection_exists.side_effect = [True, False, True]

        result = manager.list_collections()

        assert result == ["chapters_seg", "relationships"]

    def test_list_collections_all_exist(self, collection_manager):
        """测试列出所有已存在的集合"""
        manager, mock_client = collection_manager

        mock_client.collection_exists.return_value = True

        result = manager.list_collections()

        assert len(result) == 3
        assert set(result) == {"chapters_seg", "entities", "relationships"}

    def test_list_collections_none_exist(self, collection_manager):
        """测试列出集合但都不存在"""
        manager, mock_client = collection_manager

        mock_client.collection_exists.return_value = False

        result = manager.list_collections()

        assert result == []

    def test_get_collection_info(self, collection_manager):
        """测试获取集合信息"""
        manager, mock_client = collection_manager

        info = manager.get_collection_info("chapters_seg")

        assert info["vector_size"] == 1536
        assert info["distance"] == "Cosine"
        assert info["description"] == "章节内容片段向量"

    def test_get_collection_info_invalid(self, collection_manager):
        """测试获取不存在的集合信息"""
        manager, mock_client = collection_manager

        with pytest.raises(ValueError, match="Collection .* not found"):
            manager.get_collection_info("invalid_collection")

    def test_get_all_collection_names(self, collection_manager):
        """测试获取所有集合名称"""
        manager, mock_client = collection_manager

        names = manager.get_all_collection_names()

        assert names == ["chapters_seg", "entities", "relationships"]


class TestCollectionManagerEdgeCases:
    """边界情况和异常测试"""

    @pytest.fixture
    def manager_with_empty_config(self):
        """测试空配置情况"""
        with patch("infra.memory_system.vector.collections.QdrantClientWrapper") as mock_wrapper_class:
            mock_instance = Mock()
            mock_wrapper_class.return_value = mock_instance
            mock_instance.collections = {}

            manager = CollectionManager()
            manager._client = mock_instance
            yield manager, mock_instance

    def test_create_collections_empty_config(self, manager_with_empty_config):
        """测试空配置时创建集合"""
        manager, mock_client = manager_with_empty_config

        manager.create_collections()

        mock_client.create_collection.assert_not_called()
        mock_client.collection_exists.assert_not_called()

    def test_list_collections_empty_config(self, manager_with_empty_config):
        """测试空配置下列出集合"""
        manager, mock_client = manager_with_empty_config

        result = manager.list_collections()

        assert result == []

    def test_get_collection_info_empty_config(self, manager_with_empty_config):
        """测试空配置时获取集合信息"""
        manager, mock_client = manager_with_empty_config

        with pytest.raises(ValueError, match="Collection .* not found"):
            manager.get_collection_info("any_collection")