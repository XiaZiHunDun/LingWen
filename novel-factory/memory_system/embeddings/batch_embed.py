"""批量嵌入模块

提供批量将章节内容向量化的功能，支持将向量存储到 Qdrant 集合。
"""
from typing import Any, Dict, List, Optional

from memory_system.vector.embedder import Embedder
from memory_system.vector.qdrant_client import QdrantClientWrapper


class BatchEmbedder:
    """批量嵌入处理器

    负责将章节内容批量向量化并存储到 Qdrant 集合。
    """

    def __init__(
        self,
        qdrant_wrapper: QdrantClientWrapper,
        embedder: Embedder,
        collection_name: str = "chapters_seg",
    ):
        """初始化批量嵌入处理器

        Args:
            qdrant_wrapper: QdrantClientWrapper 实例
            embedder: Embedder 实例
            collection_name: 目标集合名称，默认为 chapters_seg
        """
        self.qdrant_wrapper = qdrant_wrapper
        self.embedder = embedder
        self.collection_name = collection_name

    def embed_chapters(
        self,
        chapters: List[Dict[str, Any]],
        batch_size: int = 32,
        text_field: str = "content",
        id_field: str = "chapter_id",
        metadata_fields: Optional[List[str]] = None,
    ) -> List[str]:
        """批量嵌入章节内容

        Args:
            chapters: 章节列表，每个章节包含 id, content 和可选的 metadata
            batch_size: 每批处理的章节数量，默认 32
            text_field: 章节内容字段名，默认 "content"
            id_field: 章节 ID 字段名，默认 "chapter_id"
            metadata_fields: 需要保留的额外字段列表（如 ["title", "chapter_num"]）

        Returns:
            成功嵌入的章节 ID 列表

        Raises:
            ValueError: 章节格式不正确或缺少必要字段
            Exception: 向量化或存储失败
        """
        if not chapters:
            return []

        # 验证章节格式
        self._validate_chapters(chapters, text_field, id_field)

        embedded_ids = []
        metadata_fields = metadata_fields or []

        # 分批处理
        for i in range(0, len(chapters), batch_size):
            batch = chapters[i:i + batch_size]
            embedded_ids.extend(self._process_batch(batch, text_field, id_field, metadata_fields))

        return embedded_ids

    def _validate_chapters(
        self,
        chapters: List[Dict[str, Any]],
        text_field: str,
        id_field: str,
    ) -> None:
        """验证章节格式

        Args:
            chapters: 章节列表
            text_field: 文本字段名
            id_field: ID 字段名

        Raises:
            ValueError: 验证失败
        """
        for idx, chapter in enumerate(chapters):
            if id_field not in chapter:
                raise ValueError(f"Chapter at index {idx} missing required field: {id_field}")
            if text_field not in chapter:
                raise ValueError(f"Chapter at index {idx} missing required field: {text_field}")
            if not chapter.get(text_field) or not str(chapter.get(text_field, "")).strip():
                raise ValueError(f"Chapter at index {idx} has empty content field: {text_field}")

    def _process_batch(
        self,
        batch: List[Dict[str, Any]],
        text_field: str,
        id_field: str,
        metadata_fields: List[str],
    ) -> List[str]:
        """处理单批章节

        Args:
            batch: 章节批次
            text_field: 文本字段名
            id_field: ID 字段名
            metadata_fields: 元数据字段列表

        Returns:
            成功嵌入的章节 ID 列表
        """
        # 提取文本
        texts = [chapter[text_field] for chapter in batch]

        # 向量化
        vectors = self.embedder.embed_texts(texts)

        if not vectors or len(vectors) != len(batch):
            raise Exception(f"Embedding failed: expected {len(batch)} vectors, got {len(vectors) if vectors else 0}")

        # 构建向量点
        points = []
        ids = []

        for chapter, vector in zip(batch, vectors):
            point_id = str(chapter[id_field])
            ids.append(point_id)

            # 构建 payload
            payload = {text_field: chapter[text_field]}
            for field in metadata_fields:
                if field in chapter:
                    payload[field] = chapter[field]

            # 添加额外元数据
            if id_field != "chapter_id":
                payload["chapter_id"] = chapter[id_field]

            points.append({
                "id": point_id,
                "vector": vector,
                "payload": payload,
            })

        # 存储到 Qdrant
        self.qdrant_wrapper.upsert(self.collection_name, points)

        return ids

    def embed_segments(
        self,
        segments: List[Dict[str, Any]],
        batch_size: int = 32,
        text_field: str = "text",
        id_field: str = "segment_id",
        parent_field: Optional[str] = None,
    ) -> List[str]:
        """批量嵌入段落（比章节更小的单元）

        Args:
            segments: 段落列表，每个段落包含 id, text 和可选的 parent 引用
            batch_size: 每批处理的段落数量，默认 32
            text_field: 段落文本字段名，默认 "text"
            id_field: 段落 ID 字段名，默认 "segment_id"
            parent_field: 父引用字段名（如 "chapter_id"），默认 None

        Returns:
            成功嵌入的段落 ID 列表
        """
        if not segments:
            return []

        # 验证段落格式
        for idx, segment in enumerate(segments):
            if id_field not in segment:
                raise ValueError(f"Segment at index {idx} missing required field: {id_field}")
            if text_field not in segment:
                raise ValueError(f"Segment at index {idx} missing required field: {text_field}")

        embedded_ids = []

        # 分批处理
        for i in range(0, len(segments), batch_size):
            batch = segments[i:i + batch_size]

            # 提取文本
            texts = [segment[text_field] for segment in batch]

            # 向量化
            vectors = self.embedder.embed_texts(texts)

            if not vectors or len(vectors) != len(batch):
                continue

            # 构建向量点
            points = []
            for segment, vector in zip(batch, vectors):
                point_id = str(segment[id_field])
                embedded_ids.append(point_id)

                # 构建 payload
                payload = {text_field: segment[text_field]}

                # 添加父引用
                if parent_field and parent_field in segment:
                    payload[parent_field] = segment[parent_field]

                # 添加其他字段
                for key, value in segment.items():
                    if key not in (id_field, text_field):
                        payload[key] = value

                points.append({
                    "id": point_id,
                    "vector": vector,
                    "payload": payload,
                })

            # 存储到 Qdrant
            if points:
                self.qdrant_wrapper.upsert(self.collection_name, points)

        return embedded_ids


def find_similar_chapters(
    qdrant_wrapper: QdrantClientWrapper,
    embedder: Embedder,
    query_text: str,
    collection_name: str = "chapters_seg",
    top_k: int = 5,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """查找与给定文本最相似的章节（便捷函数）

    Args:
        qdrant_wrapper: QdrantClientWrapper 实例
        embedder: Embedder 实例
        query_text: 查询文本
        collection_name: 集合名称，默认 "chapters_seg"
        top_k: 返回数量，默认 5
        filters: 可选的过滤条件

    Returns:
        相似章节列表，每项包含 id, score, payload
    """
    if not query_text or not query_text.strip():
        return []

    # 向量化查询文本
    query_vectors = embedder.embed_texts([query_text])
    if not query_vectors:
        return []

    query_vector = query_vectors[0]

    # 构建过滤器
    query_filter = None
    if filters:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        conditions = [
            FieldCondition(key=field, match=MatchValue(value=value))
            for field, value in filters.items()
        ]
        query_filter = Filter(must=conditions) if conditions else None

    # 搜索
    return qdrant_wrapper.search(
        collection_name=collection_name,
        query_vector=query_vector,
        top_k=top_k,
        query_filter=query_filter,
    )