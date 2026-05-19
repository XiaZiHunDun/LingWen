"""Qdrant 客户端封装

封装 Qdrant 向量数据库连接和操作接口。
支持 memory_system/config/memory_config.yaml 中的配置。
支持 memory_system/config/collections_schema.yaml 中定义的集合。
"""
from typing import Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, Filter, PointStruct, FieldCondition, MatchValue, PointIdsList

from memory_system.config import load_yaml


class QdrantClientWrapper:
    """Qdrant 客户端封装类

    提供向量存储和检索接口，支持以下集合：
    - chapters_seg: 章节内容片段向量
    - entities: 实体向量（角色/物品/地点）
    - relationships: 关系向量
    """

    COLLECTIONS_CONFIG_PATH = "config/collections_schema.yaml"
    MEMORY_CONFIG_PATH = "config/memory_config.yaml"

    # Distance 映射
    DISTANCE_MAP = {
        "Cosine": Distance.COSINE,
        "Euclidean": Distance.EUCLID,
        "Dot": Distance.DOT,
    }

    def __init__(self):
        """初始化 Qdrant 客户端

        从配置文件加载 Qdrant 连接参数和集合定义。
        """
        # 加载配置
        try:
            memory_config = load_yaml(self.MEMORY_CONFIG_PATH)
            collections_config = load_yaml(self.COLLECTIONS_CONFIG_PATH)
        except FileNotFoundError as e:
            raise RuntimeError(f"Failed to load configuration: {e}")

        # Qdrant 连接配置
        qdrant_config = memory_config["qdrant"]
        self.host = qdrant_config["host"]
        self.port = qdrant_config["port"]
        self.grpc_port = qdrant_config["grpc_port"]

        # Embedding 配置
        embedding_config = memory_config["embedding"]
        self.dimension = embedding_config["dimension"]

        # Retrieval 配置
        retrieval_config = memory_config["retrieval"]
        self.default_top_k = retrieval_config["default_top_k"]
        self.hybrid_alpha = retrieval_config["hybrid_alpha"]

        # 集合配置
        self.collections = collections_config["collections"]

        # 初始化 Qdrant 客户端
        self._client = QdrantClient(
            host=self.host,
            port=self.port,
            grpc_port=self.grpc_port,
        )

    @property
    def client(self) -> QdrantClient:
        """获取 Qdrant 客户端实例"""
        return self._client

    def get_collection_info(self, collection_name: str) -> dict:
        """获取集合信息

        Args:
            collection_name: 集合名称

        Returns:
            集合配置信息

        Raises:
            ValueError: 集合不存在
        """
        if collection_name not in self.collections:
            raise ValueError(f"Collection '{collection_name}' not found. Available: {list(self.collections.keys())}")

        return self.collections[collection_name]

    def _validate_collection(self, collection_name: str) -> None:
        """验证集合是否存在

        Args:
            collection_name: 集合名称

        Raises:
            ValueError: 集合不存在
        """
        if collection_name not in self.collections:
            raise ValueError(f"Collection '{collection_name}' not found. Available: {list(self.collections.keys())}")

    def upsert(self, collection_name: str, points: list[dict]) -> None:
        """Upsert 向量点到集合

        Args:
            collection_name: 集合名称
            points: 点列表，每个点包含 id, vector, payload

        Raises:
            ValueError: 集合不存在或向量维度不匹配
        """
        self._validate_collection(collection_name)

        # 验证向量维度
        for point in points:
            if len(point["vector"]) != self.dimension:
                raise ValueError(
                    f"Vector dimension mismatch: expected {self.dimension}, got {len(point['vector'])}"
                )

        # 转换 points 格式
        from qdrant_client.models import PointStruct

        qdrant_points = [
            PointStruct(
                id=point["id"],
                vector=point["vector"],
                payload=point.get("payload", {}),
            )
            for point in points
        ]

        self._client.upsert(collection_name=collection_name, points=qdrant_points)

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        top_k: Optional[int] = None,
        query_filter: Optional[Filter] = None,
    ) -> list[dict]:
        """搜索最相似的向量

        Args:
            collection_name: 集合名称
            query_vector: 查询向量
            top_k: 返回数量，默认使用 default_top_k
            query_filter: 可选的过滤器

        Returns:
            搜索结果列表

        Raises:
            ValueError: 集合不存在或向量维度不匹配
        """
        self._validate_collection(collection_name)

        if len(query_vector) != self.dimension:
            raise ValueError(
                f"Query vector dimension mismatch: expected {self.dimension}, got {len(query_vector)}"
            )

        if top_k is None:
            top_k = self.default_top_k

        search_params = {"limit": top_k}
        if query_filter is not None:
            search_params["query_filter"] = query_filter

        results = self._client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            **search_params,
        )

        # 转换结果
        return [
            {
                "id": hit.id if hasattr(hit, "id") else hit["id"],
                "score": hit.score if hasattr(hit, "score") else hit["score"],
                "payload": hit.payload if hasattr(hit, "payload") else hit.get("payload", {}),
            }
            for hit in results
        ]

    def search_with_filter(
        self,
        collection_name: str,
        query_vector: list[float],
        must: Optional[dict] = None,
        must_not: Optional[dict] = None,
        top_k: Optional[int] = None,
    ) -> list[dict]:
        """使用过滤器搜索向量

        Args:
            collection_name: 集合名称
            query_vector: 查询向量
            must: 必须满足的条件 (field: value)
            must_not: 必须不满足的条件 (field: value)
            top_k: 返回数量

        Returns:
            搜索结果列表
        """
        conditions = []

        if must:
            for field, value in must.items():
                conditions.append(FieldCondition(key=field, match=MatchValue(value=value)))

        if must_not:
            for field, value in must_not.items():
                conditions.append(FieldCondition(key=field, match=MatchValue(value=value)))

        query_filter = Filter(must=conditions) if conditions else None

        return self.search(
            collection_name=collection_name,
            query_vector=query_vector,
            top_k=top_k,
            query_filter=query_filter,
        )

    def delete(self, collection_name: str, point_id: str) -> None:
        """删除向量

        Args:
            collection_name: 集合名称
            point_id: 点 ID

        Raises:
            ValueError: 集合不存在
        """
        self._validate_collection(collection_name)

        self._client.delete(
            collection_name=collection_name,
            points_selector=PointIdsList(points=[point_id]),
        )

    def collection_exists(self, collection_name: str) -> bool:
        """检查集合是否存在

        Args:
            collection_name: 集合名称

        Returns:
            是否存在
        """
        return self._client.collection_exists(collection_name=collection_name)

    def create_collection(self, collection_name: str) -> None:
        """创建集合

        Args:
            collection_name: 集合名称

        Raises:
            ValueError: 集合类型未知
        """
        if collection_name not in self.collections:
            raise ValueError(f"Unknown collection type: {collection_name}. Available: {list(self.collections.keys())}")

        collection_info = self.collections[collection_name]

        self._client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=collection_info["vector_size"],
                distance=self.DISTANCE_MAP.get(collection_info["distance"], Distance.COSINE),
            ),
        )

    def close(self) -> None:
        """关闭客户端连接"""
        self._client.close()