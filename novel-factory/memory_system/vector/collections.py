"""集合管理器

管理 Qdrant 集合的创建、查询和配置。
从 collections_schema.yaml 加载集合配置。
"""
from typing import Optional

from memory_system.vector.qdrant_client import QdrantClientWrapper


class CollectionManager:
    """集合管理器

    负责 Qdrant 集合的管理操作，包括：
    - 从配置文件加载集合定义
    - 创建集合
    - 列出已存在的集合
    - 获取集合信息
    """

    def __init__(self):
        """初始化集合管理器

        创建 QdrantClientWrapper 实例并加载集合配置。
        """
        self._client = QdrantClientWrapper()
        self._collections = self._client.collections

    @property
    def collections(self) -> dict:
        """获取集合配置字典"""
        return self._collections

    def create_collections(self) -> None:
        """创建所有定义的集合

        仅创建尚不存在的集合。如果集合已存在，则跳过。

        Raises:
            RuntimeError: Qdrant 连接失败
        """
        for collection_name in self._collections.keys():
            if not self._client.collection_exists(collection_name):
                self._client.create_collection(collection_name)

    def list_collections(self) -> list[str]:
        """列出所有已存在的集合

        Returns:
            已存在集合的名称列表
        """
        existing = []
        for collection_name in self._collections.keys():
            if self._client.collection_exists(collection_name):
                existing.append(collection_name)
        return existing

    def get_collection_info(self, collection_name: str) -> dict:
        """获取集合的配置信息

        Args:
            collection_name: 集合名称

        Returns:
            集合配置信息（包含 description, vector_size, distance）

        Raises:
            ValueError: 集合不存在于配置中
        """
        if collection_name not in self._collections:
            raise ValueError(
                f"Collection '{collection_name}' not found. "
                f"Available collections: {list(self._collections.keys())}"
            )

        return self._collections[collection_name]

    def get_all_collection_names(self) -> list[str]:
        """获取所有已定义集合的名称

        Returns:
            所有集合名称的列表
        """
        return list(self._collections.keys())

    def collection_exists(self, collection_name: str) -> bool:
        """检查集合是否存在

        Args:
            collection_name: 集合名称

        Returns:
            是否存在
        """
        return self._client.collection_exists(collection_name)

    def close(self) -> None:
        """关闭客户端连接"""
        self._client.close()